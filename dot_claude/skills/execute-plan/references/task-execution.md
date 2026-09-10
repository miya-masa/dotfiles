# task 実行の契約

`execute-plan` の運用契約。入力は承認済みの `spec.md` + `plan.md`、または承認済みの short-path task artifact で、終端は `LOCAL_COMPLETE`。**shipping 権限を与えず、commit も作らない。**

- state と helper CLI: [state-and-artifacts.md](state-and-artifacts.md)
- spec / plan の承認契約と short path: `~/.claude/skills/product-discovery/references/spec-and-plan.md`
- 起動体制と packet: `~/.claude/skills/product-discovery/references/roles.md`
- レンズ定義: `~/.agents/workflows/software_delivery/references/review-lenses.md`
- レビュー共通制約: `~/.agents/workflows/software_delivery/references/review-common.md`

## entry と resume の gate

dispatch の前に `workflow_state.py validate` で `context.json` を検証し、記録された phase、artifact revision、実行方法の選択、不変 identity（source root、固定 default branch、full base commit、artifact path）を確認する。plan review（skip 判定を記録した場合はその理由）が通過済みで、task の goal / acceptance criteria / owned paths / evidence / validation command / 制約 / stop conditions が読めることを確認する。

entry と resume のたびに、参照している artifact と Git evidence を実際に見る。worktree path と branch が記録どおりか、base が記録された full commit に解決するか、allowlist 外の変更を task の成果と取り違えていないかを確認する。欠落・stale・矛盾・不正形式・state より先行した artifact / Git 記録は、implementer を起動する前の hard stop。`progress.md`・報告・command 出力は evidence にすぎず、state authority は `context.json`。state 更新は compare-and-swap で行う。

**resume は最初の未完了 gate から。完了済み task を再 dispatch しない。**

- 実装が完了しているなら、未完了の final review だけを回す。
- final review が完了しているなら、未完了の verification だけを回す。
- 未完了の実装 task は、evidence を再検証してから改めて dispatch する。
- context の revision より新しい報告から「完了した gate」を推論しない。

## worktree gate

実行は workflow の default branch からのみ。記録した intended base と Worktrunk の default を比較し、非 default の base / branch は stop condition。実行方法の選択を記録した後に、次を実行する。

```text
wt switch --create <branch> --base <default> --no-cd --format=json
```

JSON を検証し、選ばれた worktree を実在する canonical な絶対 path に解決して `context.json` に保存する。以後すべての subagent packet と command の作業ディレクトリはその絶対 path を使う。project hook が trust 承認を求めたら停止してユーザーに聞く（`--yes` を足さない、hook を迂回しない）。fallback の worktree command（`git worktree` 等）は使わない。

- 着手前と各 gate の前に `git rev-parse --show-toplevel` で CWD が意図した worktree であることを確認する。
- `post-start` の copy hook（`wt step copy-ignored`）が完了し失敗していないことを確認するまで実装へ進まない。
- **worktree から検証できないリポジトリ**（chezmoi の source dir のように、ツールが固定 path を見るもの）では worktree を作らず、その判断を 1 行で明示して記録する。
- 既存の未コミット変更はユーザーの作業として扱い、明示依頼なしに戻さない。

## 直列 implementer

plan の順序どおり、**1 度に 1 task**。通常は fresh な `implementer` へ実装を渡し、委譲コストが作業を上回る明確な小変更だけ controller が直接実装する。計画不足は `deliberator`、計画が十分でも実装固有の推論が難しい場合は `implementer-high` を選ぶ。委譲では、task の goal、acceptance criteria、正確な owned paths、依存と evidence の path、validation command、制約、stop conditions、固定した絶対 workdir、現在の artifact revision を含む packet を渡す。implementer は owned paths の中に留まり、無関係なユーザーの変更を保全し、**commit / push / 外部書き込み / subagent 起動をしない**。

観測可能な挙動変更には次の順序を要求し、各結果を記録する。

```text
RED → 期待した RED 理由の確認 → 最小の GREEN → GREEN 確認
    → 必要な refactor を行った場合のみ再検証
```

RED test は実装前に**記録された理由で**失敗しなければならない。限定的な refactor は owned な変更の中で重複除去と命名改善だけを行い、挙動や将来向けの抽象化を追加しない。docs、生成物、純粋な設定など非挙動の task は、plan に対象・非挙動である理由・代替 validation command を記録して検証する。追加 reviewer 承認や形式的な RED は要求しない。挙動変更を非挙動と扱わない。

テストを skip / delete して通さない。テストの実行 command はプロジェクト側（CLAUDE.md / AGENTS.md / README / Makefile / CI config）の正規 command を使い、未確認の ad-hoc command を持ち込まない。

## task 完了判定と fix loop

**task ごとの review subagent は起動しない。** implementer は TDD の自己ループで検証済みで、差分全体の敵対的検証は final review が 1 回だけ担うので、同じ差分を task 単位で二重に見ない。

**完了通知を完了の証拠にしない。** 「Background task completed」が届いても implementer がまだ書いていることがある。真の完了は (a) 対象コミット / ファイルが実 FS に着地したこと、または (b) subagent transcript（`<session>/subagents/agent-*.jsonl`）の mtime が 90 秒静止したこと、で判定する。`TaskOutput` は teammate 型 implementer には効かない（`No task found`）ので、最終報告は transcript 末尾の assistant text から読む。

