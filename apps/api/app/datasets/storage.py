import os
import shutil
import uuid
from pathlib import Path
from typing import BinaryIO, Protocol

from app.core.config import settings
from app.core.exceptions import AppError
from app.core.logging import logger


class StorageProvider(Protocol):
    """Storage provider protocol abstracting local filesystem and future S3/GCS object storage."""

    def save_file(self, file_bytes: bytes, original_filename: str) -> str: ...
    def get_file_bytes(self, storage_reference: str) -> bytes: ...
    def delete_file(self, storage_reference: str) -> bool: ...
    def file_exists(self, storage_reference: str) -> bool: ...
    def get_file_path(self, storage_reference: str) -> Path: ...


class LocalStorageProvider:
    """Secure local filesystem storage provider with path traversal protection and UUID keys."""

    def __init__(self, base_dir: str | None = None) -> None:
        self.base_dir = Path(base_dir or settings.data_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_safe_path(self, storage_reference: str) -> Path:
        """Sanitize reference and ensure it resolves strictly within base_dir."""
        clean_ref = os.path.basename(storage_reference)
        target_path = (self.base_dir / clean_ref).resolve()
        if not str(target_path).startswith(str(self.base_dir)):
            raise AppError(
                "Path traversal detected in storage reference", code="STORAGE_SECURITY_ERROR", status_code=400
            )
        return target_path

    ALLOWED_EXTENSIONS = {".csv", ".parquet", ".pdf", ".docx", ".doc", ".txt", ".md", ".json", ".markdown"}

    def save_file(self, file_bytes: bytes, original_filename: str) -> str:
        """Store file bytes under a generated unique identifier preserving safe extension."""
        safe_ext = Path(original_filename).suffix.lower()
        if safe_ext not in self.ALLOWED_EXTENSIONS:
            safe_ext = ".bin"

        unique_key = f"{uuid.uuid4().hex}{safe_ext}"
        target_path = self._resolve_safe_path(unique_key)

        try:
            with open(target_path, "wb") as f:
                f.write(file_bytes)
            logger.info(f"Stored file {unique_key} ({len(file_bytes)} bytes)")
            return unique_key
        except Exception as exc:
            logger.error(f"Failed to write file to {target_path}: {exc}")
            raise AppError("Failed to persist file to storage", code="STORAGE_WRITE_ERROR", status_code=500)

    def save_stream(self, stream: BinaryIO, original_filename: str) -> str:
        """Stream file directly to disk avoiding full memory buffering."""
        safe_ext = Path(original_filename).suffix.lower()
        if safe_ext not in self.ALLOWED_EXTENSIONS:
            safe_ext = ".bin"

        unique_key = f"{uuid.uuid4().hex}{safe_ext}"
        target_path = self._resolve_safe_path(unique_key)

        try:
            with open(target_path, "wb") as f:
                shutil.copyfileobj(stream, f)
            return unique_key
        except Exception as exc:
            logger.error(f"Failed to stream dataset file to {target_path}: {exc}")
            raise AppError("Failed to stream dataset file to storage", code="STORAGE_WRITE_ERROR", status_code=500)

    def get_file_bytes(self, storage_reference: str) -> bytes:
        target_path = self._resolve_safe_path(storage_reference)
        if not target_path.exists():
            raise AppError("Dataset file not found in storage", code="STORAGE_FILE_NOT_FOUND", status_code=404)
        return target_path.read_bytes()

    def get_file_path(self, storage_reference: str) -> Path:
        target_path = self._resolve_safe_path(storage_reference)
        if not target_path.exists():
            raise AppError("Dataset file not found in storage", code="STORAGE_FILE_NOT_FOUND", status_code=404)
        return target_path

    def delete_file(self, storage_reference: str) -> bool:
        try:
            target_path = self._resolve_safe_path(storage_reference)
            if target_path.exists():
                target_path.unlink()
                logger.info(f"Deleted dataset file {storage_reference}")
                return True
            return False
        except Exception as exc:
            logger.warning(f"Error deleting dataset file {storage_reference}: {exc}")
            return False

    def file_exists(self, storage_reference: str) -> bool:
        try:
            target_path = self._resolve_safe_path(storage_reference)
            return target_path.exists()
        except Exception:
            return False


_storage_instance: StorageProvider | None = None


def get_storage_provider() -> StorageProvider:
    """Return configured storage provider instance."""
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = LocalStorageProvider()
    return _storage_instance
