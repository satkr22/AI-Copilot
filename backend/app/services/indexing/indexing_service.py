from pathlib import Path

from sqlalchemy.orm import Session

from app.models.repository import Repository
from app.models.repository_branch import RepositoryBranch
from app.services.repositories.file_discovery_service import FileDiscoveryService


class IndexingService:
    def __init__(self, db: Session):
        self.db = db
        self.discovery = FileDiscoveryService(db)

    def index_repository(
        self,
        repository: Repository,
    ) -> None:

        if not repository.local_path:
            raise ValueError(
                "Repository does not have a local storage path"
            )

        repository_root = Path(repository.local_path)

        if not repository_root.exists():
            raise ValueError(
                "Repository local storage does not exist"
            )

        branches = (
            self.db.query(RepositoryBranch)
            .filter(
                RepositoryBranch.repository_id == repository.id
            )
            .all()
        )

        if not branches:
            raise ValueError(
                "Repository contains no branches"
            )

        for branch in branches:

            files = self.discovery.discover(
                repository_root=repository_root,
                branch_name=branch.branch_name,
                commit_hash=branch.latest_commit_hash,
            )

            for relative_path in files:

                content = self.discovery.read_file(
                    repository_root=repository_root,
                    commit_hash=branch.latest_commit_hash,
                    relative_path=relative_path,
                )

                self._index_file(
                    repository=repository,
                    branch=branch,
                    relative_path=relative_path,
                    content=content,
                )

    def _index_file(
        self,
        repository: Repository,
        branch: RepositoryBranch,
        relative_path: str,
        content: bytes,
    ) -> None:

        # Parsing
        # Chunking
        # Embedding
        # Persistence
        pass