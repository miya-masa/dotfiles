---
name: execute-plan
description: review 済みの実装計画または short-path task を、必要な実装・risk-based final review・local verification まで実行して停止する時に使う。context.json に実行選択が記録済みの時だけ起動する（既存の明示的な実装依頼からの記録を含む）。commit 以降の出荷（execute-and-ship / ship-change）や、計画そのものの作成（implementation-planning）には使わない。
---

# Execute Plan

review 済みの plan（または review 済み short-path task）を実行し、**`LOCAL_COMPLETE` で止まる** phase。`context.json` に記録済みの execution choice がある時だけ使う。phase 名の選択でも、planning が既存の明示的な実装依頼から記録した選択でもよい。未承認 spec からは実装しない。

実行契約は [references/task-execution.md](references/task-execution.md)、state と helper CLI は [references/state-and-artifacts.md](references/state-and-artifacts.md)、起動体制と packet は `~/.claude/skills/product-discovery/references/roles.md` にある。dispatch 前に読む。

実行方法の選択は、planning の「既存の実行依頼」に従い明示された実装依頼から記録してよい。同じ権限を phase 名で再確認しない。記録前や未承認 spec からは実装を開始しない。

## entry と resume の gate

`context.json`、承認済み spec / plan または short-path task、review 報告、task evidence、Git evidence を entry と**毎回の resume**で検証する。欠落・stale・矛盾・state より先行した evidence は implementer 起動前の hard stop。`progress.md` や報告から進捗を推論しない。

**resume は最初の未完了 gate から。完了済み task を再 dispatch せず、記録済みの外部 write を重複させない。**

## worktree gate

固定した default branch と base commit を要求する。base を固定する前に `git fetch origin` し、`git log --oneline <default>..origin/<default>` が空であることを確認する（local の default が stale だと、既修正の CVE 再検出やクロスサービス非互換で CI が落ち、原因調査に時間を失う）。worktree は `wt switch --create <branch> --base <default> --no-cd --format=json` でだけ作り、canonical な絶対 workdir を解決して全 packet と command に伝播する。hook の trust 承認要求、非 default の base、protected contract の判断では停止する。worktree から検証できないリポジトリでは worktree を作らず、その判断を明示して記録する。

## 直列実装と review

- 未完了 task は plan 順に fresh `implementer` へ渡す。委譲コストが作業を上回る明確な小変更だけ controller が直接実装する。計画不足は `deliberator` へ戻し、計画が十分でも実装固有の推論が難しい時だけ `implementer-high` を選ぶ。packet は goal / acceptance criteria / owned paths / evidence / validation / 制約 / stop conditions / 絶対 workdir。implementer は commit / push / 外部書き込み / subagent 起動をしない。
- 観測可能な変更は `RED → RED 理由の確認 → 最小の GREEN → GREEN 確認` と結果を記録する。refactor は必要な場合だけ行い、変更後に再検証する。非挙動の docs・生成物・設定は理由と代替 validation を記録し、形式的な failing test や追加 reviewer 承認を要求しない。
- **task ごとの review subagent は起動しない。** implementer の完了報告を受けたら、controller が focused validation の結果と owned paths の差分を確認して次の task へ進む。差分全体の敵対的検証は final review が 1 回だけ担うので、同じ差分を task 単位で二重に見ない。不足や逸脱は implementer へ差し戻す。同一 issue で 2 回修正に失敗したら roles.md の複雑な read-only 診断に切り替え、その修復条件だけを載せた packet で fresh implementer を起動する。

## final gate と handoff

全 task の実装と validation の後、共有 `review-common.md` のリスク基準を適用し、必要な fresh `reviewer`（model / effort は roles.md）に固定 base からの差分全体を review させる。`review_snapshot.py` の ID に final review と local verification を束縛する。**snapshot が変われば両 gate とも無効**で、再実行する。

`reviews/final-review.md` は、品質 finding より前に **spec の全 AC を 1 行ずつ `SATISFIED / UNSATISFIED / UNVERIFIED`（理由付き）で列挙した表**から始める（short path では `tasks/01-short-path.md` の acceptance criteria を使う）。`UNSATISFIED` が 1 行でもあれば `APPROVED` にしない。`UNVERIFIED` は理由と予定 check があれば後続 verification 待ちとして許容し、receipt で解消する。Controller は共有契約の review binding・`evidence-run`・`check-gates` 手順を実施する。共有契約は `~/.agents/workflows/software_delivery/references/evidence-contract.md` を参照する。レンズ並列でも表は 1 つに統合する。**判定を書かずに「問題なし」で済ませない** — 過不足を見た結果なのか見ていないのかが後から区別できなくなる。`reviews/final-review.md` はこの AC 判定表を持つ **lint 対象の正本**で、過去ラウンドや cross-model 報告は別名で併存させてよく lint 対象にはならない。

クロスモデル確認をユーザーが明示依頼した時だけ、`~/.claude/skills/product-discovery/references/roles.md` の「herdr 内クロスモデル並走」に従う。端末環境だけを理由に追加 reviewer を起動しない。

`APPROVED` の後、同じ snapshot・入力・環境で取得済みの evidence を確認し、不足する validation command と実際の入口だけを固定 workdir で実行し、失敗履歴と未検証範囲を `verification.md` に記録する。v2 LOWは人間待ちなし、MEDIUMはsummary、HIGHはboundaryの明示承認を要求し、v1 legacyは従来承認を維持する。`check-gates --to LOCAL_COMPLETE` 成功後は次の任意 phaseとして `ship-change` だけを報告する。

`HERDR_ENV=1` の時は、人間へ結果を提示する直前に `nvim-review-open --base <固定した base>` を 1 回実行する。同じ workspace の nvim に `base..作業ツリー` の diffview を新しいタブで開き、その nvim ペインへフォーカスを移す（nvim が居なければペインを分割して起動する）。**差分を見せる先を用意するだけで、待ち方は risk 区分のまま**変えない。失敗したら 1 行報告して提示を続け、再試行やペインの後片付けをしない。

`LOCAL_COMPLETE` で context の問題または中断希望がある時だけ、session 引き継ぎ（`handoff` skill）を提案する。基準は `~/.claude/skills/product-discovery/references/session-handoff.md`。

## この phase が行わないこと

**commit しない。** stage / push / MR の作成や変更 / merge / release / tag / その他の外部書き込みもしない。shipping 権限は `ship-change` または `execute-and-ship` の明示認可でのみ発生し、実装の完了から推論されない。scope 拡大、protected contract の判断、未解決の important finding では停止する。
