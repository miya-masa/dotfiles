---
name: park
description: 外部の応答待ちで手が離れる作業を、herdr workspace ごと閉じても再開できる形に退避する時に使う。「park して」「一旦閉じたい」「外部待ちなので置いておく」「後で戻れるようにして閉じる」「レビュー待ちなので畳む」「戻るか分からないので畳んでおく」などで起動。待ち条件と外部影響を記録して ~/.claude/data/parked/ に永続レコードを書くところまでを行う。workspace を閉じる操作（hclean）と再開（hunpark）はユーザーが実行する。
---

# Park

## Overview

**戻る契機が自分の外にある作業**を、workspace ごと閉じてよい状態にしてから畳む。レビュー・CI・他者の回答・経過観察のように、自分では進められず、いつ戻るかも決まらないものが対象。

`handoff` との違い:

| | handoff | park |
|---|---|---|
| 目的 | 同じ作業をすぐ続ける | 中断して外部の応答を待つ |
| 保存先 | scratchpad（セッションの寿命で消える） | `~/.claude/data/parked/`（永続） |
| 固有の記録 | なし | **待ち条件** と **外部影響** |
| 再開 | 起動文を貼る | `hunpark` が workspace ごと復元する |

すぐ続けたい、context を圧縮したいだけ、なら `handoff` を使う。

## park しない場合

| 状況 | 代わりに |
|---|---|
| 作業が完了している | 報告して終わる（`次: なし`） |
| 自分で続けられる（外部待ちではない） | 続ける |
| 今日中に戻るのが確実 | workspace を開いたままでよい |
| セッションを圧縮して続けたい | `handoff` |

## 手順

### 1. 待ち条件を決める（必須・1行）

「何が起きたら戻るか」を、後から機械的に判定できる形で書く。

| 良い | 悪い |
|---|---|
| MR !123 にレビューが付いたら | レビュー待ち |
| pipeline 4567 が green になったら | CI 待ち |
| API 仕様の回答が返ってきたら | 確認待ち |
| 2026-09-10 の週次で計測結果を見る | 様子見 |

会話から取れなければ **1 問だけ** 聞く。それ以外は聞かない。

### 2. 外部影響を棚卸しする（必須・無ければ「なし」と書く）

**自分の手を離れて動いているもの**を漏らさず書く。park の主目的はここ。閉じた後に忘れると事故になる。

- 出した MR / PR / issue（番号と URL）
- 走らせた CI / パイプライン
- 投入したデータ（環境・量・消したかどうか）
- 起動したままのプロセス・コンテナ・トンネル・ポート
- 送った依頼（誰に何を）
- 触った共有リソース（DB / stg 環境 / feature flag）

### 3. 自分の workspace と pane を取る

```bash
herdr agent list | jq -r --arg w "$HERDR_WORKSPACE_ID" \
  '.result.agents[] | select(.workspace_id==$w)
   | [.agent, (.agent_session.value // ""), .cwd, (.terminal_title_stripped // "")] | @tsv'
```

`HERDR_WORKSPACE_ID` が無い（herdr 外）場合は `cwd` だけで書き、`panes` は自分 1 つにする。

### 4. レコードを 2 ファイル書く

保存先は `~/.claude/data/parked/`。ファイル名は `<YYYY-MM-DD>-<label の slug>`。

**`<name>.json`**（`hunpark` と `herdr-audit` が読む契約。キー名を変えない）

```json
{
  "parked_at": "2026-09-04T09:12:00+09:00",
  "label": "<herdr workspace の label。hclean の突合キーなので実際の label と一致させる>",
  "workspace_id": "w2T",
  "cwd": "<復元時に開くディレクトリの絶対パス>",
  "wait_for": "<待ち条件 1行>",
  "external_effects": ["<外部影響を1件1要素で>"],
  "panes": [
    {"agent": "claude", "session_id": "<uuid>", "cwd": "<絶対パス>", "note": "<この pane で何をしていたか>"}
  ]
}
```

- `panes` の順序が復元順。1 つ目が root pane、2 つ目以降は右へ split される。
- `session_id` は Step 3 の `agent_session.value`。空なら素の `claude` / `codex` が起動する。

**`<name>.md`**（人間が読む本文。`hunpark` の preview に出る）

```markdown
# park: <label>

- **待ち条件**: <1行>
- **park した日**: <YYYY-MM-DD>
- **worktree / branch**: <絶対パス> / <branch>
- **再開**: `hunpark` → このレコードを選ぶ

## 外部影響（閉じた後も動いているもの）

| 対象 | 状態 | 後始末 |
|---|---|---|
| MR !123 | レビュー待ち | 不要 |
| stg への faker 投入 | 停止済み・データは残置 | 戻ったら削除する |

## ここまでの状態

- 完了したこと
- 未了のこと
- 直前の検証・テスト・CI の結果（成否と失敗内容）
- ユーザーが承認した事項 / 却下した案

## 戻ったら最初にやること

1. <具体的な1手目>
```

`handoff` の抽出項目（worktree path・編集中ファイルの絶対パス・検証結果・未完了タスク）はそのまま md に入れる。**書き出しが命綱**なので、Read/Grep を増やさず手元の context だけで一気に書き切る。

### 5. 次の操作を伝える

Claude 自身は workspace を閉じない（自分が動いている pane を閉じることになる）。書き終えたら次を伝えて終わる。

```
park しました: ~/.claude/data/parked/<name>.md
待ち条件: <1行>
閉じる: hclean（この workspace は status=park で出ます）
戻る:   hunpark
```

## 不変条件

- `herdr workspace close` を自分で実行しない。
- 待ち条件と外部影響を空欄にしない（無いなら「なし」と書く）。外部影響が本当に無いなら、それは park ではなく完了か handoff。
- JSON のキー名と `panes` の構造を変えない（`hunpark` / `herdr-audit` の契約）。
- 既存の park レコードを上書きしない。同じ label を再度 park する時は既存を読み、待ち条件と外部影響を更新して書き直す。
- レコードの捨て方をユーザーに聞かれたら: 戻らないと決めたものは `hunpark` の picker で **Ctrl-X**。`hunpark` で再開したものは `~/.claude/data/parked/resumed/` へ移り、30 日で自動的に消える。
- `hunpark` は、レコードの session がまだ別 pane で生きていると復元を拒む。park は「閉じてから戻る」もので、元の workspace を残したまま復元すると同じ会話が 2 箇所で開く。
