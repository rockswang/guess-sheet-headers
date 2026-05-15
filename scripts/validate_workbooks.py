from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from python_calamine import load_workbook

from guess_sheet_headers import do_guess


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate guess-sheet-headers against local Excel workbooks.")
    parser.add_argument("files", nargs="+", help="Workbook paths to inspect.")
    parser.add_argument("--preview", type=int, default=6, help="Rows to print per sheet.")
    args = parser.parse_args()

    for file in args.files:
        path = Path(file)
        print(f"\n## {path}")
        if not path.exists():
            print("MISSING")
            continue
        try:
            wb = load_workbook(path)
        except Exception as exc:  # noqa: BLE001
            print(f"LOAD_ERROR {type(exc).__name__}: {exc}")
            continue

        for name in wb.sheet_names:
            try:
                sheet = wb.get_sheet_by_name(name)
                rows = sheet.to_python()
                rng = do_guess(rows)
                print(f"\n### {name} rows={len(rows)} header={rng}")
                for i, row in enumerate(rows[: args.preview]):
                    print(f"{i}: {_fmt_row(row)}")
            except Exception as exc:  # noqa: BLE001
                print(f"\n### {name} ERROR {type(exc).__name__}: {exc}")
    return 0


def _fmt_row(row: list[Any], limit: int = 12) -> str:
    cells = [_fmt_cell(v) for v in row[:limit]]
    if len(row) > limit:
        cells.append("...")
    return " | ".join(cells)


def _fmt_cell(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).replace("\r", " ").replace("\n", " ").strip()
    return text if len(text) <= 40 else text[:37] + "..."


if __name__ == "__main__":
    raise SystemExit(main())
