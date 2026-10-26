# 都道府県進学先マップ

1975～2025年の「出身高校の所在地県別入学者数」を、出身県・年度・指標から探索する完全静的なWebアプリです。分析用のNotebookや元データとは分離して、`webapp/` 以下だけで配信できる構成にしています。

## 技術構成

- Vue 3 + Composition API
- TypeScript + Vite
- Leaflet（都道府県境界の表示）
- Plotly.js（51年間の推移）
- Python標準ライブラリ（CSVから静的JSONを生成）

## ディレクトリ

```text
webapp/
  public/data/
    map_rates.json       # 51年×47出身県の4進学率
    prefecture_trends.json # 出身県ごとの4系列・51年推移
    metadata.json
    prefectures.geojson
  scripts/generate_static_data.py
  src/
    components/
    lib/
    types/
  package.json
```

## セットアップと実行

```powershell
cd webapp
npm install
npm run dev
```

ブラウザで表示されたURLを開いてください。バックエンドやAPIサーバーは不要です。

## データ生成

元CSVを読み取り、既存ファイルを上書きせずに検証済みJSONを生成します。地図とグラフは同じ集計処理から生成されます。

```powershell
cd webapp
npm run generate-data
```

入力はプロジェクトルートの `data/processed/university_migration_od.csv` です。生成処理は以下を検証します。

- 1975～2025年の51年度
- 47都道府県×47都道府県×51年の112,659キー
- 年度・出身県・進学先の重複
- 欠損・負数
- GeoJSONの47都道府県
- 51年×47出身都道府県の2,397組
- 関東・関西・中京・地元の各進学率が0～100%

## 本番ビルド

```powershell
cd webapp
npm run build
npm run preview
```

`base: './'` を設定しているため、`dist/` をGitHub Pagesなどの静的ホスティングへ配置できます。`dist/index.html`を直接ダブルクリックせず、`npm run dev`または静的ファイルサーバー経由で開いてください。

## GitHub Pagesへの公開

リポジトリ直下の `.github/workflows/deploy-pages.yml` が、`webapp/` の変更時に自動で以下を実行します。

1. `webapp` で `npm ci`
2. `webapp` で `npm run build`
3. `webapp/dist` だけをGitHub Pagesへアップロード

初回だけGitHubリポジトリの設定を変更します。

1. このプロジェクトをGitHubリポジトリの `main` ブランチへpushする
2. リポジトリの **Settings → Pages** を開く
3. **Build and deployment → Source** を **GitHub Actions** に変更する
4. `main` ブランチへpushするか、Actions画面から **Deploy webapp to GitHub Pages** を手動実行する
5. Actionsが完了したら、Pages画面に表示されたURLを開く

プロジェクトサイトのURLは通常、次の形式です。

```text
https://<GitHubユーザー名>.github.io/<リポジトリ名>/
```

この設定では分析用Notebook、元Excel、元CSVはPagesへアップロードされません。公開対象はビルド後の `webapp/dist` のみです。

## 指標の定義

- **進学者数**：同じ出身高校所在地から、各進学先都道府県の大学へ入学した人数（人）。
- **進学割合**：特定の進学先への入学者数 ÷ 同じ出身高校所在地の47都道府県向け大学入学者総数 × 100。
- 出身地は居住地ではなく、出身高校の所在地です。
- 大学入学者には浪人生なども含まれます。
- 県外進学は、必ずしも転居や下宿を意味しません。
- 「関東」「関西」「中京」「自県」は構成都道府県を合計する集計区分であり、全国を排他的に分類するものではありません。

## 出典・利用条件

統計データ：文部科学省「学校基本調査」1975～2025年度「出身高校の所在地県別入学者数」。

地図：`dataofjapan/land` の `japan.geojson`。同リポジトリのREADMEに記載された通り、地球地図日本（国土地理院）のデータに基づきます。非営利利用では出典元（地球地図日本）の明記、営利利用では明記に加えて著作権者への利用報告が求められるため、アプリ画面にも出典を表示しています。

## MVPで扱わないもの

鉄道路線、所要時間、大学定員、18歳人口・進学率、任意年度比較、ストーリーモード、進学先からの逆引きは今後の拡張候補です。
