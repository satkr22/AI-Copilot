from __future__ import annotations

import hashlib
from dataclasses import dataclass
from uuid import NAMESPACE_URL, uuid5

from tree_sitter import Node

from app.services.indexing.extraction.query_extractor import RawExtractionResult
from app.services.indexing.intelligence.models import (
    ChunkOrigin,
    ChunkType,
    CodeChunkDTO,
    SymbolDTO,
)


@dataclass(slots=True)
class _Range:
    start: int
    end: int
    node: Node | None = None
    symbol: SymbolDTO | None = None


class CastChunker:
    """Build query-symbol and cAST gap chunks from one parsed tree."""

    def __init__(self, max_chunk_size: int = 12000) -> None:
        self.max_chunk_size = max_chunk_size

    def chunk(self, result: RawExtractionResult) -> list[CodeChunkDTO]:
        source = result.source_bytes
        symbols = sorted(result.symbols, key=lambda item: (item.start_byte, -(item.end_byte - item.start_byte)))
        items: list[_Range] = [_Range(symbol.start_byte, symbol.end_byte, result.symbol_nodes.get(symbol.symbol_id), symbol) for symbol in symbols]
        items.extend(self._gap_ranges(result, symbols))
        items.sort(key=lambda item: (item.start, item.end))

        chunks: list[CodeChunkDTO] = []
        for item in items:
            if item.symbol is None:
                chunks.extend(self._gap_chunks(item, result))
            elif item.end - item.start <= self.max_chunk_size:
                chunks.append(self._make_chunk(result, item.start, item.end, item.symbol, ChunkOrigin.QUERY_SYMBOL))
            else:
                chunks.extend(self._split_symbol(item, result))
        return self._merge_adjacent(chunks, result)

    def _gap_ranges(self, result: RawExtractionResult, symbols: list[SymbolDTO]) -> list[_Range]:
        source_length = len(result.source_bytes)
        # Nested methods are claimed by their containing class for gap finding.
        outer = [symbol for symbol in symbols if not any(other.start_byte <= symbol.start_byte and other.end_byte >= symbol.end_byte and other.symbol_id != symbol.symbol_id for other in symbols)]
        claimed = sorted((symbol.start_byte, symbol.end_byte) for symbol in outer)
        gaps: list[_Range] = []
        cursor = 0
        for start, end in claimed:
            if cursor < start:
                gaps.extend(self._split_gap_nodes(result.tree.root_node, cursor, start, result.source_bytes))
            cursor = max(cursor, end)
        if cursor < source_length:
            gaps.extend(self._split_gap_nodes(result.tree.root_node, cursor, source_length, result.source_bytes))
        return gaps

    def _split_gap_nodes(self, root: Node, start: int, end: int, source: bytes) -> list[_Range]:
        nodes = [node for node in root.children if node.end_byte > start and node.start_byte < end]
        if not nodes:
            return [_Range(start, end)] if source[start:end].strip() else []
        ranges: list[_Range] = []
        current_start: int | None = None
        current_end = 0
        for node in nodes:
            node_start = max(start, node.start_byte)
            node_end = min(end, node.end_byte)
            if current_start is None:
                current_start, current_end = node_start, node_end
            elif node_end - current_start <= self.max_chunk_size:
                current_end = node_end
            else:
                ranges.append(_Range(current_start, current_end, node))
                current_start, current_end = node_start, node_end
        if current_start is not None:
            ranges.append(_Range(current_start, current_end, nodes[-1]))
        return [item for item in ranges if source[item.start:item.end].strip()]

    def _gap_chunks(self, item: _Range, result: RawExtractionResult) -> list[CodeChunkDTO]:
        return [self._make_chunk(result, item.start, item.end, None, ChunkOrigin.CAST_GAP)]

    def _split_symbol(self, item: _Range, result: RawExtractionResult) -> list[CodeChunkDTO]:
        node = item.node
        if node is None or not node.children:
            return [self._make_chunk(result, item.start, item.end, item.symbol, ChunkOrigin.QUERY_SYMBOL_SPLIT, True, 0, 1)]
        pieces = self._split_gap_nodes(node, item.start, item.end, result.source_bytes)
        if len(pieces) == 1 and pieces[0].start == item.start and pieces[0].end == item.end:
            return [self._make_chunk(result, item.start, item.end, item.symbol, ChunkOrigin.QUERY_SYMBOL_SPLIT, True, 0, 1)]
        total = len(pieces)
        return [self._make_chunk(result, piece.start, piece.end, item.symbol, ChunkOrigin.QUERY_SYMBOL_SPLIT, True, index, total) for index, piece in enumerate(pieces)]

    def _merge_adjacent(self, chunks: list[CodeChunkDTO], result: RawExtractionResult) -> list[CodeChunkDTO]:
        chunks.sort(key=lambda item: (item.start_byte, item.end_byte))
        merged: list[CodeChunkDTO] = []
        for chunk in chunks:
            if merged and merged[-1].end_byte <= chunk.start_byte and len(merged[-1].content) + len(chunk.content) <= self.max_chunk_size and not merged[-1].is_partial and not chunk.is_partial:
                previous = merged.pop()
                start, end = previous.start_byte, chunk.end_byte
                symbol_ids = list(dict.fromkeys(previous.symbol_ids + chunk.symbol_ids))
                names = list(dict.fromkeys(previous.symbol_names + chunk.symbol_names))
                merged.append(self._make_chunk(result, start, end, None, ChunkOrigin.MERGED, symbol_ids=symbol_ids, symbol_names=names))
            else:
                merged.append(chunk)
        return merged

    def _make_chunk(
        self,
        result: RawExtractionResult,
        start: int,
        end: int,
        symbol: SymbolDTO | None,
        origin: ChunkOrigin,
        is_partial: bool = False,
        part_index: int | None = None,
        part_total: int | None = None,
        symbol_ids: list[str] | None = None,
        symbol_names: list[str] | None = None,
    ) -> CodeChunkDTO:
        content = result.source_bytes[start:end].decode("utf-8", errors="replace")
        symbols = [symbol] if symbol else []
        ids = symbol_ids if symbol_ids is not None else [item.symbol_id for item in symbols]
        names = symbol_names if symbol_names is not None else [item.name for item in symbols]
        scopes = self._scope_chain(symbol, result)
        chunk_type = ChunkType.MERGED if origin is ChunkOrigin.MERGED else (ChunkType.GAP if symbol is None else self._chunk_type(symbol))
        header = self._header(result, scopes, symbol)
        enriched = f"{header}\n\n{content}" if header else content
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        chunk_id = str(uuid5(NAMESPACE_URL, f"{result.file_path}:chunk:{start}:{end}:{content_hash}"))
        return CodeChunkDTO(chunk_id, chunk_type, origin, result.file_path, result.language, ids, names, scopes, start, end, self._line(result.source_bytes, start), self._line(result.source_bytes, max(start, end - 1)), content, enriched, None, is_partial, part_index, part_total, content_hash, token_count=max(1, len(enriched.split())))

    def _header(self, result: RawExtractionResult, scopes: list[str], symbol: SymbolDTO | None) -> str:
        lines = [f"# File: {result.file_path}", f"# Language: {result.language}"]
        if scopes:
            lines.append(f"# Scope: {'.'.join(scopes)}")
        if symbol and symbol.signature:
            lines.append(f"# Signature: {symbol.signature}")
        imports = [item.raw_statement.strip() for item in result.imports if item.raw_statement]
        if imports:
            lines.append(f"# Imports: {'; '.join(imports[:12])}")
        return "\n".join(lines)

    @staticmethod
    def _chunk_type(symbol: SymbolDTO) -> ChunkType:
        return ChunkType(symbol.kind.value) if symbol.kind.value in {item.value for item in ChunkType} else ChunkType.FUNCTION

    @staticmethod
    def _scope_chain(symbol: SymbolDTO | None, result: RawExtractionResult) -> list[str]:
        if symbol is None:
            return []
        by_id = {item.symbol_id: item for item in result.symbols}
        chain: list[str] = []
        current = symbol
        while current:
            chain.append(current.name)
            current = by_id.get(current.parent_symbol_id) if current.parent_symbol_id else None
        return list(reversed(chain))

    @staticmethod
    def _line(source: bytes, byte_offset: int) -> int:
        return source[:byte_offset].count(b"\n") + 1
