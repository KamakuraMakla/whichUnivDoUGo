# coding: utf-8
import json
import csv
import hashlib
import time
from pathlib import Path

import requests

# パス設定
project_root = Path(__file__).resolve().parents[2]

catalog_dir = project_root / "data" / "json" / "catalog"
output_dir = project_root / "data" / "raw" / "school_census"
output_dir.mkdir(parents=True, exist_ok=True)

# 取得済みのカタログJSON
catalog_files = [
    catalog_dir / "school_census_catalog.json",
    catalog_dir / "school_census_catalog2.json"
]

# 1. JSONの読み込み・結合
records = []

for file in catalog_files:
    with file.open("r", encoding="utf-8") as f:
        data = json.load(f)

    items = data["GET_DATA_CATALOG"]["DATA_CATALOG_LIST_INF"]["DATA_CATALOG_INF"]
    records.extend(items)

print(f"カタログ取得件数: {len(records)}")

# 2. 大学・大学院の1975～2025年を抽出
targets = {}

for record in records:
    title = record["DATASET"]["TITLE"]
    year = int(title["SURVEY_DATE"])
    category = title["TABULATION_SUB_CATEGORY4"]

    if not (1975 <= year <= 2025):
        continue
    if "大学・大学院" not in category:
        continue

    if year in targets:
        raise ValueError(f"{year}年のデータが重複しています")

    targets[year] = record["RESOURCES"]["RESOURCE"]["URL"]

# 年度の欠損チェック
expected = set(range(1975, 2026))
assert set(targets) == expected, (
    f"不足年度: {sorted(expected - set(targets))}"
)

print(f"ダウンロード対象: {len(targets)}件")

# 3. Excelファイルのダウンロード
manifest = []

with requests.Session() as session:
    for year, url in sorted(targets.items()):

        # 再実行時はダウンロード済みのファイルを利用
        existing = [
            p for p in (
                output_dir / f"{year}.xls",
                output_dir / f"{year}.xlsx"
            ) if p.exists()
        ]

        if existing:
            path = existing[0]
            content = path.read_bytes()
            print(f"{year}: スキップ（取得済み）")
        else:
            response = session.get(url, timeout=60)
            response.raise_for_status()
            content = response.content

            # ファイル形式の確認
            if content.startswith(b"\xD0\xCF\x11\xE0"):
                ext = ".xls"
            elif content.startswith(b"PK\x03\x04"):
                ext = ".xlsx"
            else:
                raise ValueError(
                    f"{year}: Excel形式ではありません。"
                    "ダウンロード結果を確認してください。"
                )

            path = output_dir / f"{year}{ext}"
            path.write_bytes(content)

            print(f"{year}: 保存完了 ({len(content):,} bytes)")
            time.sleep(0.5)

        # 出典とハッシュ値を記録
        manifest.append({
            "year": year,
            "filename": path.name,
            "source_url": url,
            "sha256": hashlib.sha256(content).hexdigest()
        })

# 4. 出典情報をCSVとして保存
manifest_path = output_dir / "manifest.csv"

with manifest_path.open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=["year", "filename", "source_url", "sha256"]
    )
    writer.writeheader()
    writer.writerows(manifest)

print(f"\n完了: {len(manifest)}年分")
