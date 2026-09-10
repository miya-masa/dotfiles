# Confluence 実務メモ

`writing-report` の成果物を Confluence へ載せるときだけ参照する。

## Confluence の実務メモ

本文は MCP `updateConfluencePage` に `contentFormat: "html"` で**全文**を渡す（部分更新は無い）。

| 要素 | 書き方 |
|---|---|
| 表 | `<table data-layout="default">`。**`data-width` を付けない**（付けると横に広がってスクロールが出る） |
| 図 | `<figure data-type="media-single" data-layout="center" data-width="760" data-width-type="pixel">` + `<div data-type="media" data-media-type="file" data-id="<既存のID>" data-collection="contentId-<pageId>" data-width="760" data-height="<比率で計算>">` |
| パネル | `<div data-type="panel-info\|panel-warning\|panel-note"><p>…</p></div>` |
| セル内改行 | `<br />`（`<p>` を並べると行間が空く） |
| 多段ヘッダーの表 | Markdown では作れない。2 段目がただのデータ行になって崩れる。**表を分割する** |
| ローカル画像 | `![](相対パス.png)` を Confluence アップロード CLI の `update` に通すと、添付 + `ac:image` になる。パスは md ファイルからの相対 |

- **図の `data-id` は既存 HTML からコピーする。** 新規添付は Confluence アップロード CLI の `attach` サブコマンドで上げてから ID を拾う
- **他ページの添付を参照する media を入れると、エラーを返さないまま body が反映されない。** `data-collection` は必ず自ページの `contentId`
- `colspan` は `<td>` にしか付けられない。`<p colspan>` は 400
- 反映確認は `getConfluencePage` の `contentFormat: "markdown"`（HTML より短い）
- **新規作成したページは本文幅が `max`（最大）になる。** MCP からは変えられないので REST v2 の page property `content-appearance-published` / `-draft` を書き換える。値は `default`（標準）/ `full-width`（広い）/ `max`（最大）の 3 つ。**`wide` のような無効値を入れても API はエラーを返さず、黙って `default` にフォールバックする**ので、値は上の 3 つから選ぶこと

```sh
# 現在値
curl -s -u "$EMAIL:$TOKEN" ".../wiki/api/v2/pages/<id>/properties?limit=25"
# content-appearance-published と -draft の両方を PUT する
# body: {"key":"content-appearance-published","value":"full-width","version":{"number":<現在+1>}}
```

- **「コンパクト表示」は API から設定できない。** page property にも本文 ADF にも保存されず、GraphQL の `commitUpdateContentModeMutation` で別管理されている。設定するには編集モードに入り、タイトル上のツールバー右側にある **`A↓`（コンパクト表示を使用）** を押して公開する。ページを量産したときは、この操作だけブラウザで繰り返すことになる

- **mermaid / drawio マクロを含むページは MCP で編集しない**（マクロが壊れる）。Confluence アップロード CLI の export → 編集 → update を使う。逆に**表を含むページで CLI round-trip を使うと表が壊れる**ので、表中心の報告ページは MCP 全文 HTML で更新する

### 表と図の幅が本文幅に合わないとき

ページ幅を `full-width` にしても、表と図には**個別の幅指定が残っている**。これを消さないと本文幅に追随しない。

| 症状 | ADF 上の原因 | 直し方 |
|---|---|---|
| 表が画面いっぱいに広がる | table に `breakout` mark（`mode: wide` / `full-width`） | mark を削除する |
| 表が本文幅より狭い / 極端に広い | table の `attrs.width`（`760` や `4000` が入っている） | `attrs` から `width` を消し、`layout: "default"` だけ残す |
| 図が本文幅より狭い | mediaSingle の `width` が小さい | 元画像の原寸を `widthType: "pixel"` で指定する |

- **mediaSingle に percentage は使えない。** `{width: 100, widthType: "percentage"}` で PUT しても、Confluence が保存時に標準幅基準の pixel（`680`）へ正規化する。指定前より狭くなる
- pixel 指定は**本文幅を超えると自動で縮む**ので、原寸を入れておけば幅設定によらず本文幅いっぱいに出る。原寸が小さい画像だけ狭く残るため、揃えたいなら他と同じ pixel 値を指定して拡大する
- `mediaSingle.width` を変えるとき `media` の `width` / `height` は触らなくてよい（アスペクト比の計算にしか使われない）

### 属性だけ直すときは ADF を直接 PUT する

幅のような属性の一括修正は、HTML+ を組み直すより REST v2 の ADF PUT が安全。本文に一切触れずに済む。

```sh
B=https://<site>/wiki/api/v2
curl -s -u "$EMAIL:$TOKEN" "$B/pages/$ID?body-format=atlas_doc_format" > page.json
jq -r '.body.atlas_doc_format.value' page.json | jq -c '<attrs を書き換える jq>' > adf.json
# PUT $B/pages/$ID
# body: {id, status:"current", title, spaceId,
#        body:{representation:"atlas_doc_format", value:"<adf.json の中身>"},
#        version:{number:<現在+1>}}
```

反映後は同じ GET で属性を読み直して確認する。Confluence は無効・非対応の値を**エラーにせず正規化する**ので、PUT が 200 でも意図どおりとは限らない

## インラインコメントへの対応

`getConfluencePageInlineComments`（`resolutionStatus: "open"`）で読む。反映しても Confluence 側はアンカーを即座に再評価しないため、`dangling` には落ちない。**解決済みにするのはユーザーの操作**なので、こちらで消そうとしない。反映確認は本文を markdown で取り直して読む。
