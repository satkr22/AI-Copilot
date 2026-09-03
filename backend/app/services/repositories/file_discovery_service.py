import subprocess
from pathlib import Path

from sqlalchemy.orm import Session


SKIP_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    "dist",
    "build",
    ".next",
    ".venv",
    "venv",
}

SKIP_FILES = {
    ".env",
}

MAX_FILE_SIZE = 2 * 1024 * 1024


class FileDiscoveryService:
    def __init__(self, db: Session):
        self.db = db

    def discover(
        self,
        repository_root: Path,
        branch_name: str,
        commit_hash: str,
    ) -> list[str]:

        result = subprocess.run(
            [
                "git",
                "-C",
                str(repository_root),
                "ls-tree",
                "-r",
                "--name-only",
                commit_hash,
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        files = []

        for relative_path in result.stdout.splitlines():
            relative_path = relative_path.strip()

            if not relative_path:
                continue

            path = Path(relative_path)

            if any(part in SKIP_DIRS for part in path.parts):
                continue

            if path.name in SKIP_FILES:
                continue

            file_size = self._get_file_size(
                repository_root,
                commit_hash,
                relative_path,
            )

            if file_size > MAX_FILE_SIZE:
                continue

            files.append(relative_path)

        return files

    def read_file(
        self,
        repository_root: Path,
        commit_hash: str,
        relative_path: str,
    ) -> bytes:

        result = subprocess.run(
            [
                "git",
                "-C",
                str(repository_root),
                "show",
                f"{commit_hash}:{relative_path}",
            ],
            check=True,
            capture_output=True,
        )

        return result.stdout

    def _get_file_size(
        self,
        repository_root: Path,
        commit_hash: str,
        relative_path: str,
    ) -> int:

        result = subprocess.run(
            [
                "git",
                "-C",
                str(repository_root),
                "cat-file",
                "-s",
                f"{commit_hash}:{relative_path}",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        return int(result.stdout.strip())