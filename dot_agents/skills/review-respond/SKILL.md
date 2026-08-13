---
name: review-respond
description: Git worktree の .review/review_comments.yaml にある must / imo / q のレビューへ対応し、対象branchにGitLab MRがあれば元コメントと対応結果をdiscussionへ同期する。「レビュー対応」「review comments」
---

# Review Respond

レビュー対象worktreeの`.review/review_comments.yaml`を絶対パスで特定し、ローカル対応とGitLab MR上の証跡を一つのworkflowとして処理する。

GitLab MRが一意に存在する場合、元コメントのdiscussion投稿、AI回答のreply、完了threadのresolveはこのskillの標準動作である。最初のwrite前に同期先projectとMRをユーザーへ通知する。commit、push、MR作成は標準動作に含めず、exact diffとdestinationを示して都度明示確認する。

## Helper

GitLab API、position計算、冪等性、YAMLのatomic updateには次を使う。

```text
~/.agents/skills/review-respond/scripts/gitlab_review_sync.py
```

直接`glab mr note create`を使わない。GitLab 15.8ではfile-level commentが使えないため、inline不可時はoverview discussionまたはlocal-onlyだけを選択肢にする。

## YAML の特定

1. ユーザーがYAMLのパスを明示した場合は、その絶対パスを使う。
2. 明示がない場合は、現在のGitリポジトリで`git worktree list --porcelain`を実行する。
3. 各`worktree`行の絶対パスに`.review/review_comments.yaml`を連結し、存在する候補を列挙する。
   - 1件: その絶対パスを使う。
   - 0件: 探索した絶対パスを報告して停止する。
   - 複数件: 候補の絶対パスを提示して対象を確認する。文脈から有力な候補を推定できる場合は、推定理由とともに「このYAMLですか？」と確認する。確認前に処理しない。
4. 選択したYAMLは`yq`でparseする。更新とarchiveはhelperの`yaml-patch`と`archive`だけを使い、直接置換や無lockの`yq -i`を行わない。answerやresolutionなどの自由文を含む更新はJSON一時ファイルを作り、`yaml-patch --patch-file`で渡す。

対象ファイルの`file`が絶対パスならそのまま使う。旧形式の相対パスは、選択したYAMLのworktree root（`.review`の親）を基準に絶対パス化する。

## YAML フォーマット

新規entryはcaptureしたコード版を識別するmetadataを持つ。

```yaml
reviews:
  - id: "stable-entry-id"
    file: "/abs/worktree/path/to/file.go"
    relative_file: "path/to/file.go"
    category: must
    status: pending
    capture_head_sha: "..."
    capture_file_blob: "..."
    reviewed_text: "..."
    context_before: []
    context_after: []
    start_line: 54
    end_line: 61
    start_col: 1
    end_col: 12
    timestamp: "2026-04-16T..."
    comment: |
      指摘内容
```

最初のMR選択時に各entryへ同期先を固定する。

```yaml
    gitlab:
      host: "git.example.com"
      source_project_id: 10
      target_project_id: 20
      source_branch: "feature"
      mr_iid: 123
      expected_head_sha: "..."
      discussion_id: "..."
      original_note_id: 456
      replies: {}
      resolved: false
```

再実行時は保存済みの`host + target_project_id + mr_iid`を使う。MRを再発見して別MRへ差し替えない。固定先がclosed、merged、消失、またはbranch再利用で不整合になった場合は停止して確認する。

## 後方互換性

- `category`がなく`severity`だけがある旧entryは`imo`として扱う。
- `status`がないentryは`pending`として扱う。
- `id`がない旧entryは、処理前にhelperの`migrate-legacy --entry-index`でlock付きのstable IDを付与する。capture metadataがない旧entryはinline同期せず、現在位置を確認したうえでoverviewへ投稿するか、local-onlyにするかをユーザーへ確認する。
- local-onlyを選んだentryは`gitlab.mode: skipped`と理由を記録する。

## 状態

| status | 意味 |
|---|---|
| `pending` | 元commentの同期またはレビュー対応が未完了 |
| `awaiting_decision` | q、曖昧なimo、想定外の人間replyなどユーザー判断待ち |
| `awaiting_publish` | ローカル修正・検証済みだが、承認済みcommit/pushとGitLab reply/resolveが未完了 |
| `resolved` | GitLab同期まで完了、または明示的にlocal-onlyで完了 |

コード変更が必要なentryを、修正直後に`resolved`へしない。`awaiting_publish`には次を保存する。

- baseline commit
- 承認対象patchのdigest
- 対象path/hunk
- push予定remote/ref
- resolutionと検証結果

retry時にworking treeと保存済みpatch digestが一致しなければ、commitやreplyを行わず、現diffを再提示して判断を求める。

## GitLab preflight

コードを修正する前に全未解決entryへ実施する。

1. helperの`discover`でGitLab host、source project、branch、open MR候補をread-onlyで取得する。
2. 候補が1件なら同期先を通知し、各entryへMR identityを固定する。
3. 0件なら、現在の変更、commit対象、push destination、MR targetを提示して、Commit / Push / MR作成を確認する。拒否された場合は同期を待つかlocal-onlyで続けるか確認する。
4. 複数件、detached HEAD、fork/remote不整合は対象を確認する。
5. helperの`position`で次を全entryについて検証する。
   - local HEADとMR headが一致する。
   - capture blobがworking treeと`HEAD:{relative_file}`のblobに一致する。
   - reviewed_textが保存行に一致する。
   - relative fileがMR diffのnew_pathへ一意に対応する。
   - old_path/new_pathとnew-side line/rangeを解決できる。
