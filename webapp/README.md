# 都道府県進学先マップ

文部科学省「学校基本調査」のデータを使い、1975年から2025年までの大学進学先の変化を、出身高校所在地別に探索する完全静的なWebアプリです。

出身高校所在地の都道府県を地図上の単位とし、各県の高校出身者が関東・関西・中京・自県の大学へ進学した割合を、年度ごとに比較できます。地図上の都道府県をクリックすると、その県の4指標について51年間の推移を表示します。

## デモ

GitHub Pagesで公開する場合のURLは、通常次の形式です。

```text
https://<GitHubユーザー名>.github.io/<リポジトリ名>/
```

ローカルでの確認方法は、[ローカル実行](#ローカル実行)を参照してください。

## 主な機能

- 1975～2025年を1年刻みで操作できる年度スライダー
- 年度の自動再生・一時停止・再生速度変更
- 全国47都道府県のコロプレス地図
- 出身高校所在地を単位にした進学率の色分け
- 次の4指標の切り替え
  - 関東進学率
  - 関西進学率
  - 中京進学率
  - 地元進学率
- 地図上のホバーによる県名・値の確認
- 地図上のクリックによる県別詳細表示
- 選択県の4指標を比較する51年間のPlotly折れ線グラフ
- 選択年度のグラフ上マーカー・縦線表示
- 地図・グラフのレスポンシブ対応
- バックエンド、APIサーバー、データベース不要

## 使用技術

- Vue 3
- Composition API
- TypeScript
- Vite
- Leaflet
- Plotly.js
- Python標準ライブラリによる静的データ生成

## ディレクトリ構成

```text
whichUnivDoUGo/
├─ .github/
│  └─ workflows/
│     └─ deploy-pages.yml       # GitHub Pages自動デプロイ
├─ data/
│  └─ processed/
│     └─ university_migration_od.csv
├─ notebook/                    # 分析用Notebook。Webアプリとは別管理
├─ scripts/                     # 元データの前処理
└─ webapp/
   ├─ public/
   │  ├─ data/
   │  │  ├─ map_rates.json
   │  │  ├─ prefecture_trends.json
   │  │  ├─ metadata.json
   │  │  ├─ prefectures.geojson
   │  │  └─ origins/            # 旧形式の出身県別データ
   │  └─ japan-wordmark-bg.svg
   ├─ scripts/
   │  └─ generate_static_data.py
   ├─ src/
   │  ├─ components/
   │  │  ├─ JapanMap.vue
   │  │  └─ MigrationChart.vue
   │  ├─ lib/
   │  │  └─ data.ts
   │  ├─ types/
   │  │  └─ migration.ts
   │  ├─ App.vue
   │  ├─ main.ts
   │  └─ style.css
   ├─ index.html
   ├─ package.json
   ├─ vite.config.ts
   └─ README.md
```

## 必要な環境

- Node.js 20以上（GitHub Actionsでは22を使用）
- npm
- Python 3.10以上

Pythonは静的JSONを再生成する場合だけ必要です。生成済みのJSONを使って画面を起動するだけなら、Node.jsとnpmがあれば実行できます。

## ローカル実行

PowerShellでプロジェクトの`webapp`へ移動します。

```powershell
cd "C:\Users\<ユーザー名>\Documents\desktop\Codes\Statistics\whichUnivDoUGo\webapp"
npm install
npm run dev
```

表示されたURLをブラウザで開きます。通常は次のURLです。

```text
http://localhost:5173/
```

スマートフォンや同じネットワーク上の別PCから確認する場合は、次のように起動します。

```powershell
npm run dev -- --host 0.0.0.0
```

そのPCのローカルIPアドレスを使ってアクセスします。

```text
http://<PCのIPアドレス>:5173/
```

### 注意：HTMLの直接起動は不可

次のように`dist/index.html`をダブルクリックして開くと、ブラウザの`file://`制限でJSONを読み込めない場合があります。

```text
file:///.../webapp/dist/index.html
```

必ず`npm run dev`または`npm run preview`を使ってください。

## 静的データの生成

入力ファイルは次のCSVです。

```text
data/processed/university_migration_od.csv
```

元CSVは変更・上書きしません。プロジェクトルートから次を実行します。

```powershell
cd webapp
npm run generate-data
```

内部では`webapp/scripts/generate_static_data.py`がCSVを読み込み、次のファイルを生成します。

| ファイル | 用途 |
|---|---|
| `public/data/map_rates.json` | 年度ごとの全国47都道府県の地図表示 |
| `public/data/prefecture_trends.json` | 県ごとの4指標・51年間のグラフ |
| `public/data/metadata.json` | 年度、都道府県、指標、出典などのメタデータ |

地図とグラフは同じ集計処理から生成されるため、別々のロジックによる数値のずれを避けています。

## データ検証

生成処理では、次の条件を検証します。

- 1975～2025年の51年度
- 47都道府県×47都道府県×51年の112,659キー
- 年度・出身県・進学先の重複がないこと
- 年度、出身県、進学先が想定値であること
- 学生数が欠損していないこと
- 学生数が負数でないこと
- GeoJSONに47都道府県が含まれること
- 51年×47出身都道府県の2,397組
- 4指標が0～100%の範囲にあること

既知の基準値は次の通りです。

| 年度 | 出身高校所在地 | 大学所在地 | 人数 |
|---:|---|---|---:|
| 1975 | 北海道 | 北海道 | 9,086 |
| 2025 | 北海道 | 北海道 | 14,256 |

## 指標の定義

分母は、同じ出身高校所在地から、元CSVに存在する47都道府県の大学へ進学した人数の合計です。

### 関東進学率

```text
関東7都県への入学者数 ÷ 大学入学者総数 × 100
```

対象は茨城、栃木、群馬、埼玉、千葉、東京、神奈川です。

### 関西進学率

```text
関西6府県への入学者数 ÷ 大学入学者総数 × 100
```

対象は滋賀、京都、大阪、兵庫、奈良、和歌山です。

### 中京進学率

```text
愛知・岐阜・三重への入学者数 ÷ 大学入学者総数 × 100
```

### 地元進学率

```text
出身高校所在地と同じ都道府県への入学者数 ÷ 大学入学者総数 × 100
```

4指標は重複します。たとえば地元進学率は、関東・関西・中京の地域進学率に含まれる場合があります。そのため、4指標を足して100%になるものではなく、積み上げグラフとして解釈しません。

## データの解釈上の注意

- 出身地は居住地ではなく、出身高校の所在地です。
- 大学入学者には浪人生なども含まれます。
- 県外進学は、必ずしも転居や下宿を意味しません。
- 進学先の分布は、本人の希望だけで決まるものではありません。
- 地域別進学率の変化だけから、交通政策や大学政策の因果効果は判断できません。
- CSVに含まれない「その他」などの分類は、分母に含まれません。

## 地図データの出典

統計データの出典は、文部科学省「学校基本調査」1975～2025年度「出身高校の所在地県別入学者数」です。

都道府県境界には、`dataofjapan/land`で公開されている`japan.geojson`を使用しています。このデータは地球地図日本（国土地理院）のShapefileを変換したものです。利用時は元データのREADMEに記載された条件を確認し、出典元を明記してください。

## 本番ビルド

```powershell
cd webapp
npm run build
npm run preview
```

ビルド成果物は`webapp/dist/`に出力されます。Viteは相対ベースパスを使用しているため、リポジトリ名を含むGitHub Pagesのプロジェクトサイトでも動作します。

## GitHub Pagesへの公開

リポジトリ直下の`.github/workflows/deploy-pages.yml`が、`webapp/`の変更を検知して自動デプロイします。

Workflowの処理は次の通りです。

1. リポジトリをcheckout
2. Node.js 22をセットアップ
3. `webapp`で`npm ci`
4. `webapp`で`npm run build`
5. `webapp/dist`だけをPagesアーティファクトとしてアップロード
6. GitHub Pagesへデプロイ

初回だけ、GitHubリポジトリで次を設定します。

1. **Settings → Pages**を開く
2. **Build and deployment → Source**を**GitHub Actions**に変更
3. `main`へpushする、またはActions画面からWorkflowを手動実行
4. Workflow完了後、Pages画面に表示されたURLを開く

この構成では、分析用Notebook、元Excel、元CSVはPagesの公開成果物に含まれません。Pagesへアップロードされるのはビルド後の`webapp/dist`だけです。

## GitHub Pagesの更新

アプリを修正したら、プロジェクトルートで次を実行します。

```powershell
git add webapp .github
git commit -m "Update web app"
git push origin main
```

`webapp/`またはPages Workflowに変更があるpushで、自動デプロイが開始します。

## トラブルシューティング

### `npm run dev`で起動できない

`package.json`がある`webapp`ディレクトリで実行しているか確認します。

```powershell
cd webapp
npm install
npm run dev
```

### 画面が読み込み中のままになる

- `file://`で開いていないか確認する
- 開発サーバーが起動しているか確認する
- ブラウザの開発者ツールで`metadata.json`、`map_rates.json`、`prefecture_trends.json`のHTTPエラーを確認する
- GitHub PagesではActionsのビルドログを確認する

### 変更がブラウザに反映されない

強制再読み込みを実行します。

```text
Ctrl + F5
```

### GitHub Pagesで404になる

- **Settings → Pages → Source**がGitHub Actionsになっているか確認する
- Actionsのデプロイが成功しているか確認する
- URL末尾のリポジトリ名と`/`を確認する

## 今後の拡張候補

MVPでは次の機能を実装していません。

- 鉄道路線・新幹線開業年の表示
- 都道府県間の鉄道所要時間
- 大学の学部・入学定員
- 18歳人口・大学進学率との比較
- 任意の2年度間の比較
- ストーリーモード
- 進学先から出身県を逆引きする機能
