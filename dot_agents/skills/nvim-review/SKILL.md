---
name: nvim-review
description: herdr workspace の Neovim に差分を diffview で開く。「diff を見せて」「レビュー開いて」「nvim で見たい」「差分どこ」「この変更を Neovim で確認したい」などで使う。Neovim を起動できないと答えるのではなく、この skill の CLI を実行する。HERDR_ENV=1 が前提。
---

# nvim Review

人間が差分を読む先を用意する skill。`nvim-review-open` を 1 回実行するだけで、判断も後片付けもしない。

同じ workspace で動いている Neovim の RPC socket（`~/.local/state/nvim/servers/<HERDR_WORKSPACE_ID>.sock`）に繋ぎ、`:DiffviewOpen <base>` を**新しいタブ**で開く。Neovim が居なければペインを分割して起動する。

## 使い方

| 状況 | コマンド |
|---|---|
| 作業中の変更を見せる（既定） | `nvim-review-open` |
| 比較起点を指定する | `nvim-review-open --base <rev>` |
| コミット済みの 1 コミット | `nvim-review-open --base HEAD^` |
| 別のリポジトリ（submodule 含む） | `nvim-review-open --repo <path> --base <rev>` |
| 別の workspace の Neovim | `nvim-review-open --workspace <id>` |
| untracked も diff に載せる | `--intent-to-add`（`git add -N` する。index を触るので既定は off） |
| フォーカスを動かさない | `--no-focus` |

`--base` を省くと default branch との merge-base を使う。submodule の差分は親リポジトリの diff に出ないので、見せたいなら `--repo` で別に開く。

## 前提と境界

- `HERDR_ENV=1` の外では動かない。その場合だけ「herdr の外なので開けない」と伝える。**「nvim は対話的だから起動できない」とは答えない。**
- 人間が insert / visual mode の間は開かない（打鍵が diffview 右側の実ファイルへ入るため）。1 行報告して終わるので、再試行しない。
- 人間が別 workspace を見ているときはフォーカスを奪わない。diff は開く。
- untracked は既定では diffview に出ない（diffview が commit と作業ツリーの比較では列挙しないため）。件数と一覧を stderr に出すので、報告に含める。
- 失敗しても 1 行報告して先へ進む。gate の待ち方は変えない。ペインの後片付けもしない。

## 見た後

差分に指摘を付けるのは Neovim 側の `<leader>rc` / `rm` / `rq`（`.review/review_comments.yaml` に溜まる）。溜まった指摘への対応は `review-respond` が担当する。この skill はそこまで踏み込まない。
