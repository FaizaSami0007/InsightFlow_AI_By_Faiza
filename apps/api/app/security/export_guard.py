"""Export Security & Spreadsheet Formula Injection (CSV Injection / DDE) Neutralization."""

import re
from typing import Any, Dict, List

FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r", "|", "%")


class ExportGuard:
    """Security utilities for safe CSV, Excel, and report exports."""

    @classmethod
    def sanitize_cell_value(cls, value: Any) -> Any:
        """
        Neutralize formula injection by prepending a single quote (') if string
        begins with dangerous formula trigger characters (=, +, -, @, \\t, \\r, |, %).
        """
        if isinstance(value, str):
            # Strip leading whitespace for check
            stripped = value.lstrip()
            if stripped and stripped.startswith(FORMULA_PREFIXES):
                return f"'{value}"
        return value

    @classmethod
    def sanitize_row(cls, row: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize all cell values in a tabular record dictionary."""
        return {k: cls.sanitize_cell_value(v) for k, v in row.items()}

    @classmethod
    def sanitize_dataset_records(cls, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sanitize a list of dictionary records before exporting to CSV or Excel."""
        return [cls.sanitize_row(row) for row in records]

    @classmethod
    def sanitize_export_filename(cls, filename: str, default_ext: str = ".csv") -> str:
        """Generate safe, injection-free export filename."""
        if not filename:
            filename = f"insightflow_export{default_ext}"
        
        # Clean filename characters
        safe = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", filename)
        if not safe.endswith(default_ext):
            safe = f"{safe}{default_ext}"
        return safe
