"""File Upload Security, Magic Byte Signature Validation, and Path Traversal Prevention."""

import os
import re
import zipfile
from typing import BinaryIO, List, Optional, Tuple

from app.core.exceptions import ValidationError

# Dangerous executable signatures to block unconditionally
DANGEROUS_SIGNATURES = [
    (b"MZ", "Windows Executable (PE/DLL/EXE)"),
    (b"\x7fELF", "Linux ELF Executable"),
    (b"\xca\xfe\xba\xbe", "Mach-O / Java Class Binary"),
    (b"\xfe\xed\xfa\xce", "Mach-O 32-bit"),
    (b"\xfe\xed\xfa\xcf", "Mach-O 64-bit"),
    (b"#!", "Shell / Script Executable"),
    (b"<!DOCTYPE html", "Raw HTML Script"),
    (b"<script", "Executable JavaScript"),
]

ALLOWED_EXTENSIONS = {
    ".csv",
    ".parquet",
    ".json",
    ".xlsx",
    ".xls",
    ".pdf",
    ".docx",
    ".txt",
    ".tsv",
}

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB
MAX_DECOMPRESSED_RATIO = 100  # Zip bomb safety ratio
MAX_DECOMPRESSED_SIZE = 150 * 1024 * 1024  # 150 MB


class FileGuard:
    """Enterprise file security, mime validation, and decompression bomb guard."""

    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """
        Strip path traversal vectors (../, ..\\), null bytes, and unsafe characters.
        Returns a clean base filename.
        """
        if not filename:
            return "unnamed_file"

        # Remove null bytes
        cleaned = filename.replace("\x00", "")
        # Get base name only
        cleaned = os.path.basename(cleaned)
        # Strip directory separators
        cleaned = cleaned.replace("/", "").replace("\\", "")
        # Replace non-alphanumeric (except . - _)
        cleaned = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", cleaned)
        # Prevent hidden files
        if cleaned.startswith("."):
            cleaned = "file_" + cleaned

        return cleaned or "safe_file"

    @classmethod
    def validate_file_content(cls, filename: str, content: bytes) -> Tuple[bool, Optional[str]]:
        """
        Validate file extension, size, magic signature, and binary safety.
        Returns (is_valid, error_message).
        """
        # 1. Size check
        if len(content) > MAX_FILE_SIZE_BYTES:
            return False, f"File size ({len(content) / 1024 / 1024:.2f} MB) exceeds maximum limit of 50 MB."

        if len(content) == 0:
            return False, "File is empty (0 bytes)."

        # 2. Extension check
        _, ext = os.path.splitext(filename.lower())
        if ext not in ALLOWED_EXTENSIONS:
            return False, f"File extension '{ext}' is not permitted. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}."

        # 3. Executable header detection
        for sig, description in DANGEROUS_SIGNATURES:
            if content.startswith(sig) or (sig == b"<!DOCTYPE html" and sig in content[:256]):
                return False, f"Dangerous executable or script format detected: {description}."

        # 4. Parquet signature verification
        if ext == ".parquet":
            if not (content.startswith(b"PAR1") or content.endswith(b"PAR1")):
                return False, "Invalid Parquet format: missing PAR1 magic bytes header/footer."

        # 5. PDF signature verification
        if ext == ".pdf":
            if not content.startswith(b"%PDF-"):
                return False, "Invalid PDF format: missing %PDF header."

        return True, None

    @classmethod
    def inspect_zip_archive_safety(cls, zip_bytes: bytes) -> Tuple[bool, Optional[str]]:
        """
        Inspect zip/docx/xlsx archive to protect against zip-bombs and decompression attacks.
        """
        try:
            import io

            with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
                total_uncompressed_size = 0
                for info in zf.infolist():
                    # Check for path traversal in archive internal filenames
                    if ".." in info.filename or info.filename.startswith("/") or info.filename.startswith("\\"):
                        return False, "Archive contains malicious path traversal entry."
                    total_uncompressed_size += info.file_size

                compressed_size = max(len(zip_bytes), 1)
                ratio = total_uncompressed_size / compressed_size

                if ratio > MAX_DECOMPRESSED_RATIO:
                    return False, f"Potential zip bomb detected: compression ratio {ratio:.1f}x exceeds threshold."

                if total_uncompressed_size > MAX_DECOMPRESSED_SIZE:
                    return False, f"Total uncompressed content ({total_uncompressed_size / 1024 / 1024:.1f} MB) exceeds limit."

                return True, None
        except zipfile.BadZipFile:
            return False, "Corrupted or invalid zip archive."
