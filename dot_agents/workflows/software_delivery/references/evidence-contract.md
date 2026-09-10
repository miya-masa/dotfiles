# Evidence contract

Codex と Claude の共有実装が読む証拠契約。`evidence.json` は canonical な active/retired AC registry、固定した check（`argv`、`cwd`、`inputs`、`targets`、期待値）、review、snapshot、CI 委譲を持つ。AC の定義は spec または short task の canonical table と exact に一致しなければならない。

実行は `workflow_artifact.py evidence-run --context PATH --check ID` で新しい run に記録する。pytest は現在の JUnit と全 target の成功、Go は `go test -json` の package/test の実行と成功、command は固定 exit code と stdout/stderr assertion の一致を要求する。exit 0、手書きの passed、古い report、skip、欠落 target は成功証拠にならない。最新 attempt の失敗・中断・未完了は過去の成功へ fallback しない。

レビューの `UNSATISFIED` は verification gate を拒否する。`UNVERIFIED` は理由と予定 check がある場合に限り local verification 待ちとして保持でき、receipt の成功で解消する。`LOCAL_COMPLETE` は全 active AC の有効な成功 receipt と risk に応じた human gate を要求する。v2 LOW は自動通過、MEDIUM/HIGH と旧 v1 は現在提示への明示承認が必要。CI 委譲だけが残る場合は、明示的な shipping 認可・local 成功・index identity 一致のある `COMMIT` 経路だけを許可し、CI 成功までは `MR_READY` に進めない。

契約 hash は review 欄を除く canonical projection から計算し、review は `reviewed_contract_hash` と snapshot に束縛する。receipt は対象 snapshot、inputs、raw log/report の hash を再検査する。`evidence-ci` は固定 GitLab host/project と pipeline の SHA、required job の最新 attempt が全て成功した場合だけ委譲を解消する。`evidence-export` は参照される source、oracle、review、receipt、raw files を相対構造でコピーし、移動後も hash を検査する。

この契約は同一権限内の明示 inputs と整合性を検査する。業務 oracle の正しさ、CI 内部の test 件数、暗号学的な改変防止、全言語・全環境の再現性は保証しない。

## 登録と schema

すべての object は下表のキーを過不足なく持つ。文字列は指定がなければ非空、配列の ID・path・target は重複不可。未知のキー、重複 JSON key、非有限数は拒否する。

| 型 / field | 必須構造と値 |
| --- | --- |
| Evidence | `version: 1`（legacy）または `2`（新規）, `workflow_id: context.identity.workflow_id`, `source: Ref`, `allowlist`, `active`, `retired`, `checks`, `review`, `ci` |
| Ref | `{root: "repo" または "workflow", path: 相対POSIX, sha256: HEX64}`。HEX64 は lowercase 64桁、prefix なし。root は選択 worktree と固定 artifact directory。絶対path、空成分、`.`、`..`、backslash、symlink経由を拒否し、既存通常fileを参照する |
| Oracle | Ref の全キー + `locator: 非空文字列`。出典の見出し・行・AC ID等を固定する。Ref に locator を付けることも、Oracle から省くことも不可 |
| source | `root: "workflow"`、`path: "spec.md"` または `"tasks/01-short-path.md"` の Ref のみ |
| allowlist | `{version: 1, paths: [repo相対path, ...]}`。空配列可。snapshot の既存 allowlist 規則に従う |
| active | 非空配列。各 row は `{id: "AC1", oracle: Oracle, plan: Ref, task: Ref, checks: [check ID, ...]}`。ID は `AC[1-9][0-9]*`、checks は非空 |
| retired | 空配列可。各 row は `{id: AC ID, reason: 非空文字列}`。active と交差不可 |
| checks | 非空配列。各 row は `{id, kind, argv, cwd, inputs, targets, expected_exit, assertions}`。ID は `[a-z][a-z0-9_-]*`。全 check を active から参照し、未知 ID は不可 |
| inputs | 全 kind で非空 Ref 配列。`context.json`、`evidence.json`、`evidence/` 内の実行出力は不可（repo 経由の alias も拒否）。実行前後に実 file hash を比較する |
| review | 登録中は `null`。記録時は `{path, hash, reviewed_contract_hash, snapshot_id, verdict, ac}`。path は workflow 相対 review file、hash はその HEX64。後二つの hash は `sha256:HEX64`。verdict は `APPROVED` または `CHANGES_REQUIRED` |
| review.ac | active と exact 一致する row 配列。各 row は `{id, status, reason, checks}`。status は `SATISFIED` / `UNSATISFIED` / `UNVERIFIED`、reason は文字列（UNVERIFIED では非空必須）、checks は当該 active row と exact 同集合 |
| ci | CI check がなければ `null`。あれば `{host, project_id, required_jobs, delegated_ac, authorization_ref}`。host は URL ではなく hostname、project_id は正整数。required_jobs は全 CI targets の集合、delegated_ac は CI check を参照する AC の集合（両方非空）。authorization_ref は承認済み CI 委譲を指す **Oracle** |

