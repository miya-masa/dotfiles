---
name: ci-monitor
description: CI/CDパイプラインやMerge Request/Pull Requestの状態監視。「CI監視」「MR監視」「PR監視」「パイプライン確認」「CIの状態」「CIチェック」「MRのステータス」「PRの状態」「CI待ち」「パイプライン見て」「CIどうなった」「MR確認して」等の依頼時に使用。MR作成（glab mr create / gh pr create）の直後にも自動発動し、継続監視モードで実行する。
---

# CI Monitor

CI/MR/PR のステータスを確認・監視する。GitLab（glab）と GitHub（gh）の両方に対応。

## モード判定

| ユーザーの意図 | モード | 動作 |
|---|---|---|
| 「CIの状態確認して」「MRどうなった」 | **ワンショット** | 1回チェックして結果を報告 |
| 「CI監視して」「CI通るまで見て」「MR監視」 | **継続監視** | /loop で定期チェック、完了まで監視 |
| MR/PR 作成直後 | **継続監視** | 自動で /loop 開始 |

## ワンショットチェック

### Step 1: 対象の特定

ユーザーが対象を指定しない場合、カレントブランチの最新パイプラインを確認する。

### Step 2: ステータス取得

**各 MR/PR を個別の Bash tool call で並列実行する。** ループやBash配列は使わない。

GitLab:
```bash
# MR のステータス
glab api "projects/<encoded_project>/merge_requests/<mr_iid>" | jq '{state, title, web_url}'

# MR のパイプライン
glab api "projects/<encoded_project>/merge_requests/<mr_iid>/pipelines" | jq '.[0] | {status, web_url}'
```

GitHub:
```bash
# PR のステータス
gh pr view <pr_number> --json state,title,url,statusCheckRollup

# ブランチの CI
gh run list --branch <branch> --limit 3 --json status,conclusion,name,url
```

カレントブランチの場合:
```bash
# GitLab
glab ci status

# GitHub
gh run list --limit 3
```

### Step 3: 結果報告

テーブル形式で報告する:

```
| MR/PR | サービス | ブランチ | MR状態 | CI状態 |
|-------|---------|---------|--------|--------|
| !12   | service-a | main | open | success |
| !13   | service-a | release-branch | merged | - |
| #34   | service-b | main | open | running |
```

## 継続監視

### Step 0: 経路判定

```bash
test "${HERDR_ENV:-}" = 1
```

成立するなら **herdr 経路**（下記）を使う。ポーリングを別ペインに持たせ、確定時の出力だけを読むため、controller のターンとコンテキストを消費しない。不成立なら従来の ScheduleWakeup 経路（Step 1 以降）を使う。

#### herdr 経路

`herdr-delegate` の `command:one-shot` モードに従う（ペイン確保・完了後の close 等の手順は同契約を参照し、ここでは再掲しない）。

```bash
# 確定するまでペイン側で回す。確定時に一意のトークンを出力させる
herdr pane run "$pane" 'while :; do s=$(glab ci status 2>&1); case "$s" in *success*|*failed*|*canceled*) echo "$s"; printf "CI""_SETTLED\n"; break;; esac; sleep 30; done'

# 確定を待つ（Bash tool の上限に合わせ 600 秒以内で刻む。timeout したらまだ CI が動いているので同じ呼び出しを再度行う）
herdr pane wait-output "$pane" --match CI_SETTLED --timeout 600000

# 確定内容だけを読む（pane read はプレーンテキストを返す。jq に通すと空になる。recent-unwrapped は出力がスクロールするまで空なので短い出力は --source visible を使う）
herdr pane read "$pane" --source recent-unwrapped --lines 60
```

`printf "CI""_SETTLED\n"` はリテラルを分割し、投入コマンド行のエコーに `wait-output --match` が誤マッチしないようにしている（分割しないと投入直後に誤報する）。

GitHub の場合は `glab ci status` を `gh run list --branch <branch> --limit 1` 等に差し替える。判定・失敗分析・報告は Step 2 以降と同一。

### Step 1: /loop 開始（herdr 外の経路）

ScheduleWakeup を使い、約 180 秒（3分）間隔で監視する。

### Step 2: 各 tick で確認

1. 全対象の CI ステータスを**並列個別呼び出し**で取得
2. 状態に応じて判定:

| CI 状態 | アクション |
|---------|-----------|
| `success` | 完了。全対象が success なら監視終了 |
| `running` / `pending` | 継続監視 |
| `failed` | 失敗分析へ（後述） |
| `canceled` | ユーザーに報告、指示を仰ぐ |

### Step 3: 失敗分析

CI が failed の場合:

```bash
# GitLab: 失敗ジョブの特定
glab api "projects/<encoded_project>/pipelines/<pipeline_id>/jobs" | jq '[.[] | select(.status=="failed") | {name, stage, web_url}]'

# GitHub: 失敗ジョブの特定
gh run view <run_id> --json jobs | jq '[.jobs[] | select(.conclusion=="failure") | {name, conclusion}]'
```

判定基準:
- 変更ファイルに関連するジョブが失敗 → **修正が必要**（ユーザーに報告）
- lint / build 失敗 → **修正が必要**
- 同じ SHA で直前の実行が success → **フレーキー**（リトライ実行）

フレーキー判定時のリトライ:
```bash
# GitLab
glab ci retry <job_id>

# GitHub
gh run rerun <run_id> --failed
```

### Step 4: 完了報告

全 CI が通ったらユーザーに報告する。

## 厳格ルール

- パイプラインが running / pending の間は「CI が通った」と報告しない
- CI ステータスを報告する前に、パイプライン API で**全ジョブの完了**を確認する
- リリースタグは CI が全て green になるまで絶対に作成しない（CI完了前のタグ作成はロールバック工数大）

## プロジェクト識別子のエンコーディング

GitLab API のプロジェクトパスは `/` を `%2F` にエンコードする:

```
group/project     → group%2Fproject
group.sub/project → group.sub%2Fproject
```
