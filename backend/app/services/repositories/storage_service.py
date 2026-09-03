import os
import re
import shutil
import subprocess
from pathlib import Path
import zipfile
from app.core.config import settings

_ID_PATTERN = re.compile(r"^[A-Za-z0-9_\-]+$")


class RepositoryStorageService:
    """Manages local filesystem storage for repositories."""

    def __init__(self) -> None:
        self.storage_root = Path(settings.REPOSITORY_STORAGE_PATH).resolve()

    # ---------- public API ----------

    def build_repository_path(self, user_id: str, repository_id: str) -> Path:
        self._validate_id(user_id)
        self._validate_id(repository_id)
        return self.storage_root / user_id / repository_id

    def ensure_repository_storage(self, user_id: str, repository_id: str) -> Path:
            path = self.build_repository_path(user_id, repository_id)
            path.mkdir(parents=True, exist_ok=True)
            return path

    def delete_repository_storage(self, user_id: str, repository_id: str) -> None:
        path = self.build_repository_path(user_id, repository_id)
        if not path.exists():
            return
        # Safety: resolved path must remain inside storage root
        resolved = path.resolve()
        try:
            resolved.relative_to(self.storage_root)
        except ValueError:
            raise RuntimeError("Refusing to delete path outside storage root")
        print(resolved)
        shutil.rmtree(resolved, ignore_errors=True)
        
        
        
    def extract_zip_safely(
        self,
        zip_file: Path,
        destination: Path
    ) -> None:
        """
        Extract ZIP while preventing Zip Slip.
        """
        #  # Zip Slip protection
        destination_resolved = destination.resolve()
        with zipfile.ZipFile(zip_file, "r") as archive:

            for member in archive.infolist():

                member_path = destination / member.filename

                resolved = member_path.resolve()

                try:
                    resolved.relative_to(destination_resolved)
                except ValueError:
                    raise ValueError(
                    f"Illegal archive path: {member.filename}"
                )
            
            archive.extractall(destination)
            os.remove(destination / "upload.zip")
            
            print("Destination:", destination)
            print("Items:", [p.name for p in destination.iterdir()])
            
        # -------- Flatten single top-level folder --------
        items = list(destination.iterdir())

        if len(items) == 1 and items[0].is_dir():
            inner_folder = items[0]

            for child in inner_folder.iterdir():
                shutil.move(str(child), str(destination))

            inner_folder.rmdir()

    def initialize_zip_repository(
        self,
        repo_dir: Path,
    ) -> dict[str, str]:

        subprocess.run(
            ["git", "init", "-b", "main", str(repo_dir)],
            check=True,
            capture_output=True,
            text=True,
        )
        
        subprocess.run(
            [
                "git", "-C", str(repo_dir),
                "config", "user.name",
                "Repository-Import",
            ],
            check=True,
        )

        subprocess.run(
            [
                "git", "-C", str(repo_dir),
                "config", "user.email",
                "repository-import@localhost",
            ],
            check=True,
        )

        subprocess.run(
            ["git", "-C", str(repo_dir), "add", "."],
            check=True,
            capture_output=True,
            text=True,
        )

        re = subprocess.run(
            [
                "git",
                "-C",
                str(repo_dir),
                "commit",
                "-m",
                "Initial commit",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        # Validate that Git created a valid repository.
        self.validate_git_repository(repo_dir)
        
        # Get every remote branch and its latest commit.
        result = subprocess.run(
            [
                "git",
                "-C",
                str(repo_dir),
                "rev-parse",
                "HEAD",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        
        commit_hash = result.stdout.strip()

        return {
            "main": commit_hash
        }

    def ingest_zip_snapshot(
        self,
        destination_path: Path,
        uploaded_zip_path: Path,
    ) -> dict[str, str]:
        try:
            self.extract_zip_safely(uploaded_zip_path, Path(destination_path))
            if (destination_path / ".git").exists():
                self.validate_git_repository(destination_path)
                branches =  self.get_git_branches(destination_path)    
                if not branches:
                    raise ValueError("Uploaded Git repository contains no branches")        
                return branches
            
            return self.initialize_zip_repository(destination_path)
        
        except ValueError:
            raise
        
        except Exception:
            raise
    
    
    def clone_github_snapshot(
        self,
        repo_dir: Path,
        github_url: str,
    ) -> dict[str, str]:
        try:
            subprocess.run(
                [
                    "git",
                    "clone",
                    github_url,
                    str(repo_dir),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            
            # Validate that Git created a valid repository.  
            self.validate_git_repository(repo_dir)
            
            branches =  self.get_git_branches(repo_dir)
            if not branches:
                raise ValueError("Uploaded Git repository contains no branches")
            return branches

        except Exception:
            raise ValueError("Cloning falied")
    
    
    
    def validate_git_repository(
        self,
        repo_dir: Path,
    ) -> None:

        # First verify that Git recognizes this as a repository.
        subprocess.run(
            [
                "git",
                "-C",
                str(repo_dir),
                "rev-parse",
                "--git-dir",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        # Verify Git object database and connectivity.
        result = subprocess.run(
            [
                "git",
                "-C",
                str(repo_dir),
                "fsck",
                "--full",
                "--no-reflogs",
            ],
            capture_output=True,
            text=True,
        )
        
        repo_root = repo_dir.resolve()
        
        for path in repo_dir.rglob("*"):
            if path.is_symlink():
                resolved = path.resolve()
                try:
                    resolved.relative_to(repo_root)
                except ValueError:
                    raise ValueError(
                        f"Repository contains symlink outside repository: {path}"
                    )

        if result.returncode != 0:
            raise ValueError(
                f"Git repository is corrupted:\n{result.stdout}\n{result.stderr}"
            )
    
    def get_git_branches(
        self,
        repo_dir: Path,
    ) -> dict[str, str]:

        result = subprocess.run(
            [
                "git",
                "-C",
                str(repo_dir),
                "for-each-ref",
                "--format=%(refname) %(objectname)",
                "refs/heads/",
                "refs/remotes/",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        branches = {}

        for line in result.stdout.splitlines():
            ref_name, commit_hash = line.split(maxsplit=1)

            if ref_name.startswith("refs/heads/"):
                branch_name = ref_name.removeprefix("refs/heads/")

            elif ref_name.startswith("refs/remotes/origin/"):
                branch_name = ref_name.removeprefix("refs/remotes/origin/")

                if branch_name == "HEAD":
                    continue

            else:
                continue

            branches[branch_name] = commit_hash

        return branches
    
    

    # ---------- helpers ----------

    @staticmethod
    def _validate_id(value: str) -> None:
        if not value or not _ID_PATTERN.match(value):
            raise ValueError(f"Invalid id: {value!r}")
       
    # detect any symlink outside repository
    def _validate_github_repository(self, repo_dir: Path) -> None:
        repo_root = repo_dir.resolve()

        for path in repo_dir.rglob("*"):
            if path.is_symlink():
                resolved = path.resolve()

                try:
                    resolved.relative_to(repo_root)
                except ValueError:
                    raise ValueError(
                        f"Repository contains symlink outside repository: {path}"
                    )

