import os
import shutil
from shutil import copytree, ignore_patterns
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from sqlalchemy import insert, delete
from sqlalchemy.orm import Session

from app.models.project import Project, ProjectStatus
from app.models.repository import Repository, SourceType
from app.models.repository_branch import RepositoryBranch
from app.models.repository_file import RepositoryFile
from app.models.indexing_jobs import IndexingJob

from app.schemas.repository import GithubRepositoryCreate

from app.services.repositories.storage_service import RepositoryStorageService
from app.services.indexing.indexing_service import IndexingService


class RepositoryService:

    def __init__(self, db: Session):
        self.db = db
        self.storage = RepositoryStorageService()
        self.indexing = IndexingService(db)

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
    
    def index_repository(
        self,
        user_id: str,
        repository_id: str
    ):
        
        repository = self.get_repository(user_id, repository_id)
        if repository is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Repository not found"
            )

        return self.indexing.index_repository(repository)

    
    

    def attach_repository(
        self,
        user_id: str,
        project_id: str,
        repository_id: str
    ) -> Repository:
        
        repository = self.get_repository(user_id, repository_id)

        if repository is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Repository not found"
            )
        
        # make a new repo by copying the existing one
        n_repository = Repository(
            user_id=user_id,
            source_type=SourceType.DUPLICATE,
            duplicate=repository_id,
            local_path=None,
            created_at=datetime.now(timezone.utc),
            indexed_at=None
        )
        self.db.add(n_repository)
        self.db.flush()
        
        # Create local storage folder and record the path
        storage_path = self.storage.ensure_repository_storage(user_id, n_repository.id)
        
        # Copy that repository inside disk in new repository folder
        # this is source path of old repo on the disk
        source_path = self.storage.build_repository_path(user_id, repository_id)
        
        shutil.copytree(
            src=source_path, 
            dst=storage_path, 
            dirs_exist_ok=True,
            ignore=ignore_patterns(
                "venv",
                ".venv",
                "__pycache__",
                "node_modules",
                "dist",
                "build",
                ".next",
            ),
            symlinks=True,
        )
        
        # get the branches of the new git folder 
        branches = self.storage.get_git_branches(storage_path)
        if not branches:
            raise ValueError("Uploaded Git repository contains no branches")
        
        return self._create_finalized_repository(
            user_id, 
            project_id, 
            n_repository, 
            storage_path, 
            branches
        )

    def create_github_repository_for_project(
        self,
        user_id: str,
        project_id: str,
        data: GithubRepositoryCreate
    ) -> Repository:

        repository = Repository(
            user_id=user_id,
            source_type=SourceType.GITHUB,
            source_url=str(data.source_url) if data.source_url else None,
            local_path=None,
            created_at=datetime.now(timezone.utc),
            indexed_at=None
        )

        self.db.add(repository)
        self.db.flush()

        # Create local storage folder and record the path
        storage_path = self.storage.ensure_repository_storage(user_id, repository.id)
        
        # now clone the github repo into local repo  folder
        try:
            branches = self.storage.clone_github_snapshot(storage_path, str(data.source_url))
        
            return self._create_finalized_repository(
                user_id=user_id,
                project_id=project_id,
                repository=repository,
                storage_path=storage_path,
                branches=branches,
            )
        
        except HTTPException:
            self.storage.delete_repository_storage(user_id, repository.id)
            self.db.rollback()
            raise
        except ValueError:
            self.storage.delete_repository_storage(user_id, repository.id)
            self.db.rollback()
            raise
        except Exception:
            self.storage.delete_repository_storage(user_id, repository.id)
            self.db.rollback()
            raise
        

    def create_zip_repository_for_project(
        self,
        user_id: str,
        project_id: str,
        file: UploadFile
    ) -> Repository:
        
        repository = Repository(
            user_id=user_id,
            source_type=SourceType.ZIP,
            source_url=None,
            branch=None,
            local_path=None,
            commit_hash=None,
            created_at=datetime.now(timezone.utc),
            indexed_at=None
        )

        self.db.add(repository)
        self.db.flush()

        # stroe zip till it is extracted 
        storage_path = self.storage.ensure_repository_storage(user_id=user_id, repository_id=repository.id)

        # Save the uploaded zip file into the repo folder (no unzip yet)
        filename = "upload.zip"
        zip_saved_path = storage_path/ filename
        with zip_saved_path.open("wb") as f:
            while chunk := file.file.read(1024 * 1024):
                f.write(chunk)
        
        # zip ingestion: extarct the zip, store the files and delete the zip, if extraction fails, delete the zip and repo folder
        branches = {}
        try:
            branches = self.storage.ingest_zip_snapshot(storage_path, zip_saved_path)
    
            return self._create_finalized_repository(
                user_id=user_id,
                project_id=project_id,
                repository=repository,
                storage_path=storage_path,
                branches=branches,
            )   
            
        except HTTPException:
            self.storage.delete_repository_storage(user_id, repository.id)
            self.db.rollback()
            raise
        except (subprocess.CalledProcessError, zipfile.BadZipFile) as e:
            self.storage.delete_repository_storage(user_id, repository.id)
            self.db.rollback()
            raise ValueError("ZIP extraction failed or unsupported zip") from e
        except ValueError:
            self.storage.delete_repository_storage(user_id, repository.id)
            self.db.rollback()
            raise
        except Exception:
            self.storage.delete_repository_storage(user_id, repository.id)
            self.db.rollback()
            raise
            
    # helper function to put repository data in db
    def _create_finalized_repository(
        self,
        user_id: str,
        project_id: str,
        repository: Repository,
        storage_path: Path,
        branches: dict[str, str],
    ) -> Repository:

        project = self._get_project_for_user(user_id, project_id)

        repository.local_path = str(storage_path)

        project.repository_id = repository.id
        project.status = ProjectStatus.IMPORTED
        project.updated_at = datetime.now(timezone.utc)

        
        self.db.execute(
            insert(RepositoryBranch),
            [
                {
                    "repository_id": repository.id,
                    "branch_name": branch_name,
                    "latest_commit_hash": commit_hash,
                    "original_commit_hash": commit_hash,
                    "indexed_at": None,
                }
                for branch_name, commit_hash in branches.items()
            ],
        )
        

        self.db.commit()
        self.db.refresh(repository)

        return repository



    def detach_repository_from_project(
        self,
        user_id: str,
        project_id: str
    ) -> Project:
        project = self._get_project_for_user(user_id, project_id)

        if project.repository_id is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project has no repository attached"
            )

        old_repository_id = project.repository_id
        project.repository_id = None
        project.status = ProjectStatus.CREATED
        project.updated_at = datetime.now(timezone.utc)
        self.db.flush()

        self.cleanup_repository_if_orphan(user_id, old_repository_id)

        self.db.commit()
        self.db.refresh(project)
        return project

    # ---------- orphan helpers ----------

    def is_repository_orphan(self, user_id: str, repository_id: str) -> bool:
        """True when no project of this user still references this repository."""
        count = (
            self.db.query(Project)
            .filter(
                Project.user_id == user_id,
                Project.repository_id == repository_id,
            )
            .count()
        )
        return count == 0


    def get_repository_branches(
        self,
        repository_id: str
    ):
        return (
            self.db.query(RepositoryBranch)
            .filter(
                RepositoryBranch.repository_id == repository_id
            ).all()
        )
        
    def get_repository_files(
        self,
        repository_id: str
    ):
        return (
            self.db.query(RepositoryFile)
            .filter(
                RepositoryFile.repository_id == repository_id
            ).all()
        )
        
    def get_index_jobs(
        self,
        repository_id: str
    ):
        return (
            self.db.query(IndexingJob)
            .filter(
                IndexingJob.repository_id == repository_id
            ).all()
        )
        
        

    def cleanup_repository_if_orphan(
        self, 
        user_id: str, 
        repository_id: str
    ) -> None:
        
        if not self.is_repository_orphan(user_id, repository_id):
            return

        repository = self.get_repository(user_id, repository_id)
        if repository is None:
            return
        
        # Delete all related data in bulk (single queries each)
        
        # 1. Delete repository files
        stmt = delete(RepositoryFile).where(
            RepositoryFile.repository_id == repository_id
        )
        self.db.execute(stmt)
        
        # 2. Delete indexing jobs
        stmt = delete(IndexingJob).where(
            IndexingJob.repository_id == repository_id
        )
        self.db.execute(stmt)
            
        # 3. Delete repository branches
        stmt = delete(RepositoryBranch).where(
            RepositoryBranch.repository_id == repository_id
        )
        self.db.execute(stmt)
        
        # 4. Remove repo data from local storage
        self.storage.delete_repository_storage(user_id, repository_id)
        
        # 5. Delete the repository itself
        self.db.delete(repository)
        self.db.flush()

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
