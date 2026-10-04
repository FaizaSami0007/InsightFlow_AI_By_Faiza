import os
from typing import List, Tuple

import polars as pl

from app.profiling.readers.base import DataReader


class CSVDataReader(DataReader):
    """Polars-powered CSV reader with delimiter detection and safe schema inference."""

    def _detect_separator(self, file_path: str) -> str:
        """Heuristically inspect header line for common CSV separators."""
        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            return ","
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            first_line = f.readline()

        delimiters = [",", "\t", ";", "|"]
        counts = {d: first_line.count(d) for d in delimiters}
        best_delimiter = max(counts, key=counts.get)
        return best_delimiter if counts[best_delimiter] > 0 else ","

    def read_schema(self, file_path: str) -> List[Tuple[str, str]]:
        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            return []
        sep = self._detect_separator(file_path)
        lf = pl.scan_csv(file_path, separator=sep, infer_schema_length=10000, ignore_errors=True, try_parse_dates=True)
        schema = lf.collect_schema()
        return [(name, str(dtype)) for name, dtype in schema.items()]

    def read_dataframe(self, file_path: str, max_rows: int | None = None) -> pl.DataFrame:
        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            return pl.DataFrame()
        sep = self._detect_separator(file_path)
        lf = pl.scan_csv(file_path, separator=sep, infer_schema_length=10000, ignore_errors=True, try_parse_dates=True)
        if max_rows is not None:
            lf = lf.limit(max_rows)
        return lf.collect()

    def read_sample(self, file_path: str, n_rows: int = 100) -> pl.DataFrame:
        return self.read_dataframe(file_path, max_rows=n_rows)

    def get_row_count(self, file_path: str) -> int:
        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            return 0
        sep = self._detect_separator(file_path)
        lf = pl.scan_csv(file_path, separator=sep, ignore_errors=True)
        return lf.select(pl.len()).collect().item()
