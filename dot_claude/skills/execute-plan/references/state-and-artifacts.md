# workflow state と artifact

`.aidocs/workflows/<workflow-id>/context.json` が software delivery workflow の**唯一の機械可読な state authority**。報告・`progress.md`・command 出力は evidence であって、それ自体では workflow を進めない。helper は Claude Code と Codex で共有する単一実装で、`~/.agents/workflows/software_delivery/scripts/` に置かれている。

```text
.aidocs/workflows/<workflow-id>/
├── context.json      state authority（schema v1・CAS revision）
├── spec.md           承認済み spec
├── plan.md           decision-complete plan
├── tasks/            task artifact（short path は 01-short-path.md 単独）
├── reviews/          reviewer の報告
├── verification.md   local verification の evidence
└── progress.md       append-only の監査ログ
```

## artifact のライフサイクル

```text
python ~/.agents/workflows/software_delivery/scripts/workflow_artifact.py \
  new-id [slug] [--project-root ROOT]
python ~/.agents/workflows/software_delivery/scripts/workflow_artifact.py \
  init --project-root ROOT --workflow-id ID [--default-branch B] [--base-commit C]
python ~/.agents/workflows/software_delivery/scripts/workflow_artifact.py \
  remove --project-root ROOT --workflow-id ID --expected-revision N \
  [--phase ARTIFACT_REMOVE] [--context PATH]
```

- `new-id` は slug を小文字 ASCII とハイフンへ正規化して 38 文字に切り詰め、UTC 秒と 8 桁の hex を付ける（最大 63 文字）。
- `init` は既存 / 衝突する workflow ディレクトリを拒否し、traversal・絶対・不正・symlink の path も拒否する。canonical な project root、artifact root、Git の default branch、full base commit を schema-v1 `context.json` に記録する。初期状態は phase `DISCOVERY`、revision `0`、worktree なし、shipping 認可なし、task 履歴は空、`spec_review` は pending。
- `init` は artifact を作る前に `.aidocs/` について `git check-ignore` を実行する。project が未 ignore なら、repository-local な `.git/info/exclude` へ `/.aidocs/` を **1 度だけ**追記する。既存のバイトは保全し、再実行は冪等で、**tracked な `.gitignore` は決して書き換えない**。Git metadata が symlink または利用不可なら、別の場所へ迂回せず拒否する。→ artifact は Git 追跡対象にならない。**init に失敗したら workflow を始めない。**
- `remove` は fail-closed。canonical な project root、symlink でない単一の直下 workflow path、`context.json` の identity 一致を検証し、schema 妥当で phase が `ARTIFACT_REMOVE`、かつ `--expected-revision` が正確に一致することを要求する。不一致なら artifact に触れない。`.aidocs/` 自体や他の workflow、symlink 先は決して削除しない。
  ただし**通常の workflow は artifact を削除しない**。merge 後も spec / plan / review / verification / progress を参照するため、`post-merge-cleanup` は worktree だけを消して `WT_REMOVE` で終端する。`remove` はユーザーが個別に「この workflow の記録を消す」と依頼した時だけ使う。

## state CLI

すべての command が `--context <path>` を要る。

```text
workflow_state.py validate  --context context.json
workflow_state.py transition --context context.json \
  --expected-revision N --to PHASE [--patch-json JSON_OBJECT]
workflow_state.py invalidate-normative --context context.json --expected-revision N
workflow_state.py stop   --context context.json --expected-revision N --reason "external blocker"
workflow_state.py resume --context context.json --expected-revision N
```

成功する変更はすべて compare-and-swap。渡した revision が `state.artifact_revision` と一致する必要があり、結果の revision はちょうど 1 つ増える。不正な JSON、フィールド欠落、無効な遷移、不変 identity の変更、stale な revision は非ゼロ終了し、**元のバイトを一切変更しない**。

