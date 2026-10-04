from abc import ABC, abstractmethod
from typing import List, Tuple

import polars as pl


class DataReader(ABC):
    """Abstract interface for format-agnostic data reading into Polars structures."""

    @abstractmethod
    def read_schema(self, file_path: str) -> List[Tuple[str, str]]:
        """Return list of (column_name, polars_dtype_str)."""
        pass

    @abstractmethod
    def read_dataframe(self, file_path: str, max_rows: int | None = None) -> pl.DataFrame:
        """Read and return complete or bounded in-memory Polars DataFrame."""
        pass

    @abstractmethod
    def read_sample(self, file_path: str, n_rows: int = 100) -> pl.DataFrame:
        """Read small sample of records for inspection and representation."""
        pass

    @abstractmethod
    def get_row_count(self, file_path: str) -> int:
        """Compute or extract total row count efficiently."""
        pass