**git 状態の確認は `dangerouslyDisableSandbox: true` で行う。** sandbox 越しの `git log` が、実在しない hash と期待どおりのメッセージを持つ「幻のコミット」を返したことがある（実測で 2 回）。sandbox 内の `Monitor` で git を監視しない。Go の build / test / generate も GOCACHE が read-only で sandbox 内では落ちるので、その注意は packet に最初から書いて往復を減らす。

implementer が完了を報告し focused validation が通ったら、controller が次を自分で確認して次の task へ進む。

- acceptance criteria が満たされているか（一次証拠は validation の実行結果と owned paths の差分）
- owned paths の外を触っていないか、無関係なユーザーの変更を保全しているか
- 観測可能な挙動変更で `RED → GREEN` が記録されているか（または非挙動変更の理由と代替検証があるか）

不足や逸脱が見つかったら、正確なシナリオ・impact・一次証拠・最小の修正を添えて implementer へ差し戻し、focused validation を通してから次の task へ進む。

**同一 issue の失敗回数を数える。同じ issue で 2 回修正に失敗したら implementer のループを止め**、roles.md の複雑な read-only 診断へ委譲して root cause と修復条件を確定させる（それでも割れないなら `codex:codex-rescue`）。その後、その修復条件だけを載せた packet で fresh `implementer` を起動する。未解決の重大な逸脱、scope 拡大、protected contract の判断、信頼できない validation は workflow を停止する。

## final review、snapshot、local verification

Controller は共有 `~/.agents/workflows/software_delivery/references/evidence-contract.md` の phase 手順2–3を実施する。final review 前に `load_contract` で registry を検証し、review 後に file hash・contract hash・snapshot と AC 判定を `evidence.json.review` へ束縛する。`check-gates --to LOCAL_VERIFICATION` を通し、不足 check を `evidence-run` で収集する。共有 `~/.agents/workflows/software_delivery/references/review-common.md` と `human_review.py` の検査に従い、v2 LOWは人間待ちなし、MEDIUMはsummary、HIGHはboundaryの明示承認を要求し、v1 legacyは従来承認を維持する。shipping 認可済み composite の引き継ぎは同 reference の D1 に従う。

全 task の実装と focused validation が終わったら、共有 `review-common.md` のリスク基準を適用する。軽微なら controller の self-check、それ以外は必要な fresh `reviewer`（model / effort は roles.md）を起動する。固定した merge-base からの allowlist 済み差分全体を対象に、該当するレンズだけを使わせる。reviewer 0 の場合も同じ AC 表・verdict・snapshot を controller が記録し、review gate 自体は省略しない。 verdict は `APPROVED` / `CHANGES_REQUIRED` / `USER_DECISION_REQUIRED`。

不変の `review_snapshot_id` を snapshot helper で計算する。

```text
python ~/.agents/workflows/software_delivery/scripts/review_snapshot.py \
  --repo <worktree> --base-commit <full commit> \
  --allowlist-json '{"version":1,"paths":[...]}' \
  --source worktree --output <manifest path>
```

final review と local verification を同じ snapshot に束縛する。内容・mode・削除・allowlist・base・external-dirty preflight のいずれかが変われば ID が変わり、**両方の gate が無効化されて再実行が必要**になる。別の snapshot の報告を使い回さない。

`APPROVED` の後、同じ snapshot・入力・環境で取得済みの evidence を確認し、不足する validation command だけを固定した絶対 workdir で実行する。可能なら未確認の実際の入口（CLI / API / 画面 / メッセージ / デバイス）も 1 つ通す。mock だけで終えない。実行した正確な command、成功、失敗履歴、未検証の範囲を `verification.md` に記録する。実入口 evidence は一度取れば足り、「念のため」の再実行を積まない。失敗は所属する task / review / verification の gate へ戻し、gate の省略を正当化しない。

`verification.md` は正準見出し（行頭が `#` の行）2 種を持つ — 失敗履歴側の見出しに `失敗` または `Failure`、未検証範囲側の見出しに `未検証` / `未実施` / `未確認` のいずれかを含める。どちらか欠けると `LOCAL_VERIFICATION → LOCAL_COMPLETE`（および `→ COMMIT`）が `artifact lint failed` で rc=1 になり `context.json` は変わらない（検査の詳細は [state-and-artifacts.md](state-and-artifacts.md)）。

検証成功後、現在提示への明示承認と helper 検査成功を確認して snapshot を記録し、`LOCAL_COMPLETE` へ遷移する。**`execute-plan` の選択は local completion だけを意味する。commit しない。stage・push・MR の作成や変更・merge・release・tag・その他の外部書き込みもしない。** 結果を報告し、次の任意 phase として `ship-change` だけを示す。shipping 認可記録済みの `execute-and-ship` は、この handoff または共有 evidence contract の D1 による `LOCAL_VERIFICATION` handoff を使える。

## stop と recovery

非 default の base、未承認の Worktrunk hook、artifact / Git evidence の欠落や不整合、stale な revision、snapshot 不一致、未解決の important finding、protected contract や security の判断、scope 拡大、信頼できない validation では dispatch 前に停止する。worktree と artifact は調査のために残す。後で resume する時は記録された context と Git 状態を再検証し、完了済み task の履歴を保全し、最初の未完了 gate からだけ続ける。部分的に書かれたファイルや報告から進捗を推論しない。