`invalidate-normative` は `SPEC_REVIEWS` へ戻し、`plan_path` を削除し、有効な `execution.tasks` を消し、plan と下流 gate の値・実行方法の選択・snapshot を消し、shipping 認可を取り消し、shipping status を初期化する。有効な task ID を後継 plan へ持ち越さない。監査履歴は append-only の `progress.md` か別の履歴フィールドに置き、invalidation はそれらを変更しない。

### schema v1 の必須オブジェクト

- `identity`: `schema_version`(`1`), `workflow_id`, `source_root`, `artifact_root`, `default_branch`, `base_commit`（初期化後は不変）
- `workspace`: nullable な `worktree_path`, `branch`
- `state`: `phase`, nullable な `stopped_from`, 非負の `artifact_revision`
- `authorization`: `shipping_authorized`
- `artifacts`: `spec_path`, nullable な `plan_path`, `tasks_path`, `reviews_path`, `verification_path`
- `execution`: task 記録、gate 記録、nullable な実行方法 `choice`、nullable な `review_snapshot_id`
- `shipping`: nullable な `commit`, `push`, `mr`, `ci`

### state graph

phase 名と辺は helper の `PHASES` / `TRANSITIONS` が権威で、表にない jump は非ゼロ終了する。前進辺は次のとおり。

```text
DISCOVERY → SPEC_DRAFT → SPEC_REVIEWS → USER_APPROVED_SPEC → PLAN → PLAN_REVIEW
  → EXECUTION_CHOICE → WORKTREE_READY → TASKS → FINAL_REVIEW → LOCAL_VERIFICATION
  → LOCAL_COMPLETE → COMMIT → PUSH_MR → CI → MR_READY → MERGE_CHECK
  → WT_REMOVE → ARTIFACT_REMOVE
```

`WT_REMOVE` が通常の終端。`ARTIFACT_REMOVE` は helper 上の辺として残っているが、既定の workflow では踏まない（artifact を残すため）。

short path は `DISCOVERY → SHORT_TASK_DRAFT → EXECUTION_CHOICE`。Claude では preflight review を挟まないので `SHORT_TASK_PREFLIGHT` は使わない（helper 上は Codex 用に残っている）。

| phase | 担当 skill |
|---|---|
| `DISCOVERY` / `SPEC_DRAFT` / `SPEC_REVIEWS` / `USER_APPROVED_SPEC`（short path は `SHORT_TASK_DRAFT`） | `product-discovery` |
| `PLAN` / `PLAN_REVIEW` / `EXECUTION_CHOICE` | `implementation-planning` |
| `WORKTREE_READY` / `TASKS` / `FINAL_REVIEW` / `LOCAL_VERIFICATION` / `LOCAL_COMPLETE` | `execute-plan` |
| `COMMIT` / `PUSH_MR` / `CI` / `MR_READY` | `ship-change` |
| `MERGE_CHECK` / `WT_REMOVE` | `post-merge-cleanup`（**`WT_REMOVE` が終端。artifact は残す**） |
| `ARTIFACT_REMOVE` | 既定では使わない。ユーザーが artifact の削除を個別に依頼した時だけ |

戻り辺と分岐:

- 差し戻し: `SPEC_DRAFT` / `SPEC_REVIEWS` / `PLAN` → `DISCOVERY`、`USER_APPROVED_SPEC` → `SPEC_REVIEWS`、`PLAN_REVIEW` → `PLAN`、`SHORT_TASK_DRAFT` → `DISCOVERY`、`FINAL_REVIEW` / `LOCAL_VERIFICATION` / `CI` → `TASKS`。
- `DEBUGGING` へは `TASKS` / `FINAL_REVIEW` / `LOCAL_VERIFICATION` / `CI` から入り、`TASKS` へ戻る。
- `LOCAL_VERIFICATION → COMMIT` の直行辺も helper 上は存在するが使わない。`execute-plan` は `LOCAL_COMPLETE` で止まり、shipping は必ず `LOCAL_COMPLETE → COMMIT` から入る。
- `USER_DECISION_REQUIRED` へは非終端の全 phase から入れる。外部 blocker は `stop` を使い、直前の phase が `state.stopped_from` に記録され、`resume` がそれを復元する。`stopped_from` を持たない user-decision 状態は resume できない（該当する normative gate か controller gate で解消する）。
- `ARTIFACT_REMOVE` と `USER_DECISION_REQUIRED` は出口を持たない。`STOPPED` phase は存在しない。