6. 全entryが同一のexpected headでpreflight済みになってから、元commentを投稿する。

GitLab側に未反映の保存済みdirty fileは正常なcaptureである。Commit / Push後にcapture blobとMR head blobが完全一致した場合だけ投稿する。

## 元commentの投稿

1. helperの`post-original`を使い、全entryの元commentをコード変更前に投稿する。
2. 各POST直前にexpected headを再照合する。途中でMR versionが変化した場合、投稿済みthreadは保持し、未投稿entryを自動的に別versionへ投稿せず停止する。
3. helperの結果からdiscussion ID、note ID、position SHAを`yaml-patch`で保存する。
4. inline不可時は自動fallbackしない。
   - GitLab 15.8: overview discussion / local-onlyを確認する。
   - overviewはhelperの`post-original --mode overview`を使い、同じmarker・sanitization・retry規則を適用する。
5. helperはentry IDとphase/content digestの非表示markerを使う。retry時は全discussion pageを検索し、0件ならcreate、完全一致する1件ならreuse、複数またはidentity不一致なら停止する。

元comment、answer、resolutionはquick action、mention、絶対path、credentialをそのままGitLabへ出さない。helperが安全にrenderできない本文は投稿せず報告する。

## カテゴリ別の対応

### must

- 原則として修正する。
- protected contractとの衝突、重大な回帰、要求矛盾がある場合だけ保留する。
- 修正・focused test後はresolutionを記録し、`awaiting_publish`にする。

### imo

- 技術的・プロダクト的に評価し、見解を示す。
- 採用して修正した場合は`awaiting_publish`にする。
- 不採用でコード変更がなければ理由を同じthreadへreplyし、想定外の人間replyがないことを確認してresolve後に`resolved`とする。
- ユーザー固有の意図が必要ならanswerをreplyし、`awaiting_decision`にする。

### q

- 質問へ回答し、質問だけを根拠にコードを修正しない。
- answerを同じthreadへreplyし、`awaiting_decision`にする。
- 明示判断後、変更不要なら最終replyとresolve、変更が必要なら修正・検証後に`awaiting_publish`へ進める。

## Publish

readyなコード変更は1回のreview runで一つのbatchにまとめる。qの判断待ちは、他entryのreadyな修正を妨げない。

1. 既存のstaged変更を確認する。承認対象外がstagedなら停止する。
2. `.review/**`を除外し、明示path/hunkだけをstageする。`git add -A`を使わない。
3. commit直前の`git diff --cached`を全文提示し、保存済みpatch digestと一致することを確認する。
4. commit message、明示remote/ref、MR URLを提示し、Commit / Pushを確認する。
5. commit後にparentとの差分が承認済みcached diffと一致し、`.review/**`を含まないことを再確認する。
6. 確認済みsource projectのremote/refへpushする。tracking設定だけに依存したpushをしない。
7. MR headがpushしたcommitになったことを確認する。
8. 固定済みhost、source/target project、source branch、MR IIDが変わっていないことを再確認し、各entryの`gitlab.expected_head_sha`だけを検証済みのpush commitへ`yaml-patch`で更新する。他のMR identityは変更しない。
9. resolution、実行した検証、commit SHAを各threadへphase付きでreplyする。
10. resolve直前にdiscussionをGETし、marker付きの自分のnote以外の非system replyがないことを確認する。人間replyがあれば`awaiting_decision`として停止する。
11. resolve後のGETでresolvedを確認してからentryを`resolved`にする。

commitまたはpushを拒否された場合は`awaiting_publish`のまま保持し、threadをresolveしない。

## Partial failureとretry

- original/replyのPOST成功後にYAML更新前で停止しても、phase markerを検索して既存noteを再利用する。
- resolveはGETで現在状態を確認してから冪等なPUTを行い、再度GETする。
- GitLab API、auth、network failureはローカル対応を破棄しない。同期を待つかlocal-onlyで完了するか確認する。
- helper、Neovim capture、YAML update、archiveは`.review/.lock`を共通利用する。lockが残っている場合は、別writerがいないことを確認するまで削除しない。

## 対応フロー

1. YAMLを絶対パスで特定してparseする。
2. GitLab preflightを全entryへ行い、元commentを全件投稿する。
3. 対象コードの該当範囲と前後を読み、カテゴリ順ではなく記録順に対応する。
4. focused testと必要な検証を実行する。
5. コード変更なしのreply/resolveを行う。
6. readyな修正をbatchでCommit / Push確認し、publish後にreply/resolveする。
7. 結果をentryごとに報告する。
8. 全entryが`resolved`の場合だけhelperの`archive`を使う。

## ファイル種別に応じたスキル活用

| 拡張子 | スキル |
|---|---|
| `.go` | coding-golang（実装）→ reviewing-golang（自己レビュー） |
| その他 | 汎用的に対応 |

## 対応結果の報告

```text
## レビュー対応結果

### 1. {file}:{start_line}-{end_line} [{category}]
- コメント: {要約}
- 対応: {何をしたか}
- 見解・回答: {imoまたはq。該当しなければ省略}
- ローカル状態: pending / awaiting_decision / awaiting_publish / resolved
- GitLab: MR URL / discussion ID / synced, waiting, skipped
```

## アーカイブ

helperの`archive`は全entryが`resolved`であることを再検証し、同じ`.review/archive/{timestamp}.yaml`へatomicに移動する。archive先の絶対パスを報告する。
