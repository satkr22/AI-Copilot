from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.repository import Repository
from app.models.repository_branch import RepositoryBranch
from app.models.indexing_jobs import IndexingJob, JobStatus
from app.models.repository_file import RepositoryFile

from app.services.repositories.file_discovery_service import FileDiscoveryService


class IndexingService:
    def __init__(self, db: Session):
        self.db = db
        self.discovery = FileDiscoveryService(db)

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

                # Remove previous indexed snapshot for this branch
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

                    self.db.add(repo_file)

                    # ------------------------------------------------------
                    # Read file contents for parsing / chunking later.
                    # ------------------------------------------------------
                    #
                    # content = self.discovery.read_file(
                    #     repository_root=repository_root,
                    #     commit_hash=branch.latest_commit_hash,
                    #     relative_path=relative_path,
                    # )
                    #
                    # self._index_file(
                    #     repository=repository,
                    #     branch=branch,
                    #     repo_file=repo_file,
                    #     content=content,
                    # )

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
        pass