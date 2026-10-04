import hashlib
import io
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

import polars as pl

from app.core.config import settings
from app.core.exceptions import AppError, ValidationError
from app.database.models.dataset import FileFormat


@dataclass
class ValidatedDatasetInfo:
    """Metadata extracted during file validation."""

    file_format: FileFormat
    file_size: int
    checksum: str
    row_count: int
    column_count: int
    columns: list[str]


def compute_sha256(content: bytes) -> str:
    """Compute SHA-256 hash of file content."""
    return hashlib.sha256(content).hexdigest()


def validate_file_size(content: bytes) -> int:
    """Verify file is not empty and does not exceed configured size limit."""
    file_size = len(content)
    if file_size == 0:
        raise ValidationError("Uploaded file is empty.")

    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if file_size > max_bytes:
        raise AppError(
            f"File size ({file_size / (1024 * 1024):.1f} MB) exceeds maximum allowed limit of {settings.max_upload_size_mb} MB.",
            code="FILE_TOO_LARGE",
            status_code=413,
            details={"file_size_bytes": file_size, "max_bytes": max_bytes},
        )
    return file_size


def validate_csv_content(content: bytes) -> Tuple[int, int, list[str]]:
    """Validate that CSV content can be decoded and parsed cleanly into a structured tabular dataframe."""
    try:
        # Check text decoding
        _ = content[:1024].decode("utf-8")
    except UnicodeDecodeError:
        raise ValidationError("CSV file must be valid UTF-8 encoded text.")

    try:
        # Parse using Polars to extract row count, column count, and verify table structure
        df = pl.read_csv(io.BytesIO(content), infer_schema_length=100)
        columns = list(df.columns)
        if not columns or len(columns) == 0:
            raise ValidationError("CSV dataset contains no columns or headers.")
        row_count = df.height
        column_count = df.width
        return row_count, column_count, columns
    except ValidationError:
        raise
    except Exception as exc:
        raise ValidationError(f"Malformed CSV file: {str(exc)}")


def validate_parquet_content(content: bytes) -> Tuple[int, int, list[str]]:
    """Validate that Parquet content is readable and contains valid tabular metadata."""
    # Parquet files start with magic bytes "PAR1"
    if len(content) < 8 or not (content.startswith(b"PAR1") or content.endswith(b"PAR1")):
        raise ValidationError("Invalid Parquet file header: missing PAR1 magic bytes.")

    try:
        df = pl.read_parquet(io.BytesIO(content))
        columns = list(df.columns)
        if not columns or len(columns) == 0:
            raise ValidationError("Parquet dataset contains no columns.")
        row_count = df.height
        column_count = df.width
        return row_count, column_count, columns
    except ValidationError:
        raise
    except Exception as exc:
        raise ValidationError(f"Malformed Parquet file: {str(exc)}")


def validate_dataset_file(content: bytes, original_filename: str) -> ValidatedDatasetInfo:
    """Entrypoint for validating uploaded CSV and Parquet files."""
    file_size = validate_file_size(content)
    checksum = compute_sha256(content)

    ext = Path(original_filename).suffix.lower()
    if ext == ".csv":
        file_format = FileFormat.CSV
        row_count, col_count, columns = validate_csv_content(content)
    elif ext == ".parquet":
        file_format = FileFormat.PARQUET
        row_count, col_count, columns = validate_parquet_content(content)
    else:
        raise ValidationError(
            f"Unsupported file format '{ext}'. Only CSV and Parquet files are supported.",
            details={"supported_formats": [".csv", ".parquet"], "provided": ext},
        )

    return ValidatedDatasetInfo(
        file_format=file_format,
        file_size=file_size,
        checksum=checksum,
        row_count=row_count,
        column_count=col_count,
        columns=columns,
    )
