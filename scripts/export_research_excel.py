#!/usr/bin/env python3
"""CLI for exporting an existing offline ResearchSnapshot JSON to XLSX."""
import argparse
import sys

from finsight_research.excel_exporter import ExcelExportError, export_snapshot_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Export an offline ResearchSnapshot JSON to Excel")
    parser.add_argument("snapshot", help="path to a saved ResearchSnapshot JSON")
    parser.add_argument("--output", required=True, help="destination .xlsx path")
    parser.add_argument("--overwrite", action="store_true", help="replace an existing output file")
    args = parser.parse_args()
    try:
        print(export_snapshot_file(args.snapshot, args.output, overwrite=args.overwrite))
    except ExcelExportError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
