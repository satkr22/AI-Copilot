from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.repository import Repository
from app.models.repository_branch import RepositoryBranch
from app.models.indexing_jobs import IndexingJob, JobStatus
from app.models.repository_file import RepositoryFile, ParseStatus
from app.models.repository_symbol import RepositorySymbol, SymbolKind, SymbolLanguage
from app.models.repository_import import RepositoryImport, ImportLanguage


from app.services.repositories.file_discovery_service import FileDiscoveryService
from app.services.indexing.parser_service import ParserService
from app.services.indexing.language_detector import detect_language
from app.services.indexing.dto import SymbolDTO, ImportDTO, ParseResult


class IndexingService:
    def __init__(self, db: Session):
        self.db = db
        self.discovery = FileDiscoveryService(db)
        self.parser = ParserService()

    def index_repository(
        self,
        repository: Repository,
    ) -> IndexingJob:
        """
        Repository indexing flow
        
        Repository
            └── Branch
                    └── Discover files
                            └── Persist files in chunks and qdrant.
        """

        # ------------------------------------------------------------------
        # Validate repository storage
        # ------------------------------------------------------------------
        if not repository.local_path:
            raise ValueError("Repository does not have a local storage path")

        repository_root = Path(repository.local_path)

        if not repository_root.exists():
            raise ValueError("Repository local storage does not exist")

        # ------------------------------------------------------------------
        # Create indexing job
        # ------------------------------------------------------------------
        job = IndexingJob(
            repository_id=repository.id,
            status=JobStatus.PENDING,
            created_at=datetime.now(timezone.utc),
        )

        self.db.add(job)
        # self.db.flush()

        try:
            # --------------------------------------------------------------
            # Mark running
            # --------------------------------------------------------------
            job.status = JobStatus.RUNNING
            job.started_at = datetime.now(timezone.utc)

            branches = (
                self.db.query(RepositoryBranch)
                .filter(RepositoryBranch.repository_id == repository.id)
                .all()
            )

            if not branches:
                raise ValueError("Repository contains no branches")

            # --------------------------------------------------------------
            # Index every branch snapshot
            # --------------------------------------------------------------
            for branch in branches:

                # Remove previous parsed snapshot for this branch from repository_symbols
                (
                    self.db.query(RepositorySymbol)
                    .filter(
                        RepositorySymbol.repository_branch_id == branch.id
                    )
                    .delete(synchronize_session=False)
                )
                
                # Remove previous parsed snapshot for this branch from repository_imports
                (
                    self.db.query(RepositoryImport)
                    .filter(
                        RepositoryImport.repository_branch_id == branch.id
                    )
                    .delete(synchronize_session=False)
                )

                # Remove previous indexed snapshot for this branch from repository_files
                (
                    self.db.query(RepositoryFile)
                    .filter(
                        RepositoryFile.repository_branch_id == branch.id
                    )
                    .delete(synchronize_session=False)
                )
                
                discovered_files = self.discovery.discover(
                    repository_root=repository_root,
                    branch_name=branch.branch_name,
                    commit_hash=branch.latest_commit_hash,
                )

                # Persist metadata only
                for relative_path, file_size in discovered_files.items():

                    repo_file = RepositoryFile(
                        repository_id=repository.id,
                        repository_branch_id=branch.id,
                        repository_branch_name=branch.branch_name,
                        path=relative_path,
                        commit_hash=branch.latest_commit_hash,
                        size_bytes=file_size,
                        language=None,
                        indexed_at=datetime.now(timezone.utc),
                        created_at=datetime.now(timezone.utc),
                    )
                    # parsestaus, pasrseerror, parsedat

                    self.db.add(repo_file)
                    self.db.flush()

                    # ------------------------------------------------------
                    # Read file contents for parsing / chunking later.
                    # ------------------------------------------------------
                    
                    content = self.discovery.read_file(
                        repository_root=repository_root,
                        commit_hash=branch.latest_commit_hash,
                        relative_path=relative_path,
                    )
                    
                    self._index_file(
                        repository=repository,
                        branch=branch,
                        repo_file=repo_file,
                        content=content,
                    )

                # Branch indexed successfully
                branch.indexed_at = datetime.now(timezone.utc)
                

            # --------------------------------------------------------------
            # Repository indexed successfully
            # --------------------------------------------------------------
            repository.indexed_at = datetime.now(timezone.utc)

            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now(timezone.utc)

            self.db.commit()
            self.db.refresh(job)
            
            print("indexing done")
            return job

        except Exception as exc:
            self.db.rollback()

            job.status = JobStatus.FAILED
            job.completed_at = datetime.now(timezone.utc)
            job.error_message = str(exc)[:500]

            self.db.add(job)
            self.db.commit()
            self.db.refresh(job)

            raise

    # ----------------------------------------------------------------------
    # Parsing / Chunking / Embeddings
    # ----------------------------------------------------------------------
    #
    def _index_file(
        self,
        repository: Repository,
        branch: RepositoryBranch,
        repo_file: RepositoryFile,
        content: bytes,
    ) -> None:
        # ----------------------------------------------------------------------
        # Parsing
        # ----------------------------------------------------------------------
        
        repo_file.parse_status = ParseStatus.PROCESSING
        
        # language detection
        language = detect_language(repo_file.path)
        if language is None:
            repo_file.parsed_at = datetime.now(tz=timezone.utc)
            repo_file.parse_status = ParseStatus.SKIPPED
            return
        
        repo_file.language = language
        
    
        # parse source code file
        try:
            source = content.decode("utf-8", errors="replace")
            parse_result = self.parser.parse(language, source)

            # enter each symbol in db 'repository_symbols' table
            self._save_symbols(
                repository, 
                branch, 
                repo_file, 
                parse_result.symbols
            )
                
            # enter each import in db 'repository_imports' table
            self._save_imports(
                repository, 
                branch, 
                repo_file, 
                parse_result.imports
            )
                
            repo_file.parsed_at = datetime.now(timezone.utc)
            repo_file.parse_status = ParseStatus.COMPLETED
             
        except Exception as e:
            repo_file.parse_status = ParseStatus.FAILED
            repo_file.parse_error = str(e)[:500]
            return
    
    def _save_symbols(
        self,
        repository: Repository,
        branch: RepositoryBranch,
        repo_file: RepositoryFile,
        symbols: list[SymbolDTO]
    ):
        for symbol in symbols:
                     
            file_symbol = RepositorySymbol(
                repository_id = repository.id,
                repository_branch_id = branch.id,
                repository_file_id = repo_file.id,
                name = symbol.name,
                kind = symbol.kind,
                language = symbol.language,
                start_line = symbol.start_line,
                end_line = symbol.end_line,
                created_at = datetime.now(tz=timezone.utc)
            )
            self.db.add(file_symbol)
            
    
    def _save_imports(
        self,
        repository: Repository,
        branch: RepositoryBranch,
        repo_file: RepositoryFile,
        imports: list[ImportDTO]
    ):
        for imprt in imports:
            file_import = RepositoryImport(
                repository_id = repository.id,
                repository_branch_id = branch.id,
                repository_file_id = repo_file.id,
                language = imprt.language,
                import_path = imprt.import_path,
                import_name = imprt.import_name,
                line_number = imprt.line_number,
                created_at = datetime.now(tz=timezone.utc)
            )
            self.db.add(file_import)
            
        
        
        