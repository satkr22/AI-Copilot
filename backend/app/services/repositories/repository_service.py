from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.project import Project, ProjectStatus
from app.models.repository import Repository, SourceType
from app.schemas.repository import GithubRepositoryCreate


class RepositoryService:

    def __init__(self, db: Session):
        self.db = db

    def list_repositories(self, user_id: str) -> list[Repository]:
        return (
            self.db.query(Repository)
            .filter(Repository.user_id == user_id)
            .all()
        )

    def get_repository(
        self,
        user_id: str,
        repository_id: str
    ) -> Repository | None:
        return (
            self.db.query(Repository)
            .filter(
                Repository.id == repository_id,
                Repository.user_id == user_id
            )
            .one_or_none()
        )

    def get_project_repository(
        self,
        user_id: str,
        project_id: str
    ) -> Repository:
        project = self._get_project_for_user(user_id, project_id)

        if project.repository_id is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project has no repository attached"
            )

        repository = self.get_repository(user_id, project.repository_id)
        if repository is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attached repository not found"
            )

        return repository

    def attach_repository(
        self,
        user_id: str,
        project_id: str,
        repository_id: str
    ) -> Project:
        project = self._get_project_for_user(user_id, project_id)
        repository = self.get_repository(user_id, repository_id)

        if repository is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Repository not found"
            )

        project.repository_id = repository.id
        project.status = ProjectStatus.IMPORTED
        project.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(project)

        return project

    def create_github_repository_for_project(
        self,
        user_id: str,
        project_id: str,
        data: GithubRepositoryCreate
    ) -> Repository:
        project = self._get_project_for_user(user_id, project_id)

        repository = Repository(
            user_id=user_id,
            source_type=SourceType.GITHUB,
            source_url=str(data.source_url) if data.source_url else None,
            branch=data.branch,
            local_path=None,
            commit_hash=None,
            created_at=datetime.now(timezone.utc),
            indexed_at=None
        )

        self.db.add(repository)
        self.db.flush()

        project.repository_id = repository.id
        project.status = ProjectStatus.IMPORTED
        project.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(repository)

        return repository

    def update_index_status(self):
        pass

    def _get_project_for_user(
        self,
        user_id: str,
        project_id: str
    ) -> Project:
        project = (
            self.db.query(Project)
            .filter(
                Project.id == project_id,
                Project.user_id == user_id
            )
            .one_or_none()
        )

        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        return project
