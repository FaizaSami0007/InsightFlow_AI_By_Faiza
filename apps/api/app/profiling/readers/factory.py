from app.database.models.dataset import FileFormat
from app.profiling.readers.base import DataReader
from app.profiling.readers.csv_reader import CSVDataReader
from app.profiling.readers.parquet_reader import ParquetDataReader


def get_data_reader(file_format: FileFormat | str) -> DataReader:
    """Factory resolving the appropriate DataReader instance for a file format."""
    fmt = str(file_format).upper()
    if "PARQUET" in fmt:
        return ParquetDataReader()
    return CSVDataReader()
