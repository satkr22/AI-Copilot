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
            
            self._validate_github_repository(repo_dir)
            
            # Get every remote branch and its latest commit.
            result = subprocess.run(
                [
                    "git",
                    "-C",
                    str(repo_dir),
                    "for-each-ref",
                    "--format=%(refname:short) %(objectname)",
                    "refs/remotes/origin/",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            branches = {}

            for line in result.stdout.splitlines():
                branch_ref, commit_hash = line.split(maxsplit=1)

                branch_name = branch_ref.removeprefix("origin/")

                if branch_name == "HEAD":
                    continue

                branches[branch_name] = commit_hash

            return branches

        except Exception:
            raise ValueError("Cloning falied")

    # ---------- helpers ----------

    @staticmethod
    def _validate_id(value: str) -> None:
        if not value or not _ID_PATTERN.match(value):
            raise ValueError(f"Invalid id: {value!r}")
        
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