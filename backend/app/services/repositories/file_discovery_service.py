from sqlalchemy.orm import Session

from pathlib import Path

SKIP_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    "dist",
    "build",
    ".next",
    ".venv",
    "venv",
    ".env"
}

MAX_FILE_SIZE = 2 * 1024 * 1024


class FileDiscoveryService:
    def __init__(self, db: Session):
        self.db = db

    def discover(self, repository_root: Path):

        files = []

        for path in repository_root.rglob("*"):

            if path.is_dir():
                continue

            if any(part in SKIP_DIRS for part in path.parts):
                continue

            if path.stat().st_size > MAX_FILE_SIZE:
                continue

            files.append(path)

        return files
    
      