### shipping 認可の記録

`execute-and-ship` の認可は phase 遷移と同じ CAS で書く。`--patch-json` は候補 state への deep merge で、`--to` の phase が優先される。

```text
workflow_state.py transition --context context.json --expected-revision N \
  --to EXECUTION_CHOICE \
  --patch-json '{"authorization":{"shipping_authorized":true},"execution":{"choice":"execute-and-ship"}}'
```

`invalidate-normative` は `shipping_authorized` を `false` に戻し、実行方法の選択と snapshot も消す。

## 原子的な commit point と復旧

変更時、helper は次の context 全体を同じディレクトリ内の一意な一時ファイルへ書き、flush と `fsync` をしてから `os.replace` で `context.json` に被せる。**replace の成功が commit point**。書き込み失敗や replace 前の中断は一時ファイルを消し、直前の context をバイト単位でそのまま残す。

load → revision 比較 → 操作 → replace の全体は、context を含むディレクトリ inode への `fcntl.flock` 排他ロック下で行う（replace をまたいでロックを安定させるため、置換される inode ではなくディレクトリをロックする。ロックファイルは作らない）。2 番目の writer は待機後に新しい revision を読み、CAS が stale として失敗する。

中断後の resume では `context.json` を読んで検証し、記録された artifact と Git evidence を実際に確認し、**最後に原子的 commit された revision だけを信じる**。部分的に書かれた一時ファイルや、context より先行した報告から後の state を推論しない。

## review snapshot

```text
python ~/.agents/workflows/software_delivery/scripts/review_snapshot.py \
  --repo ROOT --base-commit FULL_COMMIT \
  --allowlist-json '{"version":1,"paths":["path/to/file"]}' \
  --source worktree|index --output MANIFEST
```

allowlist は version `1` で、正規化した repository 相対 path を持つ。重複、`..` の脱出、絶対 path、末尾セパレータ、symlink の親、`.git` metadata path は拒否される。base commit は full な解決済み ID が必須（短縮形は拒否）。

manifest は `base_commit` と、正規化 path 順に並んだ `paths`（`content_sha256` / `mode` / `path` / `state`）を持つ。`state` は `present`（選択された最終 tree の mode と生バイト。symlink は link 先を hash）/ `deleted`（削除された base entry の mode と content hash）/ `absent`（base tree にも選択 tree にも無い）。

snapshot ID は canonical JSON（`sort_keys=True`、compact separators、末尾改行なし）の UTF-8 バイトに対する `sha256:<hex>`。source selector は manifest に含まれないので、**等価な worktree と index は同じ ID になる**。base commit・allowlist 対象の内容・mode・削除のいずれかが変われば ID が変わる。

標準出力は ID と preflight を含む 1 つの JSON。

```json
{"preflight":{"external_dirty_paths":[],"external_staged_paths":[],"shipping_blocked":false},
 "review_snapshot_id":"sha256:<hex>"}
```

allowlist 外の dirty / staged path は identity から除外されるが、**shipping は blocking する**。`index` mode では allowlist 外の staged path は hard error（manifest も置換しない）。manifest は全検証と hash に成功した後にだけ、同一ディレクトリの一時ファイルと `os.replace` で置換される。

## cleanup 結果の確認

worktree 削除の確認に helper は使わない。Worktrunk の JSON はスキーマが version 間で変わるため、`git worktree list` と `git branch --list` で Git 側を直接確認する（`post-merge-cleanup` の契約を参照）。保存した `wt-remove.json` は evidence として artifact 配下に置くだけで、判定の根拠にはしない。
