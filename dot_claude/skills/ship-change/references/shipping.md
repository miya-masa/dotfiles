# shipping の契約

`ship-change` の運用契約。入力は `LOCAL_COMPLETE` の workflow（final review 通過 + local verification 済み）で、終端は **MR ready**。merge / release / tag は行わない。

- state と helper CLI: `~/.claude/skills/execute-plan/references/state-and-artifacts.md`
- 実行側の契約: `~/.claude/skills/execute-plan/references/task-execution.md`
- 起動体制と packet: `~/.claude/skills/product-discovery/references/roles.md`

## entry と resume の gate

entry と resume のたびに、`context.json`、固定した default branch と base、artifact revision、allowlist、review と verification の evidence、`review_snapshot_id`、記録済みの commit / remote / MR / CI status をすべて検証する。欠落・stale・矛盾・snapshot 不一致は停止する。

**resume では検証済みの commit / remote / MR evidence を再利用し、push と MR 作成を重複させない。**

## sanitize gate

staging や commit の前に、controller が repository status、intended な base / head、allowlist、staged tree を自分で検査する。新しい scanner を発明しない。汚染の疑いや evidence の不足は fail-closed（停止）で扱い、allowlist 外の dirty / staged path は拒否する。

送信対象の diff と MR/PR description 候補について、次を確認する。

- token、password、API key、credential
- `/home/<user>/...` などの内部 path
- 本番 / 社内 host、非公開 URL、顧客情報、社外秘
- ローカル専用の spec / plan / workflow artifact（`.aidocs/` 配下）への path や link

controller は承認を求める前に、MR/PR description 候補と送信対象の `git diff` をユーザーへ提示する。diff が長大なら、sanitize 判断に必要な要約、送信対象の範囲、完全な diff の参照方法を示す。判断材料を示さずに承認を求めない。`AskUserQuestion` で `sanitize OK / 修正が必要 / 中止` を確認し、`sanitize OK` 以外では push と MR/PR 作成を行わない。修正後は gate を再実行する。

## snapshot equality gate

1. **staging の直前**に `review_snapshot.py` を `--source worktree` で再計算し、preflight を確認する。
2. allowlist の path **だけ**を stage する。
3. staging の後に `--source index` で再計算する。
4. **commit の直前**に、間に何の変更も挟まずに `--source index` でもう一度再計算する。

review 時・verification 時・staged の identity が**厳密に等しい**ことを要求する。1 つでも不一致なら review と verification は無効化され、そこで停止して再実行する（`task-execution.md` の final review + local verification へ戻る）。allowlist 外の dirty / staged path は preflight が `shipping_blocked` を立てるので拒否する。

## commit / push / MR

equality gate を通ってから、**論理的に 1 つの commit** を作る。

- `conventional-commit` とリポジトリ規約に従う。英語・命令形・lowercase・末尾ピリオドなし、emoji / AI attribution / `Co-authored-by` なし、必要なら `BREAKING CHANGE:` footer。
- commit 対象と `git diff --cached`（および `--check`）を確認し、既存の未コミット変更を混ぜない。
- ローカル専用 spec / plan / artifact の path を commit message に含めない。
- commit と push の前に `git rev-parse --show-toplevel` で CWD を確認する。
- Worktrunk を使う場合は `wt step commit --dry-run` で候補 message を生成する（設定の `stage = "none"` を尊重する）。ユーザーの明示承認を得てから、承認済み message と**完全に同一**の内容で commit する。
- MR ルートでは `wt merge` を使わない。必要な場合だけ、承認済み hook を `wt hook pre-merge` で手動実行し、補助的に `wt list --full` で worktree・branch・CI 状態を確認する。

push はユーザーの明示許可後。記録済みの branch を push し、固定した Worktrunk default branch を target に MR を開く。forge の CLI（`gh` 等）とリポジトリの MR/PR template を使う。本文にはローカル spec の参照ではなく、目的・scope・主要変更・検証結果を要約する。

## in-scope CI

- forge skill / CLI で全 required job が終わるまで監視する（`ci-monitor`）。
- 失敗時はログを取得し、root cause を調べて**同じ review / verification / snapshot の gate を通した in-scope な実装修正だけ**を行い、再 push して再監視する。scope を広げない。
- 2 回の修正または同等の調査でも原因が絞れない場合は、別コンテキストの fresh `explorer` / `reviewer` に read-only 診断を委譲する（失敗ログ、試した修正、結果、関連 path を渡す）。仮説は検証してから採用する。
- 外部 service 障害、runner / cache / secret manager、再現困難な複数 system、acceptance 自体の矛盾、protected contract の変更が必要な場合は推測せずユーザー判断を得る。

CI 全 pass の evidence を確認してから終端を報告する。CI 未完了や未確認を「完了」と報告しない。

## この phase が行わないこと

merge、release、tag、production 変更、credential / 権限の変更、local merge による override、scope 拡大。未認可の shipping、snapshot / commit / remote / MR / CI evidence の不一致、外部 dirty state、protected contract の判断、外部起因の失敗では停止する。**ready な MR がこの phase の終端**で、後から実際に merge されたときにだけ `post-merge-cleanup` を明示的に案内する。
