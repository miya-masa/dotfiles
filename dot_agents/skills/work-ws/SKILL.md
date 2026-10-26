---
name: work-ws
description: main セッション専用の作業用 herdr workspace（上に Neovim、下に手作業用の shell）を用意する・閉じる。「作業用のワークスペース開いて」「作業 WS 出して」「手作業する場所を用意して」と言われた時と、ユーザーに手作業や対話的な操作を頼む（「ユーザーで実行してください」「端末で叩いてください」）直前に使う。結果を会話に戻す `!` での依頼には使わない。diff やファイルを見せるだけなら nvim-review。HERDR_ENV=1 が前提。
---

# Work Workspace

main（人間の窓口の agent ペイン）ごとに 1 つ、作業用の herdr workspace `work/<slug>` を持たせる。母艦の workspace にペインを足さず、人間が広い画面で Neovim を読んだり shell で手作業したりする場所にする。

## 使い方

| 状況 | コマンド |
|---|---|
| 作業 WS を開く（無ければ作る。あれば使い回す） | `work-ws ensure` |
| ユーザーに手作業・対話的な操作をしてもらう | `work-ws ensure` の後、「作業 WS `work/<slug>` の下の shell で実行してください」とコマンドを添えて頼む |
| 結果を会話に戻す必要があるコマンドを頼む | 従来どおり `! <command>` で頼む（作業 WS の shell の出力は会話に戻らない） |
| main と作業 WS を行き来する（人間の操作） | herdr の `Ctrl+s w`（`work-ws toggle`） |
| 記録を見る | `work-ws show` |
| 閉じる | `work-ws close`（shell で何か実行中なら exit 3 で止まる。人間に確かめてから `--force`） |

`ensure` は JSON（`workspace_id` / `label` / `nvim_pane_id` / `shell_pane_id` / `created`）を返す。報告には label だけ書けばよい。

## 前提と境界

- 使うのは人間の窓口のセッション（main）だけ。worker / reviewer は使わない。
- 1 main につき最大 1 つ。`claude --resume`（`sebas resume` を含む） でペインが変わっても、同じ session なら同じ WS に付け替わる。
- 人間のフォーカスは動かさない（別の作業中のことが多い）。用意したら「`work/<slug>` を用意しました（`Ctrl+s w` で移れます）」と伝える。
- 自分からは閉じない。sebas から起動された main なら、終了後に sebas が「使っていますか？」と確かめて閉じる。それ以外は人間が閉じる（`work-ws close` か `hclean`）。
- `HERDR_ENV=1` の外では使えない。その時は `!` での実行を頼む。
- 失敗しても 1 行報告して先へ進む。
