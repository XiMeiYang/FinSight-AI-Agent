"""Offline ResearchSnapshot to XLSX export adapter.

The workbook is authored by the bundled ``@oai/artifact-tool`` runtime.  This
module validates the input path, hands the JSON snapshot to a small JS builder,
and never fetches or invents data.
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import shutil
import uuid
from pathlib import Path
from typing import Any


class ExcelExportError(RuntimeError):
    """Raised when a snapshot cannot be exported safely."""


def _validate_snapshot(snapshot: dict[str, Any]) -> None:
    required = {"schema_version", "snapshot_id", "as_of", "security", "market_data", "sec_facts", "sec_filings", "sources", "data_quality", "run_record"}
    missing = sorted(required.difference(snapshot))
    if missing:
        raise ExcelExportError(f"snapshot missing required fields: {', '.join(missing)}")
    if snapshot.get("schema_version") != "1.1": raise ExcelExportError("schema_version must be 1.1")
    if snapshot.get("snapshot_type") != "single_stock_research": raise ExcelExportError("snapshot_type must be single_stock_research")
    if snapshot.get("data_mode") not in {"synthetic", "saved_snapshot"}: raise ExcelExportError("data_mode must be synthetic or saved_snapshot")
    for field in ("snapshot_id", "as_of"):
        if not isinstance(snapshot.get(field), str) or not snapshot[field].strip(): raise ExcelExportError(f"{field} must be non-empty text")
    if not isinstance(snapshot["security"], dict) or not isinstance(snapshot["security"].get("symbol"), str) or not snapshot["security"]["symbol"].strip():
        raise ExcelExportError("snapshot.security.symbol is required text")
    if not isinstance(snapshot["market_data"], dict): raise ExcelExportError("market_data must be an object")
    for field in ("sec_facts", "sec_filings", "sources"):
        if not isinstance(snapshot[field], list): raise ExcelExportError(f"{field} must be a list")
    for field in ("data_quality", "run_record"):
        if not isinstance(snapshot[field], dict): raise ExcelExportError(f"{field} must be an object")
    for row in snapshot["sec_facts"] + snapshot["sec_filings"] + snapshot["sources"]:
        if not isinstance(row, dict): raise ExcelExportError("snapshot list records must be objects")
    network_executed = snapshot["run_record"].get("network_executed")
    if type(network_executed) is not bool or network_executed is not False:
        raise ExcelExportError("export requires network_executed to be boolean false")


def _safe_local_path(path: Path, root: Path) -> None:
    if os.path.lexists(path) and path.is_symlink():
        raise ExcelExportError(f"symlink output path is not allowed: {path}")
    resolved_root = root.resolve()
    candidate = path.resolve(strict=False)
    if resolved_root not in candidate.parents:
        raise ExcelExportError(f"path must be inside {root}")
    current = root
    for part in candidate.relative_to(resolved_root).parts[:-1]:
        current = current / part
        if current.is_symlink():
            raise ExcelExportError(f"symlink path component is not allowed: {current}")


def _local_root(path: Path) -> Path:
    for parent in (path.resolve(strict=False), *path.resolve(strict=False).parents):
        if parent.name == ".local_data":
            return parent
    raise ExcelExportError("path must be inside a .local_data directory")


def export_snapshot_to_excel(snapshot: dict[str, Any], output_path: str | os.PathLike[str], *, node_bin: str | None = None, overwrite: bool = False) -> Path:
    """Export one validated ResearchSnapshot to ``output_path``.

    The caller owns the output location.  Existing files are overwritten only
    after the builder has produced a valid workbook at that exact path.
    """
    _validate_snapshot(snapshot)
    destination = Path(output_path).expanduser()
    local_root = _local_root(destination)
    if not destination.name.lower().endswith(".xlsx"):
        raise ExcelExportError("output must have .xlsx extension")
    _safe_local_path(destination, local_root)
    if os.path.lexists(destination) and not overwrite:
        raise ExcelExportError(f"output already exists (use overwrite=True): {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp_output = destination.with_name(f".{destination.name}.{uuid.uuid4().hex}.tmp.xlsx")
    root = Path(__file__).resolve().parents[2]
    builder = root / "scripts" / "build_research_excel.mjs"
    if not builder.exists():
        raise ExcelExportError(f"missing workbook builder: {builder}")
    bundled_node = node_bin or os.environ.get("FINSIGHT_NODE") or "/Users/chichenyang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node"
    with tempfile.TemporaryDirectory(prefix="finsight-export-") as temp_dir:
        input_path = Path(temp_dir) / "snapshot.json"
        input_path.write_text(json.dumps(snapshot, ensure_ascii=False), encoding="utf-8")
        # ESM resolves packages relative to the builder file.  Keep the
        # dependency directory untouched and expose it through a temporary
        # symlink as required by the spreadsheet runtime.
        temp_root = Path(temp_dir)
        temp_builder = temp_root / "build_research_excel.mjs"
        shutil.copy2(builder, temp_builder)
        (temp_root / "node_modules").symlink_to(Path(bundled_node).parent.parent / "node_modules", target_is_directory=True)
        proc = subprocess.run([bundled_node, str(temp_builder), str(input_path), str(temp_output)], cwd=temp_root, text=True, capture_output=True)
        if proc.returncode:
            detail = (proc.stderr or proc.stdout).strip()
            raise ExcelExportError(f"artifact-tool export failed: {detail}")
    if not temp_output.is_file() or temp_output.stat().st_size == 0:
        raise ExcelExportError("artifact-tool reported success but no workbook was written")
    os.replace(temp_output, destination)
    return destination


def export_snapshot_file(snapshot_path: str | os.PathLike[str], output_path: str | os.PathLike[str], **kwargs: Any) -> Path:
    path = Path(snapshot_path)
    local_root = _local_root(path)
    _safe_local_path(path, local_root)
    if path.is_symlink():
        raise ExcelExportError("snapshot symlink is not allowed")
    try:
        snapshot = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ExcelExportError(f"cannot read snapshot JSON: {path}") from exc
    if not isinstance(snapshot, dict):
        raise ExcelExportError("snapshot JSON must contain an object")
    return export_snapshot_to_excel(snapshot, output_path, **kwargs)
