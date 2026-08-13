---
name: execute-plan
description: review 済みの実装計画または short-path task を、直列 TDD の implementer・final review・local verification まで実行して停止する時に使う。ユーザーが実行方法として execute-plan を明示選択した後にだけ起動する。commit 以降の出荷（execute-and-ship / ship-change）や、計画そのものの作成（implementation-planning）には使わない。
---

# Execute Plan

review 済みの plan（または review 済み short-path task）を実行し、**`LOCAL_COMPLETE` で止まる** phase。ユーザーが `execute-plan`（または `execute-and-ship` の実行段）を明示選択した後にだけ使う。

実行契約は [references/task-execution.md](references/task-execution.md)、state と helper CLI は [references/state-and-artifacts.md](references/state-and-artifacts.md)、起動体制と packet は `~/.claude/skills/product-discovery/references/roles.md` にある。dispatch 前に読む。

## entry と resume の gate

`context.json`、承認済み spec / plan または short-path task、review 報告、task evidence、Git evidence を entry と**毎回の resume**で検証する。欠落・stale・矛盾・state より先行した evidence は implementer 起動前の hard stop。`progress.md` や報告から進捗を推論しない。

**resume は最初の未完了 gate から。完了済み task を再 dispatch せず、記録済みの外部 write を重複させない。**

## worktree gate

固定した default branch と base commit を要求する。worktree は `wt switch --create <branch> --base <default> --no-cd --format=json` でだけ作り、canonical な絶対 workdir を解決して全 packet と command に伝播する。hook の trust 承認要求、非 default の base、protected contract の判断では停止する。worktree から検証できないリポジトリでは worktree を作らず、その判断を明示して記録する。

## 直列実装と review

- 未完了 task ごとに fresh `implementer`（sonnet）を **plan 順に 1 体ずつ**起動する。packet は goal / acceptance criteria / owned paths / evidence / validation / 制約 / stop conditions / 絶対 workdir。implementer は commit / push / 外部書き込み / subagent 起動をしない。
- `RED → RED 理由の確認 → 最小の GREEN → GREEN 確認 → 限定的な refactor → GREEN 再確認` を要求し、各結果を記録する。TDD 例外は、承認済み plan が対象・RED 不可能な理由・代替 validation・reviewer 承認を明記している時だけ許す（実行時に発明しない）。
- **task ごとの review subagent は起動しない。** implementer の完了報告を受けたら、controller が focused validation の結果と owned paths の差分を確認して次の task へ進む。差分全体の敵対的検証は final review が 1 回だけ担うので、同じ差分を task 単位で二重に見ない。不足や逸脱は implementer へ差し戻す。同一 issue で 2 回修正に失敗したら read-only `explorer` の診断に切り替え、その修復条件だけを載せた packet で fresh implementer を起動する。

## final gate と handoff

全 task の実装と validation の後、fresh `reviewer` を fable xhigh（高リスク、または fix loop を要した逸脱があった場合は opus xhigh のレンズ並列）で起動し、固定 base からの差分全体を review させる。`review_snapshot.py` の ID に final review と local verification を束縛する。**snapshot が変われば両 gate とも無効**で、再実行する。

herdr 内（`HERDR_ENV=1` かつ `~/.claude/data/harness/cross-model-off` 未設置 かつ `command -v codex` 成立）では、この final reviewer と同時に Codex（`herdr-delegate` の `agent` モード）を並走させる。入力は diff + spec + plan で、同じ `review_snapshot.py` の ID に束縛する — **snapshot ID が変われば final review 本体と同様に Codex 側も再実行する**。突き合わせの詳細は `~/.claude/skills/product-discovery/references/roles.md` の「herdr 内クロスモデル並走」を参照。Codex が fail-soft で終わった場合、gate は fable reviewer 側だけで成立し、warning は `reviews/` に残した上で `ship-change` の既存経路で MR/PR description にも転記する。

`APPROVED` の後、記録済みの validation command と実際の入口を固定 workdir で実行し、失敗履歴と未検証範囲を `verification.md` に記録する。成功したら `LOCAL_COMPLETE` へ遷移し、次の任意 phase として `ship-change` だけを報告する。

`LOCAL_COMPLETE` を報告する時、session 引き継ぎ（`handoff` skill、既定 new-session）を提案する。基準は `~/.claude/skills/product-discovery/references/session-handoff.md`。

## この phase が行わないこと

**commit しない。** stage / push / MR の作成や変更 / merge / release / tag / その他の外部書き込みもしない。shipping 権限は `ship-change` または `execute-and-ship` の明示認可でのみ発生し、実装の完了から推論されない。scope 拡大、protected contract の判断、未解決の important finding では停止する。
