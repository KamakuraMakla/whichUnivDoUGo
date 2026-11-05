# coding: utf-8
import json
from pathlib import Path

import requests

#API_KEY 個人利用のためenv移動はなし
API_KEY = 'dee22c610bc2f119ac5e1debfd43316393722ee1'
BASE_URL = "https://api.e-stat.go.jp/rest/3.0/app/json/getDataCatalog"

#APIに渡すパラメータ
params = {
    'appId': API_KEY,
    'statsCode': '00400001',
    'searchWord': '出身高校の所在地県別',
    'dataType': 'XLS',
    'limit': 100,
    # 2回目
    #'startPosition': 101
}

# 実働部分
response = requests.get(BASE_URL, params=params, timeout=30)
response.raise_for_status()

json_string = response.json()

project_root = Path(__file__).resolve().parents[2]
output_path = project_root / 'data' / 'json' / 'catalog' / 'school_census_catalog.json'
output_path.parent.mkdir(parents=True, exist_ok=True)

with output_path.open('w', encoding='utf-8') as f:
    json.dump(json_string, f, ensure_ascii=False, indent=2)
    print("処理を完了しました。")
