"""Generate browser-ready static data from the analysis CSV.

The source CSV is read-only.  Every origin receives one compact JSON file so
the browser only loads the prefecture currently being explored.
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

YEARS = list(range(1975, 2026))
PREFECTURES = [
    "北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県",
    "茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県",
    "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県", "岐阜県",
    "静岡県", "愛知県", "三重県", "滋賀県", "京都府", "大阪府", "兵庫県",
    "奈良県", "和歌山県", "鳥取県", "島根県", "岡山県", "広島県", "山口県",
    "徳島県", "香川県", "愛媛県", "高知県", "福岡県", "佐賀県", "長崎県",
    "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県",
]
PREFECTURE_CODES = {prefecture: f"{index:02d}" for index, prefecture in enumerate(PREFECTURES, 1)}


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_records(csv_path: Path) -> dict[str, dict[int, dict[str, int]]]:
    records: dict[str, dict[int, dict[str, int]]] = defaultdict(lambda: defaultdict(dict))
    expected_keys = {
        (year, origin, destination)
        for year in YEARS
        for origin in PREFECTURES
        for destination in PREFECTURES
    }
    seen: set[tuple[int, str, str]] = set()
    with csv_path.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames != ["year", "origin", "destination", "students"]:
            raise ValueError(f"Unexpected CSV columns: {reader.fieldnames}")
        for row in reader:
            year = int(row["year"])
            origin = row["origin"]
            destination = row["destination"]
            students_text = row["students"].strip()
            if year not in YEARS or origin not in PREFECTURES or destination not in PREFECTURES:
                raise ValueError(f"Unexpected key: {year}, {origin}, {destination}")
            if not students_text:
                raise ValueError(f"Missing students value: {year}, {origin}, {destination}")
            key = (year, origin, destination)
            if key in seen:
                raise ValueError(f"Duplicate key: {key}")
            seen.add(key)
            students = int(students_text)
            if students < 0:
                raise ValueError(f"Negative students value: {key}")
            records[origin][year][destination] = students
    if seen != expected_keys:
        missing = sorted(expected_keys - seen)[:5]
        extra = sorted(seen - expected_keys)[:5]
        raise ValueError(f"CSV key set mismatch; missing={missing}, extra={extra}")
    return records


def validate_geojson(geojson_path: Path) -> None:
    data = json.loads(geojson_path.read_text(encoding="utf-8"))
    names = {feature.get("properties", {}).get("nam_ja") for feature in data.get("features", [])}
    if names != set(PREFECTURES):
        raise ValueError(f"GeoJSON does not contain exactly 47 prefectures: {len(names)}")


def main() -> None:
    root = project_root()
    csv_path = root / "data" / "processed" / "university_migration_od.csv"
    output_dir = root / "webapp" / "public" / "data"
    origins_dir = output_dir / "origins"
    output_dir.mkdir(parents=True, exist_ok=True)
    origins_dir.mkdir(parents=True, exist_ok=True)
    records = load_records(csv_path)
    validate_geojson(output_dir / "prefectures.geojson")

    region_definitions = {
        "kanto": ["茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県"],
        "kansai": ["滋賀県", "京都府", "大阪府", "兵庫県", "奈良県", "和歌山県"],
        "chukyo": ["岐阜県", "愛知県", "三重県"],
    }
    map_rates = []
    prefecture_trends = {}
    for origin in PREFECTURES:
        prefecture_trends[origin] = {}
        for year in YEARS:
            students = records[origin][year]
            total = sum(students.values())
            rates = {
                name: sum(students[destination] for destination in destinations) / total * 100
                for name, destinations in region_definitions.items()
            }
            rates["local"] = students[origin] / total * 100
            map_rates.append({"year": year, "origin": origin, **rates})
            prefecture_trends[origin][str(year)] = rates
    (output_dir / "map_rates.json").write_text(
        json.dumps(map_rates, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )
    (output_dir / "prefecture_trends.json").write_text(
        json.dumps(prefecture_trends, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )

    for origin in PREFECTURES:
        totals = {str(year): sum(records[origin][year].values()) for year in YEARS}
        payload = {
            "origin": origin,
            "originCode": PREFECTURE_CODES[origin],
            "years": {
                str(year): {
                    "students": records[origin][year],
                    "total": totals[str(year)],
                    "shares": {
                        destination: records[origin][year][destination] / totals[str(year)] * 100
                        for destination in PREFECTURES
                    },
                }
                for year in YEARS
            },
        }
        (origins_dir / f"{PREFECTURE_CODES[origin]}.json").write_text(
            json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )

    metadata = {
        "title": "都道府県進学先マップ",
        "years": YEARS,
        "prefectures": [
            {"code": PREFECTURE_CODES[name], "name": name} for name in PREFECTURES
        ],
        "metrics": ["students", "share"],
        "regions": {
            "関東": ["茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県"],
            "関西": ["滋賀県", "京都府", "大阪府", "兵庫県", "奈良県", "和歌山県"],
            "中京": ["岐阜県", "愛知県", "三重県"],
            "自県": ["出身県と進学先県が同一"],
        },
        "rateMetrics": {
            "kanto": "関東進学率",
            "kansai": "関西進学率",
            "chukyo": "中京進学率",
            "local": "地元進学率",
        },
        "source": "文部科学省「学校基本調査」1975～2025年度「出身高校の所在地県別入学者数」",
        "geojsonSource": "地球地図日本（GSI）を加工した dataofjapan/land の japan.geojson",
        "definition": "出身地は居住地ではなく、出身高校の所在地。対象はCSVに含まれる47都道府県への大学入学者です。",
        "recordCount": len(PREFECTURES) * len(PREFECTURES) * len(YEARS),
    }
    (output_dir / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Generated {len(PREFECTURES)} origin files and {metadata['recordCount']} validated records.")


if __name__ == "__main__":
    main()
