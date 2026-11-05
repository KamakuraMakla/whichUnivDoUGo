"""Build university migration OD data from School Census workbooks.

The source workbooks are intentionally treated as read-only.  Layout detection
is based on table shape and numeric cells because older files use different
labels and some downloaded workbooks contain mojibake in text cells.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any

import pandas as pd


YEARS = range(1975, 2026)
PREFECTURES = [
    "北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県",
    "茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県",
    "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県", "岐阜県",
    "静岡県", "愛知県", "三重県", "滋賀県", "京都府", "大阪府", "兵庫県",
    "奈良県", "和歌山県", "鳥取県", "島根県", "岡山県", "広島県", "山口県",
    "徳島県", "香川県", "愛媛県", "高知県", "福岡県", "佐賀県", "長崎県",
    "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県",
]
MISSING_VALUES = {"", "-", "－", "―", "…", "...", "NA", "N/A"}


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def workbook_for_year(raw_dir: Path, year: int) -> Path:
    matches = sorted(raw_dir.glob(f"{year}.xls*"))
    if len(matches) != 1:
        raise FileNotFoundError(
            f"{year}: expected exactly one workbook in {raw_dir}, found {len(matches)}"
        )
    return matches[0]


def numeric_columns(row: pd.Series) -> list[int]:
    columns: list[int] = []
    for column, value in row.items():
        if isinstance(value, bool):
            continue
        if isinstance(value, (int, float)) and not pd.isna(value):
            columns.append(int(column))
    return columns


def locate_table(df: pd.DataFrame) -> tuple[int, int, list[int]]:
    """Return total row, destination column, and numeric value columns."""
    for row_index in range(len(df)):
        columns = numeric_columns(df.iloc[row_index])
        if len(columns) < 10:
            continue
        data_row = df.iloc[row_index + 1] if row_index + 1 < len(df) else None
        if data_row is None:
            continue
        data_columns = numeric_columns(data_row)
        if len(data_columns) < 10:
            continue
        destination_columns = [
            int(column)
            for column, value in data_row.items()
            if pd.notna(value) and int(column) not in data_columns
        ]
        if not destination_columns:
            raise ValueError(f"Could not locate destination column in row {row_index + 1}")
        return row_index, destination_columns[0], data_columns
    raise ValueError("Could not locate a numeric OD table")


def parse_student_count(value: Any) -> int:
    if pd.isna(value):
        return 0
    if isinstance(value, str):
        value = value.strip().replace(",", "")
        if value in MISSING_VALUES:
            return 0
    number = float(value)
    if not math.isfinite(number) or not number.is_integer():
        raise ValueError(f"Student count is not an integer: {value!r}")
    return int(number)


def extract_year(year: int, workbook: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    excel = pd.ExcelFile(workbook)
    records: list[dict[str, Any]] = []
    selected_sheets: list[dict[str, Any]] = []
    origin_index = 0

    for sheet_number, sheet_name in enumerate(excel.sheet_names):
        frame = pd.read_excel(excel, sheet_name=sheet_name, header=None)
        total_row, destination_column, value_columns = locate_table(frame)
        if sheet_number == 0:
            value_columns = value_columns[1:]  # remove the national total column

        remaining = len(PREFECTURES) - origin_index
        selected_columns = value_columns[:remaining]
        if not selected_columns:
            break
        data_start = total_row + 1
        data_end = data_start + len(PREFECTURES)
        if data_end > len(frame):
            raise ValueError(f"{year}/{sheet_name}: fewer than 47 destination rows")

        selected_sheets.append(
            {
                "sheet": sheet_name,
                "shape": [int(frame.shape[0]), int(frame.shape[1])],
                "total_row": total_row,
                "data_start_row": data_start,
                "destination_column": destination_column,
                "value_columns": selected_columns,
                "origins": PREFECTURES[origin_index : origin_index + len(selected_columns)],
            }
        )

        for destination_offset, destination in enumerate(PREFECTURES):
            row = frame.iloc[data_start + destination_offset]
            for origin, column in zip(
                PREFECTURES[origin_index : origin_index + len(selected_columns)],
                selected_columns,
            ):
                records.append(
                    {
                        "year": year,
                        "origin": origin,
                        "destination": destination,
                        "students": parse_student_count(row.iloc[column]),
                    }
                )
        origin_index += len(selected_columns)
        if origin_index == len(PREFECTURES):
            break

    if origin_index != len(PREFECTURES):
        raise ValueError(f"{year}: recovered {origin_index}/47 origin prefectures")
    if len(records) != 47 * 47:
        raise ValueError(f"{year}: recovered {len(records)} cells instead of 2209")
    return records, {
        "year": year,
        "workbook": workbook.name,
        "sheet_count": len(excel.sheet_names),
        "sheet_names": excel.sheet_names,
        "selected_sheets": selected_sheets,
        "recovered_cells": len(records),
        "layout_group": "single-sheet-47-columns"
        if len(selected_sheets) == 1
        else "multi-sheet-column-split",
    }


def inspect_all(raw_dir: Path, report_path: Path) -> list[dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    for year in YEARS:
        workbook = workbook_for_year(raw_dir, year)
        excel = pd.ExcelFile(workbook)
        sheets: list[dict[str, Any]] = []
        for sheet_name in excel.sheet_names:
            frame = pd.read_excel(excel, sheet_name=sheet_name, header=None)
            total_row, destination_column, value_columns = locate_table(frame)
            sheets.append(
                {
                    "sheet": sheet_name,
                    "rows": int(frame.shape[0]),
                    "columns": int(frame.shape[1]),
                    "total_row": total_row,
                    "data_start_row": total_row + 1,
                    "destination_column": destination_column,
                    "numeric_columns": value_columns,
                }
            )
        reports.append(
            {
                "year": year,
                "workbook": workbook.name,
                "sheet_count": len(excel.sheet_names),
                "sheets": sheets,
            }
        )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(reports, ensure_ascii=False, indent=2), encoding="utf-8")
    return reports


def build_od(raw_dir: Path, output_path: Path, report_path: Path | None) -> None:
    all_records: list[dict[str, Any]] = []
    reports: list[dict[str, Any]] = []
    for year in YEARS:
        records, report = extract_year(year, workbook_for_year(raw_dir, year))
        all_records.extend(records)
        reports.append(report)

    result = pd.DataFrame(all_records, columns=["year", "origin", "destination", "students"])
    expected = len(YEARS) * 47 * 47
    if len(result) != expected:
        raise ValueError(f"Expected {expected} rows, got {len(result)}")
    if result[["year", "origin", "destination"]].duplicated().any():
        raise ValueError("Duplicate year/origin/destination keys detected")
    if result["students"].isna().any():
        raise ValueError("Missing student counts remain in the output")
    result["year"] = result["year"].astype("int64")
    result["students"] = result["students"].astype("int64")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_path, index=False, encoding="utf-8")
    if report_path is not None:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(reports, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["inspect", "build"])
    parser.add_argument("--raw-dir", type=Path, default=project_root() / "data/raw/school_census")
    parser.add_argument(
        "--report",
        type=Path,
        default=project_root() / "data/processed/school_census_structure.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=project_root() / "data/processed/university_migration_od.csv",
    )
    args = parser.parse_args()
    if args.command == "inspect":
        inspect_all(args.raw_dir, args.report)
    else:
        build_od(args.raw_dir, args.output, args.report)


if __name__ == "__main__":
    main()