| kind | argv / cwd / expected_exit | targets / assertions |
| --- | --- | --- |
| pytest | 非空 argv / repo 内の既存相対directory（`.`可）/ `0` | exact node ID（`::` を含む）の非空配列 / `[]` |
| go_test | 非空 argv / 同上 / `0`。直接実行は `go test -json -count=1 ...` 必須 | `{package: 非空, test: 非空}` の非空配列 / `[]` |
| command | 非空 argv / 同上 / 整数 | `[]` / 非空 `{stream: "stdout" または "stderr", op: "equals" または "contains", value: 文字列}` 配列。contains の value は非空。既知 test runner を command へ偽装しない |
| gitlab_ci | `[]` / `null` / `null` | 非空 job名配列 / `[]` |

argv は shell 展開せず実行する。pytest の JUnit・rootdir・plugin 設定は collector が追加するので固定 argv や既存設定から上書きしない。全 target の実行成功と今回の report を検査し、skip・欠落・Go cache 成功は成功証拠にしない。
contract hash は `review` だけを除いた object に `json.dumps(..., ensure_ascii=False, separators=(',', ':'), sort_keys=True, allow_nan=False).encode('utf-8')` を適用した SHA-256 に `sha256:` を付ける。`workflow_evidence.contract_hash(manifest)` を使い、review file hash・snapshot ID と混同しない。

## 実装前の assurance（version 2）

新規 workflow は `version:2` にし、既存 manifest へ次の `assurance` だけを追加する。v1 の record/承認/receipt を新規 LOW の根拠へ自動移行しない。

```text
assurance = {
  risk: "low" | "medium" | "high", reason: 非空文字列,
  existing_contract: bool, bounded_blast: bool, adequate_oracle: bool,
  protected_boundaries: [具体的な境界名],
  risks: [{kind: trigger, checks: [既存check ID]}],
  important: [{id: active AC ID,
    needs: [{kind: "concrete" | "negative" | "invariant" | "reference",
             checks: [そのACのcheck ID]}]}]
}
```

