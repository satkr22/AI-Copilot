from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.repository import Repository
from app.models.repository_branch import RepositoryBranch
from app.models.repository_file import ParseStatus, RepositoryFile
from app.services.indexing.chunking.cast_chunker import CastChunker
from app.services.indexing.extraction.query_extractor import QueryExtractor
from app.services.indexing.dto_models.models import ParseResultDTO
from app.services.indexing.parser.parser_service import ParserService
from app.services.indexing.persistence import IndexingPersistence


class IndexingPipeline:
    def __init__(self, db: Session, max_chunk_tokens: int = 800) -> None:
        self.db = db
        self.parser = ParserService()
        self.extractor = QueryExtractor()
        self.chunker = CastChunker(max_chunk_tokens)
        self.persistence = IndexingPersistence()

    def process_file(
        self,
        repository: Repository,
        branch: RepositoryBranch,
        file: RepositoryFile,
        content: bytes,
    ) -> None:
        file.parse_status = ParseStatus.PROCESSING
        try:
            from app.services.indexing.language_detector import detect_language

            language = detect_language(file.path, content)
            if language is None:
                file.parse_status = ParseStatus.SKIPPED
                file.parsed_at = datetime.now(timezone.utc)
                return
            parsed = self.parser.parse_tree(
                language, content.decode("utf-8", errors="replace")
            )
            print("####### parsed tree ########")
            raw = self.extractor.extract(
                parsed.tree, parsed.source_bytes, file.path, language, parsed.language
            )
            print("####### extracted ########")
            result = ParseResultDTO(
                file_path=file.path,
                language=language,
                file_content_hash=hashlib.sha256(parsed.source_bytes).hexdigest(),
                symbols=raw.symbols,
                imports=raw.imports,
                chunks=self.chunker.chunk(raw),
            )
            
            self.persistence.save(self.db, repository.id, branch.id, file, result)
            file.parse_status = ParseStatus.COMPLETED
            print("####### saved ########")
            
        except Exception as exc:
            file.parse_status = ParseStatus.FAILED
            file.parse_error = str(exc)[:500]
            file.parsed_at = datetime.now(timezone.utc)
