"""Safe, repository-local JSON/binary snapshot input loader."""
from __future__ import annotations
import hashlib, json
from pathlib import Path

class LocalDataError(ValueError):
    pass

MAX_BYTES = 80 * 1024 * 1024

def _root(root: Path) -> Path:
    return root.resolve()

def load_json(path: str | Path, *, data_root: str | Path) -> tuple[object, dict[str, object]]:
    root = _root(Path(data_root)); candidate = Path(path)
    if not candidate.is_absolute():
        # Accept both paths relative to .local_data and repository-relative
        # paths such as ``.local_data/market/raw/file.json``.
        candidate = (root.parent / candidate) if candidate.parts and candidate.parts[0] == root.name else (root / candidate)
    try: resolved = candidate.resolve(strict=True)
    except (FileNotFoundError, OSError) as exc: raise LocalDataError("input file is unavailable") from exc
    if root not in resolved.parents or resolved == root: raise LocalDataError("input path must be inside .local_data")
    try:
        rel_parts = resolved.relative_to(root).parts
        cur = root
        if any((cur := cur / part).is_symlink() for part in rel_parts):
            raise LocalDataError("symbolic links are not allowed")
    except ValueError as exc: raise LocalDataError("input path must be inside .local_data") from exc
    if not resolved.is_file(): raise LocalDataError("input must be a regular file")
    size = resolved.stat().st_size
    if size > MAX_BYTES: raise LocalDataError("input file exceeds size limit")
    try: raw = resolved.read_bytes(); value = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc: raise LocalDataError("input is not valid UTF-8 JSON") from exc
    rel = resolved.relative_to(root).as_posix()
    return value, {"input_file": rel, "sha256": hashlib.sha256(raw).hexdigest(), "size": size}

def atomic_write_json(path: str | Path, value: object, *, data_root: str | Path, overwrite: bool = False) -> tuple[str, str]:
    root = _root(Path(data_root)); candidate = Path(path)
    if not candidate.is_absolute():
        candidate = (root.parent / candidate) if candidate.parts and candidate.parts[0] == root.name else (root / candidate)
    import os
    if os.path.lexists(candidate) and candidate.is_symlink():
        raise LocalDataError("symbolic links are not allowed")
    resolved = candidate.resolve()
    if root not in resolved.parents or resolved == root: raise LocalDataError("output path must be inside .local_data")
    cur = root
    for part in resolved.relative_to(root).parts[:-1]:
        cur = cur / part
        if cur.is_symlink(): raise LocalDataError("symbolic links are not allowed")
    if resolved.is_symlink(): raise LocalDataError("symbolic links are not allowed")
    if resolved.exists() and not overwrite: raise LocalDataError("output already exists; use --overwrite")
    resolved.parent.mkdir(parents=True, exist_ok=True)
    import os, tempfile
    data = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    fd, temp = tempfile.mkstemp(prefix=".snapshot-", dir=str(resolved.parent))
    try:
        with os.fdopen(fd, "wb") as handle: handle.write(data); handle.flush(); os.fsync(handle.fileno())
        os.replace(temp, resolved)
    finally:
        if os.path.exists(temp): os.unlink(temp)
    return resolved.relative_to(root).as_posix(), hashlib.sha256(data).hexdigest()
