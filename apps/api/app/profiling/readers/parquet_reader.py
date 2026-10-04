import os
from typing import List, Tuple

import polars as pl

from app.profiling.readers.base import DataReader


class ParquetDataReader(DataReader):
    """Polars-powered Parquet reader utilizing embedded column chunk metadata."""

    def read_schema(self, file_path: str) -> List[Tuple[str, str]]:
        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            return []
        lf = pl.scan_parquet(file_path)
        schema = lf.collect_schema()
        return [(name, str(dtype)) for name, dtype in schema.items()]

    def read_dataframe(self, file_path: str, max_rows: int | None = None) -> pl.DataFrame:
        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            return pl.DataFrame()
        lf = pl.scan_parquet(file_path)
        if max_rows is not None:
            lf = lf.limit(max_rows)
        return lf.collect()

    def read_sample(self, file_path: str, n_rows: int = 100) -> pl.DataFrame:
        return self.read_dataframe(file_path, max_rows=n_rows)

    def get_row_count(self, file_path: str) -> int:
        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            return 0
        lf = pl.scan_parquet(file_path)
        return lf.select(pl.len()).collect().item()