risk の条件と trigger の検証選定は [review-common.md](review-common.md#risk-に応じた検証の選択) を正本にする。LOW は三 bool が true、risks/boundaries が空。protected boundary、api/security、限定できない blast radius は HIGH。adequate_oracle=false は完了拒否。HIGH は具体的な boundary と important AC を持ち、negative/invariant/reference の少なくとも一種類で境界を反証する。各 important は必要な kind だけを非空で登録し、すべての種類を要求しない。

期待値・禁止例・不変条件・既存契約の本文は discovery の既存 spec/short task（`active[].oracle` の参照先）へ **実装前** に置く。例えば認可境界なら「他tenantのIDでは拒否しデータを返さない」。実装を見てから期待値を合わせない。重要でない AC の例や新しい文書は増やさない。

初回 `TASKS` 入口で state helper が `execution.gates.assurance_contract` を生成する。source/assurance/全active ACのoracle参照と対応checkのcommand・target・期待値を固定し、実装後に変わる inputs hash、review、receiptは含めない。戻り・resumeでは上書きせず、normative invalidationだけで解除する。実装後はinputsの実hashを更新し、run/後段gateで固定投影を再検査する。新testを作る前に実装結果のhashを要求しない。

同じcheck IDを複数AC/triggerから参照できる。一回の実行が複数ACを証明するならraw/receiptを共有する。新たな失敗attemptは従来どおり旧成功に優先する。hash固定は意味的な独立性の証明ではないため、reviewerがoracleの出典と反例を照合する。

## phase への接続と出荷条件（D1）

1. discovery 担当は spec（short path は task）に正本の表を1つだけ作る。header は `| AC ID | Lifecycle | Criterion |`、separator は `| --- | --- | --- |`、row は AC ID・`ACTIVE`/`RETIRED`・非空 criterion。Controller が source と registry の active/retired 集合を exact 照合する。
2. planning 完了時（short path は task 確定時）、Controller が v2 `evidence.json` に oracle・plan・task・固定 check・assurance を登録し、TASKS 入口で期待値を固定する。実行前には inputs の実 hash を揃える。final review 前に `load_contract` で検証し、reviewer へ正本 AC・契約 hash・snapshot を渡す。reviewer の AC 判定を Controller が確認し、review file を保存した後で `review` に hash・判定・binding を記録する。`USER_DECISION_REQUIRED` は state の停止で扱い、review.verdict に書かない。
3. execute-plan の Controller は `check-gates --to LOCAL_VERIFICATION` を確認し、既存 state/CAS 手順で進める。不足する local check を `workflow_artifact.py evidence-run --context PATH --check ID` で実行する。手実行や手書き passed は receipt の代用にならない。local 成功後に下記「人間レビューの記録と操作」で現在の品質を確認する。v2 LOW の passed は停止/回答なしで進め、他は提示・明示承認・resume を済ませる。通常の execute-plan 単体は `check-gates --to LOCAL_COMPLETE` 成功後に同 phase で止まる。
4. shipping 明示認可がある composite / ship-change は、全 local 必須 check の成功・review binding・risk に応じた human gate が有効で、承認済み CI 委譲 **だけ**が未完了なら、`LOCAL_VERIFICATION` から ship-change へ引き継げる。ship-change の Controller が既存 sanitize・stage・index equality を通し、`check-gates --to COMMIT` 成功後に既存 state/CAS 手順で `COMMIT` へ進む。全 AC の receipt が揃った通常の入口は `LOCAL_COMPLETE`。`UNSATISFIED`、local receipt 未成功の `UNVERIFIED`、未承認委譲をこの例外で出荷しない。
5. ship-change の Controller が `workflow_artifact.py evidence-ci --context PATH --pipeline-id ID` で固定 host/project の CI を収集する。commit SHA と全 required job の最新 attempt 成功を検査し、`check-gates --to MR_READY` 成功前に MR ready を報告しない。
6. cleanup の Controller が新 directory `evidence/cleanup` へ `workflow_artifact.py evidence-export --context PATH --output NEW_DIRECTORY`、`check-gates --to WT_REMOVE`、既存削除、`git worktree list` / `git branch --list` 確認、既存 state 遷移の順で進める。stale bundle は新 directory への再 export と検査後に置き換える（worktree 削除後は旧 bundle を参照に使う）。

`check-gates` の完全形は `python3 ~/.agents/workflows/software_delivery/scripts/workflow_state.py check-gates --context PATH --to PHASE`（read-only）。collector の完全形は `python3 ~/.agents/workflows/software_delivery/scripts/workflow_artifact.py` に上記 subcommand を続ける。state/CAS、risk matrix、snapshot の正本をここで再定義しない。legacy は現 phase で registry/receipt を補完して同じ gate を再検査する。
pytest の実設定（`PYTEST_ADDOPTS` の JUnit/rootdir/plugin、`WORKFLOW_EVIDENCE_RUN_ID`、`PYTHONDONTWRITEBYTECODE`、`pythonpath_prepend`）は `adapter.json` に保存され、receipt 検証時に schema・run ID・raw file hash を検査する。
各 run は `evidence/runs/<run-id>/` に start/receipt、argv/cwd、snapshot/inputs 前後、commit、raw log/report/API response と hash を保存する。同一契約・snapshot・check の最新 started attempt だけを採用し、中断・receipt 欠落から過去成功へ戻らない。export は source・oracle・review・選択した run を相対構造で保持し、`validate_export` が移動後も2 root 内で hash を検査する。

## Legacy version 1 の schema 例

Git repository 内から次を実行する。既存 repository は read-only で参照し、temporary directory 内に1つの command check 契約を作り、実 hash を埋めて `load_contract` に通す。これは schema 検証用であり、review / receipt を持つ出荷証拠ではない。未 installed の開発 checkout では第1引数を `dot_agents/workflows/software_delivery/scripts` に置き換える。

```sh
python3 - ~/.agents/workflows/software_delivery/scripts <<'PY'
import hashlib, json, subprocess, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(sys.argv[1]).expanduser().resolve()))
from workflow_evidence import load_contract, contract_hash
repo = Path(subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], text=True).strip())
base = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
with tempfile.TemporaryDirectory(prefix='evidence-schema-') as tmp:
    root = Path(tmp)
    (root / 'spec.md').write_text('| AC ID | Lifecycle | Criterion |\n| --- | --- | --- |\n| AC1 | ACTIVE | stdout が ok |\n')
    (root / 'plan.md').write_text('AC1: stdout の一致を確認する。\n')
    (root / 'task.md').write_text('AC1: fixed-command を実行する。\n')
    def ref(path):
        return dict(root='workflow', path=path, sha256=hashlib.sha256((root / path).read_bytes()).hexdigest())
    manifest = dict(version=1, workflow_id='schema-example', source=ref('spec.md'),
        allowlist=dict(version=1, paths=[]),
        active=[dict(id='AC1', oracle=dict(**ref('spec.md'), locator='AC1'),
                     plan=ref('plan.md'), task=ref('task.md'), checks=['fixed-command'])],
        retired=[], checks=[dict(id='fixed-command', kind='command',
            argv=[sys.executable, '-c', 'print("ok")'], cwd='.', inputs=[ref('task.md')],
            targets=[], expected_exit=0, assertions=[dict(stream='stdout', op='equals', value='ok\n')])],
        review=None, ci=None)
    context = dict(identity=dict(workflow_id='schema-example', source_root=str(repo),
                                artifact_root=str(root), base_commit=base))
    (root / 'context.json').write_text(json.dumps(context))
    (root / 'evidence.json').write_text(json.dumps(manifest))
    loaded = load_contract(root / 'context.json')
    assert loaded == manifest
    print('load_contract: OK', contract_hash(loaded))
PY
```

## 人間レビューの記録と操作

対象の分類と提示内容は [review-common.md](review-common.md#人間コードレビューの局所化) が正本。以下は `human_review.py` の操作契約である。新規はv2のrisk判定を使い、legacy v1は従来の承認を維持する。正式 workflow の記録は `context.execution.human_review`、直接経路は対象 repository の `git rev-parse --git-path human-review/<change-id>.json` に保存する。record を手書きせず helper で生成する。直接経路に spec / plan / task / context の作成を追加しない。

```sh
python3 ~/.agents/workflows/software_delivery/scripts/human_review.py --context /absolute/context.json --operation-file /absolute/operation.json --expected-revision N
python3 ~/.agents/workflows/software_delivery/scripts/human_review.py --record /absolute/git-metadata/human-review/change-id.json --operation-file /absolute/operation.json --expected-revision N
```

`--context` と `--record` は択一。更新直前に現在値を読み、workflow は `state.artifact_revision`、direct は record の `revision` を N に指定する。初回 direct は record が存在しない状態で N=0、成功すると revision=1。以後各操作で +1。操作内に revision を重ねて指定しない。未知/不足 field、競合、不正引用、前提不足では記録の byte を変更しない。

| 操作 | operation.json の exact keys と値 |
| --- | --- |
| workflow 提示 | `{action: "present", assessment}`。scope/target/quality/CI 履歴は既存 context/evidence と validator から生成 |
| direct 初回提示 | `{action: "present", scope: {id: change-id, repository: canonical絶対Git root}, target: {base_commit: full commit ID, allowlist: {version: 1, paths: [...] }}, assessment, quality}` |
| direct 再提示 | `{action: "present", target, assessment, quality}`。scope は指定せず既存値を維持 |
| 回答 | `{action: "respond", presentation_id: 最新提示UUID, targets: ["self"] または card IDの非空配列, decision: "approve_current" または "request_change", user_citation}` |
| 撤回 | `{action: "revoke", presentation_id, targets, user_citation}`。decision は指定しない |

`user_citation` は exact `{role: "user", reference: 発言の参照, quote: 実際の発言引用}`。空値/assistant role/旧提示/未知 card は拒否する。対象なしの回答だけ `targets:["self"]` を使う。helper が `basis` / `basis_hash` / target.snapshot_id / 新規 presentation UUID / prompt / revision / ci_pending を生成するため、caller はそれらや承認済み flag を入力しない。

`assessment` は legacy では `{self_reason, blockers, cards, verification_assumptions}`、v2ではこれに `boundary_cards` を加える。対象なしは非空 self_reason と `cards:[]`、対象ありは cards を埋める。blockers は `{kind, reason, evidence:[Ref,...]}` 配列（kind と行き先は review-common）。未解決 blocker があれば提示を拒否する。verification_assumptions は検証前提の Ref 配列（空可）。

card は `{id, question, code, scenario, impact, evidence, unresolved_reason, options, recommendation, current_option, answer_scope, conditions}`。code は非空の `{path, symbol, excerpt, reference:Ref}` 配列、evidence は非空 Ref 配列、options は異なる ID の `{id, description}` が2件以上。recommendation/current_option は実在 option ID。conditions は review-common の五条件と同じ順序の `{satisfied:true, reason, evidence:[Ref,...]}` を5件持つ。理由や bounded context を空にしない。対象なしでは self_reason を示し、カードを捏造しない。

v2 HIGH の `boundary_cards` は `{id, boundary, question, code, scenario, impact, evidence, answer_scope}`。code/Ref は既存カード型と同じで、全 protected_boundaries を確認対象に含める。五条件・複数案は不要。workflow のriskをassessmentへ再入力せずmanifestから導出する。LOWではカードも回答も作らない。

### 直接経路の品質証跡

新規 v2 direct は LOW 専用。`quality` は既存の `kind, review_requirement, reviews, validation` に `assurance` と `oracle` を一度だけ持つ。oracle は `root:"repo"` の既存契約/testを指す Oracle Ref で、base commit に同一hashで存在する必要がある。新しい外部挙動やMEDIUM/HIGHは正式workflowへ移す。

通常のtest実行を、同じ既存runnerを呼ぶ次のcollect操作へ置き換える。追加LLM/agentは不要。spec/plan/contextをdirect用に作らない。

```text
collect.json = {
  action: "collect", scope: {id: change-id, repository: 絶対Git root},
  target: {base_commit: full SHA, allowlist: {version:1, paths:[...]}},
  oracle: Oracle Ref, definition: 既存check schema
}
```

```sh
python3 ~/.agents/workflows/software_delivery/scripts/human_review.py --record "$review_record" --operation-file collect.json
```

collectには `expected-revision` は不要。実行開始時にhelperがrun IDとsnapshotを生成し、終了時snapshot/inputsとraw/receiptを記録する。callerから成功状態やsnapshotを入力しない。directのinputsはrepo Refのみ。新規v2の `validation.checks` は `{definition, receipt:Ref}` の配列で、collectが返したreceiptを参照する。従来の `status/argv/snapshot_id` の手書きrowや古いrawの付け替えでは自動通過できない。

present/read時は既存parserで結果を再解析し、現在snapshot、定義、base側oracle、inputs、最新attemptとreceiptを照合する。失敗・中断・receipt欠落から旧成功へ戻らない。同一checkの成功をそのまま再利用でき、ACごとの再実行は不要。MEDIUM/HIGHの人間確認やshippingは、このdirect経路で省略しない。

以下は互換性を維持する **legacy v1** の形式・準備例であり、新規LOWの自動通過には使わない。

legacy v1 direct の `quality` は `{kind:"direct", review_requirement, reviews, validation}`。Controller が既存 policy と実際の実行結果から埋め、helper が結果/snapshot/参照の整合性を検査する。新しい test collector ではない。

| field | 構造 |
| --- | --- |
| review_requirement | `{fresh_count:0 または 1 または 2, policy:Oracle, reason}`。人数は runtime の既存 matrix で決める |
| reviews | `{id, kind:"self" または "fresh", status, snapshot_id, evidence:[Ref,...]}` 配列。fresh_count=0 は self 1件、1/2 は異なる ID の fresh を指定件数 |
| validation | `{requirement:"required" または "not_applicable", reason, evidence:[Ref,...], checks:[...]}` |
| checks | `{id, argv:[string,...], status, snapshot_id, evidence:[Ref,...]}`。required は1件以上、ID 重複不可。policy/実行入口に基づく必要な検証をすべて列挙 |

status は `passed` / `failed` / `unverified`。提示には必要な全結果の passed と現在 snapshot の一致が必要。`not_applicable` は実行対象 validation がない根拠の非空 reason/evidence と `checks:[]` を必要とし、挙動変更、環境不足、未実行、失敗には使わない。docs 等に代替検証があれば required にする。direct の CI 履歴は空で、CI 委譲 shipping は正式 workflow へ移る。

Ref/Oracle は上記 schema を使い、direct の `repo` root は scope.repository、`workflow` root は **record file の親 directory**。外部の runtime policy はその directory にコピーし、Oracle.locator に元の出典/節を記録する。コピーと検証/review log の実 hash は `sha256sum FILE` 等で求める。任意絶対 path や symlink を Ref に入れない。保存 record 自体を quality の証跡へ入れると更新で失効するため、独立した証跡を使う。

direct の準備例（変更内容と実際の証跡を用意してから実行）:

```sh
review_repo=$(git rev-parse --show-toplevel)
change_id=my-change
review_record=$(git rev-parse --path-format=absolute --git-path "human-review/$change_id.json")
mkdir -p "$(dirname "$review_record")"
# 適用した runtime の policy と実行/review log を record の親へ保存する。
# base_commit と allowlist.json は変更対象の固定値を用意する。
python3 ~/.agents/workflows/software_delivery/scripts/review_snapshot.py --repo "$review_repo" --base-commit "$base_commit" --allowlist-json "$(cat allowlist.json)" --source worktree --output "$(dirname "$review_record")/$change_id-snapshot.json"
```

返された `review_snapshot_id` と、その対象で実施済みの review/validation を `quality.json` に記録する。上記 assessment 形式を `assessment.json` に保存し、operation を組み立てる:

```sh
python3 - "$review_repo" "$change_id" "$base_commit" > present.json <<'PY'
import json, sys
from pathlib import Path
read = lambda name: json.loads(Path(name).read_text())
print(json.dumps(dict(action='present', scope=dict(id=sys.argv[2], repository=sys.argv[1]),
    target=dict(base_commit=sys.argv[3], allowlist=read('allowlist.json')),
    assessment=read('assessment.json'), quality=read('quality.json')), ensure_ascii=False))
PY
python3 ~/.agents/workflows/software_delivery/scripts/human_review.py --record "$review_record" --operation-file present.json --expected-revision 0
```

### 提示、停止、回答、再検査

1. 必須 AI review/local validation 成功後に present を実行する。v2 LOWでpassedなら回答待ち・stop・resumeなしで進む。それ以外は返された `prompt` と presentation_id をユーザーへ提示する。出力は route/status/presentation_id/reason/prompt。pending は **exit 1 でも提示の保存成功**であり、自動再試行しない。workflow は `USER_DECISION_REQUIRED` へ停止し元 phase を stopped_from に保持する。提示前に shipping 認可や index equality は要求しない。
2. 現在の提示へのユーザー回答が来たら、上記 respond/revoke operation を実引用で作り、最新 revision で記録する。全対象の approve_current は exit 0。部分回答は他 card を承認しない。request_change は実装変更へ戻し、revoke は承認を撤回する。いずれも同じ提示への再承認では解消せず、新提示が必要。
3. workflow の respond 成功は停止状態を自動解除しない。`workflow_state.py resume --context PATH --expected-revision N` で元 phase を復元し、次の `check-gates` と state 遷移を実施する。完了後の revoke は同じ CAS 内で停止する。`LOCAL_VERIFICATION` への入口には承認を要求しないが、`LOCAL_COMPLETE` / `COMMIT` 以降、resume、直接 mutation、cleanup は現在のriskに応じた通過条件を再検査する。
4. 操作ファイルなしの `human_review.py --context PATH` / `--record PATH` は read-only。現在の対象に passed なら exit 0、pending/stale/blocked は exit 1、不正入力・検証例外は exit 2。完了直前に成功を確認する。`E_HUMAN_REVIEW_REQUIRED` / `E_HUMAN_REVIEW_STALE` / `E_HUMAN_REVIEW_RESPONSE` / `E_HUMAN_REVIEW_SCHEMA` は不足・失効・回答・schema の診断で、手書き gate の passed は代替にならない。

approval の basis は scope/target/assessment/quality/ci_history。判断・検証前提・実 Ref hash、workflow の contract/review/local receipt が変われば再判定・再提示する。回答、presentation ID、record/context revision、shipping 認可を basis に入れず、承認追記で既存の AI review/validation を失効させない。

承認済み CI 委譲が残る提示は `ci_pending:true` と CI 未完を明示する。予定済み CI 成功だけなら承認を反復しない。現在 contract/snapshot の失敗 receipt と後続 attempt のある未完了 attempt は履歴へ固定し、失敗/放棄後の成功で旧承認を復活させない。最新未完了は pending として `MR_READY` を拒否する。

export は最新承認 record を `workflow/human-review.json`、現在判断の参照と CI 履歴の start/失敗 receipt/raw/後続 start を保持する。元 root を読まず保持 root で検査し、cleanup では live record・履歴とも一致させる。撤回後に再承認した場合は、新 directory へ export して検査後に canonical `evidence/cleanup` bundle を更新してから resume する。worktree 削除後の再 export に旧 bundle を使うため、先に旧 bundle を失わない。旧 workflow は読取/停止/修復可能だが、次の完了/出荷/削除で承認不足を拒否する。


## 明示された merge の一つの入口

`ship-change` は MR_READY で止め、merge の権限を含まない。その後にユーザーがmergeを明示依頼した時だけ、次を使う。

```sh
python3 ~/.agents/workflows/software_delivery/scripts/workflow_merge.py --context PATH --mr IID --sha FULL_SHA --authorize MERGE
```

`--authorize MERGE` を省けば外部GETだけの検査となる（最新CI receiptはローカル保存する）。helperは固定host/projectのproject設定を一回取得し、`only_allow_merge_if_pipeline_succeeds:true` と `allow_merge_on_skipped_pipeline:false` を必須にする。未設定・欠落・取得失敗ではmergeせず、設定を自動変更しない。MR/source/target branch、shipping.commitとlive HEAD/pipeline、既存のreview/receipt/human gateを再検査し、最終pipeline statusもsuccessの場合だけSHAを固定してmergeする。失敗・証拠不足ではPUTを呼ばず、不明なAPI結果を自動再試行しない。

この境界は正式CLIに対する強制であり、GitLab UI/raw glabや同権限writerを制限しない。最終GET後のCI再実行はGitLabの既存pipeline必須条件に委ねる。全経路のharness証跡強制には別途branch protectionが必要で、API flagの確認をserver内部の原子性の実証とは呼ばない。現repositoryでは `.gitlab-ci.yml` の `harness` が既存三suiteを実行する。出荷時はその対象SHAの成功を既存 `gitlab_ci` checkへ登録する。remote実行前に成功と報告しない。
