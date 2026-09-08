from __future__ import annotations

import bisect
import hashlib
from dataclasses import dataclass, replace
from uuid import NAMESPACE_URL, uuid5

from tree_sitter import Node

from app.services.indexing.chunking.tokenizer import CodeTokenCounter
from app.services.indexing.extraction.query_extractor import RawExtractionResult
from app.services.indexing.dto_models.models import (
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

    def __init__(
        self, max_chunk_tokens: int = 800, tokenizer: CodeTokenCounter | None = None
    ) -> None:
        if max_chunk_tokens < 1:
            raise ValueError("max_chunk_tokens must be positive")
        self.max_chunk_tokens = max_chunk_tokens
        self.tokenizer = tokenizer or CodeTokenCounter()
        self._symbol_by_id: dict[str, SymbolDTO] = {}
        self._scope_cache: dict[str, list[str]] = {}
        self._enriched_cache: dict[tuple, tuple[str, int]] = {}
        self._import_context_cache = ""
        # Byte offsets of every newline in the current file, used by _line
        # for O(log n) lookups instead of rescanning source_bytes from the
        # start on every call.
        self._newline_offsets: list[int] = []

    def chunk(self, result: RawExtractionResult) -> list[CodeChunkDTO]:
        source = result.source_bytes
        self._symbol_by_id = {item.symbol_id: item for item in result.symbols}
        self._scope_cache = {}
        self._enriched_cache = {}
        self._import_context_cache = self._import_context(result)
        self._newline_offsets = self._compute_newline_offsets(source)
        symbols = sorted(
            result.symbols,
            key=lambda item: (item.start_byte, -(item.end_byte - item.start_byte)),
        )
        items: list[_Range] = [
            _Range(
                symbol.start_byte,
                symbol.end_byte,
                result.symbol_nodes.get(symbol.symbol_id),
                symbol,
            )
            for symbol in symbols
        ]
        items.extend(self._gap_ranges(result, symbols))
        items.sort(key=lambda item: (item.start, item.end))

        chunks: list[CodeChunkDTO] = []
        for item in items:
            if item.symbol is None:
                chunks.extend(self._gap_chunks(item, result))
            elif self._fits(result, item.start, item.end, item.symbol, ChunkOrigin.QUERY_SYMBOL):
                chunks.append(
                    self._make_chunk(
                        result,
                        item.start,
                        item.end,
                        item.symbol,
                        ChunkOrigin.QUERY_SYMBOL,
                    )
                )
            else:
                chunks.extend(self._split_symbol(item, result))
        return self._deduplicate(self._merge_adjacent(chunks, result))
        # return self._deduplicate(chunks)

    def _gap_ranges(
        self, result: RawExtractionResult, symbols: list[SymbolDTO]
    ) -> list[_Range]:
        source_length = len(result.source_bytes)
        # Nested methods are claimed by their containing class for gap finding.
        # `symbols` is already sorted by (start_byte, -length), so ranges
        # nest properly (no partial overlaps) and a single pass with a stack
        # of still-open ranges finds the outer (unenclosed) symbols in O(n)
        # instead of the previous O(n^2) "is this contained by any other
        # symbol" scan.
        outer: list[SymbolDTO] = []
        stack: list[SymbolDTO] = []
        for symbol in symbols:
            while stack and stack[-1].end_byte <= symbol.start_byte:
                stack.pop()
            if not stack:
                outer.append(symbol)
            stack.append(symbol)
        claimed = sorted((symbol.start_byte, symbol.end_byte) for symbol in outer)
        gaps: list[_Range] = []
        cursor = 0
        for start, end in claimed:
            if cursor < start:
                gaps.extend(
                    self._split_gap_nodes(
                        result.tree.root_node, cursor, start, result
                    )
                )
            cursor = max(cursor, end)
        if cursor < source_length:
            gaps.extend(
                self._split_gap_nodes(
                    result.tree.root_node, cursor, source_length, result
                )
            )
        return gaps

    def _split_gap_nodes(
        self,
        root: Node,
        start: int,
        end: int,
        result: RawExtractionResult,
        symbol: SymbolDTO | None = None,
        origin: ChunkOrigin = ChunkOrigin.CAST_GAP,
    ) -> list[_Range]:
        source = result.source_bytes
        nodes = [
            node
            for node in root.children
            if node.end_byte > start and node.start_byte < end
        ]
        if not nodes:
            if not source[start:end].strip():
                return []
            return self._hard_split_ranges(result, start, end, symbol, origin)
        ranges: list[_Range] = []
        current_start: int | None = None
        current_end = 0
        for node in nodes:
            node_start = max(start, node.start_byte)
            node_end = min(end, node.end_byte)
            if not self._fits(result, node_start, node_end, symbol, origin):
                if current_start is not None:
                    ranges.append(_Range(current_start, current_end))
                    current_start = None
                if node.children:
                    ranges.extend(
                        self._split_gap_nodes(
                            node, node_start, node_end, result, symbol, origin
                        )
                    )
                else:
                    ranges.extend(
                        self._hard_split_ranges(result, node_start, node_end, symbol, origin)
                    )
            elif current_start is None:
                current_start, current_end = node_start, node_end
            elif self._fits(result, current_start, node_end, symbol, origin):
                current_end = node_end
            else:
                ranges.append(_Range(current_start, current_end))
                current_start, current_end = node_start, node_end
        if current_start is not None:
            ranges.append(_Range(current_start, current_end))
        return [item for item in ranges if source[item.start : item.end].strip()]

    def _gap_chunks(
        self, item: _Range, result: RawExtractionResult
    ) -> list[CodeChunkDTO]:
        return [
            self._make_chunk(result, item.start, item.end, None, ChunkOrigin.CAST_GAP)
        ]

    def _split_symbol(
        self, item: _Range, result: RawExtractionResult
    ) -> list[CodeChunkDTO]:
        node = item.node
        if node is None or not node.children:
            pieces = self._hard_split_ranges(
                result,
                item.start,
                item.end,
                item.symbol,
                ChunkOrigin.QUERY_SYMBOL_SPLIT,
            )
        else:
            pieces = self._split_gap_nodes(
                node,
                item.start,
                item.end,
                result,
                item.symbol,
                ChunkOrigin.QUERY_SYMBOL_SPLIT,
            )
        if (
            len(pieces) == 1
            and pieces[0].start == item.start
            and pieces[0].end == item.end
        ):
            return [
                self._make_chunk(
                    result,
                    item.start,
                    item.end,
                    item.symbol,
                    ChunkOrigin.QUERY_SYMBOL_SPLIT,
                    True,
                    0,
                    1,
                )
            ]
        total = len(pieces)
        return [
            self._make_chunk(
                result,
                piece.start,
                piece.end,
                item.symbol,
                ChunkOrigin.QUERY_SYMBOL_SPLIT,
                True,
                index,
                total,
            )
            for index, piece in enumerate(pieces)
        ]

    def _merge_adjacent(
        self, chunks: list[CodeChunkDTO], result: RawExtractionResult
    ) -> list[CodeChunkDTO]:
        chunks.sort(key=lambda item: (item.start_byte, item.end_byte))
        merged: list[CodeChunkDTO] = []
        for chunk in chunks:
            if (
                merged
                and merged[-1].end_byte <= chunk.start_byte
                and self._fits(
                    result,
                    merged[-1].start_byte,
                    chunk.end_byte,
                    None,
                    ChunkOrigin.MERGED,
                    merged[-1].symbol_ids + chunk.symbol_ids,
                )
                and not merged[-1].is_partial
                and not chunk.is_partial
            ):
                previous = merged.pop()
                start, end = previous.start_byte, chunk.end_byte
                symbol_ids = list(dict.fromkeys(previous.symbol_ids + chunk.symbol_ids))
                names = list(dict.fromkeys(previous.symbol_names + chunk.symbol_names))
                merged.append(
                    self._make_chunk(
                        result,
                        start,
                        end,
                        None,
                        ChunkOrigin.MERGED,
                        symbol_ids=symbol_ids,
                        symbol_names=names,
                    )
                )
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
        ids = (
            symbol_ids
            if symbol_ids is not None
            else [item.symbol_id for item in symbols]
        )
        names = (
            symbol_names
            if symbol_names is not None
            else [item.name for item in symbols]
        )
        scopes = self._scope_chain(symbol, result)
        chunk_type = (
            ChunkType.MERGED
            if origin is ChunkOrigin.MERGED
            else (ChunkType.GAP if symbol is None else self._chunk_type(symbol))
        )
        context_symbols = self._context_symbols(result, ids, symbol)
        enriched, enriched_tokens = self._select_enriched(
            result, start, end, scopes, symbol, context_symbols
        )
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        # A source range is not sufficient identity: two symbols can produce
        # the same bytes, and split/merged chunks can share a range. Include
        # lineage and symbol membership so uuid5 remains deterministic without
        # collapsing distinct logical chunks onto one primary key.
        identity = ":".join(
            (
                result.file_path,
                result.language,
                str(start),
                str(end),
                chunk_type.value,
                origin.value,
                ",".join(sorted(ids)),
                str(part_index),
                str(part_total),
                str(is_partial),
                content_hash,
            )
        )
        chunk_id = str(
            uuid5(NAMESPACE_URL, identity)
        )
        return CodeChunkDTO(
            chunk_id,
            chunk_type,
            origin,
            result.file_path,
            result.language,
            ids,
            names,
            scopes,
            start,
            end,
            self._line(result.source_bytes, start),
            self._line(result.source_bytes, max(start, end - 1)),
            content,
            enriched,
            None,
            is_partial,
            part_index,
            part_total,
            content_hash,
            token_count=max(1, enriched_tokens),
        )

    def _fits(
        self,
        result: RawExtractionResult,
        start: int,
        end: int,
        symbol: SymbolDTO | None,
        origin: ChunkOrigin,
        symbol_ids: list[str] | None = None,
    ) -> bool:
        scopes = self._scope_chain(symbol, result)
        _, enriched_tokens = self._select_enriched(
            result,
            start,
            end,
            scopes,
            symbol,
            self._context_symbols(result, symbol_ids or [], symbol),
        )
        return enriched_tokens <= self.max_chunk_tokens

    def _hard_split_ranges(
        self,
        result: RawExtractionResult,
        start: int,
        end: int,
        symbol: SymbolDTO | None,
        origin: ChunkOrigin,
    ) -> list[_Range]:
        """Split a single leaf node by token count as a last resort."""
        ranges: list[_Range] = []
        cursor = start
        while cursor < end:
            low, high, best = cursor + 1, end, cursor
            while low <= high:
                candidate = (low + high) // 2
                if self._fits(result, cursor, candidate, symbol, origin):
                    best = candidate
                    low = candidate + 1
                else:
                    high = candidate - 1
            if best == cursor:
                # A header can itself exceed the budget. Emit one byte rather
                # than looping forever; the resulting chunk is still bounded
                # as tightly as this input permits.
                best = min(cursor + 1, end)
            while best < end and (result.source_bytes[best] & 0xC0) == 0x80:
                best += 1
            ranges.append(_Range(cursor, best))
            cursor = best
        return ranges

    @staticmethod
    def _deduplicate(chunks: list[CodeChunkDTO]) -> list[CodeChunkDTO]:
        """Drop exact duplicate logical chunks before ORM persistence.

        Query patterns can occasionally describe the same syntax node more
        than once. Distinct symbols remain distinct because their IDs are part
        of the chunk identity above.
        """
        unique: dict[str, CodeChunkDTO] = {}
        for chunk in chunks:
            unique.setdefault(chunk.chunk_id, chunk)
        return list(unique.values())

    def _header(
        self,
        result: RawExtractionResult,
        scopes: list[str],
        symbol: SymbolDTO | None,
        context_symbols: list[SymbolDTO] | None = None,
        include_imports: bool = True,
    ) -> str:
        lines = [f"# File: {result.file_path}", f"# Language: {result.language}"]
        module = self._module_name(result.file_path)
        if module:
            lines.append(f"# Module: {module}")
        if scopes:
            lines.append(f"# Scope: {'.'.join(scopes)}")
        if symbol:
            lines.append(f"# Entity: {symbol.qualified_name}")
            lines.append(f"# Entity Type: {symbol.kind.value}")
            if symbol.signature:
                lines.append(f"# Signature: {self._compact(symbol.signature, 500)}")
            if symbol.docstring:
                lines.append(f"# Documentation: {self._compact(symbol.docstring, 600)}")
        elif context_symbols:
            entity_lines = [
                f"# - {item.qualified_name} [{item.kind.value}]"
                for item in context_symbols
            ]
            lines.append("# Entities:")
            lines.extend(entity_lines)
        if include_imports:
            imports = self._import_context_cache
            if imports:
                lines.append(f"# Imports:\n{imports}")
        return "\n".join(lines)

    def _select_enriched(
        self,
        result: RawExtractionResult,
        start: int,
        end: int,
        scopes: list[str],
        symbol: SymbolDTO | None,
        context_symbols: list[SymbolDTO],
    ) -> tuple[str, int]:
        key = (
            start,
            end,
            symbol.symbol_id if symbol else "",
            tuple(item.symbol_id for item in context_symbols),
        )
        cached = self._enriched_cache.get(key)
        if cached is not None:
            return cached
        content = result.source_bytes[start:end].decode("utf-8", errors="replace")
        header = self._header(result, scopes, symbol, context_symbols)
        enriched = f"{header}\n\n{content}"
        enriched_tokens = self.tokenizer.count(enriched)
        if enriched_tokens <= self.max_chunk_tokens:
            value = (enriched, enriched_tokens)
            self._enriched_cache[key] = value
            return value

        # Preserve source and identity first. Drop imports before any richer
        # entity context; imports are useful, but they are the least specific
        # part of a function/method embedding header.
        reduced = self._header(
            result, scopes, symbol, context_symbols, include_imports=False
        )
        reduced_enriched = f"{reduced}\n\n{content}"
        reduced_tokens = self.tokenizer.count(reduced_enriched)
        if reduced_tokens <= self.max_chunk_tokens:
            value = (reduced_enriched, reduced_tokens)
            self._enriched_cache[key] = value
            return value

        if symbol and symbol.docstring:
            shortened = replace(symbol, docstring=None)
            reduced = self._header(
                result, scopes, shortened, context_symbols, include_imports=False
            )
            reduced_enriched = f"{reduced}\n\n{content}"
            reduced_tokens = self.tokenizer.count(reduced_enriched)
            if reduced_tokens <= self.max_chunk_tokens:
                value = (reduced_enriched, reduced_tokens)
                self._enriched_cache[key] = value
                return value
        value = (enriched, enriched_tokens)
        self._enriched_cache[key] = value
        return value

    @staticmethod
    def _compact(value: str, limit: int) -> str:
        return " ".join(value.split())[:limit]

    @staticmethod
    def _module_name(file_path: str) -> str:
        path = file_path.replace("\\", "/")
        if "/" not in path:
            return path.rsplit(".", 1)[0]
        return path.rsplit("/", 1)[0].replace("/", ".")

    @staticmethod
    def _import_context(result: RawExtractionResult) -> str:
        values: list[str] = []
        for item in result.imports:
            statement = item.raw_statement.strip() if item.raw_statement else ""
            if statement and statement not in values:
                values.append(statement)
        return "\n".join(f"# - {value}" for value in values)

    def _context_symbols(
        self,
        result: RawExtractionResult,
        symbol_ids: list[str],
        symbol: SymbolDTO | None,
    ) -> list[SymbolDTO]:
        if symbol is not None:
            return [symbol]
        return [self._symbol_by_id[item] for item in symbol_ids if item in self._symbol_by_id]

    @staticmethod
    def _chunk_type(symbol: SymbolDTO) -> ChunkType:
        return (
            ChunkType(symbol.kind.value)
            if symbol.kind.value in {item.value for item in ChunkType}
            else ChunkType.FUNCTION
        )

    def _scope_chain(
        self,
        symbol: SymbolDTO | None, result: RawExtractionResult
    ) -> list[str]:
        if symbol is None:
            return []
        cached = self._scope_cache.get(symbol.symbol_id)
        if cached is not None:
            return cached
        chain: list[str] = []
        current = symbol
        while current:
            chain.append(current.name)
            current = (
                self._symbol_by_id.get(current.parent_symbol_id)
                if current.parent_symbol_id
                else None
            )
        value = list(reversed(chain))
        self._scope_cache[symbol.symbol_id] = value
        return value

    @staticmethod
    def _compute_newline_offsets(source: bytes) -> list[int]:
        # bytes.find is a C-level scan; this is far faster than a Python
        # per-byte loop (e.g. `enumerate(source)`) for large files.
        offsets: list[int] = []
        start = source.find(b"\n")
        while start != -1:
            offsets.append(start)
            start = source.find(b"\n", start + 1)
        return offsets

    def _line(self, source: bytes, byte_offset: int) -> int:
        # Previously `source[:byte_offset].count(b"\n")`: an O(file size)
        # rescan from the start of the file on every call, called twice per
        # chunk. With newline positions precomputed once per file, this is
        # an O(log n) binary search instead.
        return bisect.bisect_left(self._newline_offsets, byte_offset) + 1