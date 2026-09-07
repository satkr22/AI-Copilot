from __future__ import annotations

from datetime import datetime, timezone
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy.orm import Session

from app.models.repository_chunk import (
    ChunkProvider,
    ChunkType as ORMChunkType,
    RepositoryChunk,
)
from app.models.repository_file import RepositoryFile
from app.models.repository_import import ImportLanguage, RepositoryImport
from app.models.repository_symbol import (
    RepositorySymbol,
    SymbolKind as ORMSymbolKind,
    SymbolLanguage,
)
from app.services.indexing.dto_models.models import ParseResultDTO


class IndexingPersistence:
    """Translate pipeline DTOs into the existing repository ORM rows."""

    def save(
        self,
        db: Session,
        repository_id: str,
        branch_id: str,
        file: RepositoryFile,
        result: ParseResultDTO,
    ) -> None:
        now = datetime.now(timezone.utc)
        file.language = result.language
        file.content_hash = result.file_content_hash
        # ORM ids are global across branches. Keep DTO ids stable for a branch
        # while preventing identical paths in two branch snapshots colliding.
        symbol_ids = {
            item.symbol_id: str(uuid5(NAMESPACE_URL, f"{branch_id}:{item.symbol_id}"))
            for item in result.symbols
        }
        import_ids = {
            item.import_id: str(uuid5(NAMESPACE_URL, f"{branch_id}:{item.import_id}"))
            for item in result.imports
        }
        chunk_ids = {
            item.chunk_id: str(uuid5(NAMESPACE_URL, f"{branch_id}:{item.chunk_id}"))
            for item in result.chunks
        }

        symbol_rows: dict[str, RepositorySymbol] = {}
        for symbol in result.symbols:
            try:
                kind = ORMSymbolKind(symbol.kind.value)
                language = SymbolLanguage(symbol.language)
            except ValueError:
                continue
            row = RepositorySymbol(
                id=symbol_ids[symbol.symbol_id],
                repository_id=repository_id,
                repository_branch_id=branch_id,
                repository_file_id=file.id,
                name=symbol.name,
                kind=kind,
                language=language,
                start_line=symbol.start_line,
                end_line=symbol.end_line,
                qualified_name=symbol.qualified_name,
                parent_symbol_id=(
                    symbol_ids.get(symbol.parent_symbol_id)
                    if symbol.parent_symbol_id
                    else None
                ),
                start_byte=symbol.start_byte,
                end_byte=symbol.end_byte,
                signature=symbol.signature,
                docstring=symbol.docstring,
                content_hash=symbol.content_hash,
                created_at=now,
            )
            db.add(row)
            symbol_rows[symbol.symbol_id] = row
        db.flush()

        for item in result.imports:
            try:
                language = ImportLanguage(item.language)
            except ValueError:
                continue
            db.add(
                RepositoryImport(
                    id=import_ids[item.import_id],
                    repository_id=repository_id,
                    repository_branch_id=branch_id,
                    repository_file_id=file.id,
                    import_path=item.import_path,
                    import_name=item.import_name,
                    language=language,
                    line_number=item.line_number,
                    alias=item.alias,
                    is_relative=item.is_relative,
                    start_byte=item.start_byte,
                    end_byte=item.end_byte,
                    raw_statement=item.raw_statement,
                    created_at=now,
                )
            )

        for chunk in result.chunks:
            try:
                chunk_type = ORMChunkType(chunk.chunk_type.value)
            except ValueError:
                chunk_type = ORMChunkType.FUNCTION
            symbol_id = (
                chunk.symbol_ids[0]
                if len(chunk.symbol_ids) == 1 and chunk.symbol_ids[0] in symbol_rows
                else None
            )
            db.add(
                RepositoryChunk(
                    id=chunk_ids[chunk.chunk_id],
                    repository_id=repository_id,
                    repository_branch_id=branch_id,
                    repository_file_id=file.id,
                    symbol_id=symbol_ids.get(symbol_id) if symbol_id else None,
                    provider=ChunkProvider.TREE_SITTER,
                    chunk_type=chunk_type,
                    origin=chunk.origin.value,
                    symbol_ids=[
                        symbol_ids.get(item, item) for item in chunk.symbol_ids
                    ],
                    scope_chain=chunk.scope_chain,
                    content=chunk.content,
                    enriched_content=chunk.enriched_content,
                    contextual_summary=chunk.contextual_summary,
                    start_byte=chunk.start_byte,
                    end_byte=chunk.end_byte,
                    start_line=chunk.start_line,
                    end_line=chunk.end_line,
                    token_count=chunk.token_count,
                    is_partial=chunk.is_partial,
                    part_index=chunk.part_index,
                    part_total=chunk.part_total,
                    content_hash=chunk.content_hash,
                    created_at=now,
                )
            )
        file.parsed_at = now
