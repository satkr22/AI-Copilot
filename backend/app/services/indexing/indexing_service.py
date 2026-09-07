from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.indexing_jobs import IndexingJob, JobStatus
from app.models.repository import Repository
from app.models.repository_branch import RepositoryBranch
from app.models.repository_chunk import RepositoryChunk
from app.models.repository_file import RepositoryFile
from app.models.repository_import import RepositoryImport
from app.models.repository_symbol import RepositorySymbol
from app.services.indexing.discovery.file_discovery_service import FileDiscoveryService
from app.services.indexing.pipeline import IndexingPipeline


class IndexingService:
    """Coordinate repository snapshots; file parsing is delegated to the pipeline."""

    def __init__(self, db: Session):
        self.db = db
        self.discovery = FileDiscoveryService(db)
        self.pipeline = IndexingPipeline(db)

    def index_repository(self, repository: Repository) -> IndexingJob:
        if not repository.local_path:
            raise ValueError("Repository does not have a local storage path")
        repository_root = Path(repository.local_path)
        if not repository_root.exists():
            raise ValueError("Repository local storage does not exist")

        job = IndexingJob(repository_id=repository.id, status=JobStatus.PENDING, created_at=datetime.now(timezone.utc))
        self.db.add(job)
        try:
            job.status = JobStatus.RUNNING
            job.started_at = datetime.now(timezone.utc)
            branches = self.db.query(RepositoryBranch).filter(RepositoryBranch.repository_id == repository.id).all()
            if not branches:
                raise ValueError("Repository contains no branches")

            for branch in branches:
                self._clear_branch_snapshot(branch.id)
                discovered_files = self.discovery.discover(repository_root, branch.branch_name, branch.latest_commit_hash)
                for relative_path, file_size in discovered_files.items():
                    file = RepositoryFile(
                        repository_id=repository.id,
                        repository_branch_id=branch.id,
                        repository_branch_name=branch.branch_name,
                        path=relative_path,
                        commit_hash=branch.latest_commit_hash,
                        size_bytes=file_size,
                        indexed_at=datetime.now(timezone.utc),
                        created_at=datetime.now(timezone.utc),
                    )
                    self.db.add(file)
                    self.db.flush()
                    content = self.discovery.read_file(repository_root, branch.latest_commit_hash, relative_path)
                    self.pipeline.process_file(repository, branch, file, content)
                branch.indexed_at = datetime.now(timezone.utc)

            repository.indexed_at = datetime.now(timezone.utc)
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(job)
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

    def _clear_branch_snapshot(self, branch_id: str) -> None:
        file_ids = [row.id for row in self.db.query(RepositoryFile.id).filter(RepositoryFile.repository_branch_id == branch_id).all()]
        if file_ids:
            self.db.query(RepositoryChunk).filter(RepositoryChunk.repository_file_id.in_(file_ids)).delete(synchronize_session=False)
            self.db.query(RepositoryImport).filter(RepositoryImport.repository_file_id.in_(file_ids)).delete(synchronize_session=False)
            self.db.query(RepositorySymbol).filter(RepositorySymbol.repository_file_id.in_(file_ids)).delete(synchronize_session=False)
        self.db.query(RepositorySymbol).filter(RepositorySymbol.repository_branch_id == branch_id).delete(synchronize_session=False)
        self.db.query(RepositoryImport).filter(RepositoryImport.repository_branch_id == branch_id).delete(synchronize_session=False)
        self.db.query(RepositoryFile).filter(RepositoryFile.repository_branch_id == branch_id).delete(synchronize_session=False)
