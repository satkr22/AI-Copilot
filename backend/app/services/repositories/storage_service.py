import re
import shutil
from pathlib import Path

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
        shutil.rmtree(resolved, ignore_errors=True)

    # ---------- helpers ----------

    @staticmethod
    def _validate_id(value: str) -> None:
        if not value or not _ID_PATTERN.match(value):
            raise ValueError(f"Invalid id: {value!r}")