"""Offline research snapshot contract."""
from .snapshot import build_research_snapshot, SnapshotError, SnapshotConflictError
try:
    from .excel_exporter import ExcelExportError, export_snapshot_file, export_snapshot_to_excel
except ModuleNotFoundError as exc:
    if exc.name != "openpyxl":
        raise
    ExcelExportError = None
    export_snapshot_file = None
    export_snapshot_to_excel = None
__all__ = ["build_research_snapshot", "SnapshotError", "SnapshotConflictError", "ExcelExportError", "export_snapshot_file", "export_snapshot_to_excel"]
