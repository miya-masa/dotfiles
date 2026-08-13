---
name: ship-change
description: local に完成した変更を 1 つの commit・push・MR・in-scope CI まで出荷し、merge の手前で止まる時に使う。「MR を作って」「push して」「出荷して」「CI を見て」などで、ユーザーが ship-change を明示選択した後、または execute-and-ship の handoff として起動する。実装そのもの（execute-plan）や merge 後の後片付け（post-merge-cleanup）には使わない。
---

# Ship Change

`LOCAL_COMPLETE` の変更を **MR ready まで**出荷する phase。明示的な `ship-change` 選択、または shipping 認可を記録した `execute-and-ship` の handoff でのみ使う。入力は final review 通過 + local verification 済みであること。**通常の実装は shipping を認可しない。**

契約の詳細は [references/shipping.md](references/shipping.md)、state と helper CLI は `~/.claude/skills/execute-plan/references/state-and-artifacts.md` にある。

## entry と resume の gate

`context.json`、固定した default branch と base、artifact revision、allowlist、review / verification evidence、`review_snapshot_id`、記録済みの commit / remote / MR / CI status を entry と resume で検証する。欠落・stale・矛盾・snapshot 不一致は停止する。**resume では検証済み evidence を再利用し、push と MR 作成を重複させない。**

## sanitize gate

staging や commit の前に、controller が repository status、intended な base / head、allowlist、staged tree を検査する。新しい scanner を発明しない。汚染の疑いや evidence 不足は fail-closed で停止し、allowlist 外の dirty / staged path は拒否する。

secret・credential・内部 path・非公開 host・顧客情報・`.aidocs/` 配下の workflow artifact への参照を確認し、MR description 候補と送信対象 diff をユーザーへ提示してから `sanitize OK / 修正が必要 / 中止` を確認する。`sanitize OK` 以外では push も MR 作成もしない。

## snapshot equality gate

**staging の直前**に `review_snapshot.py` を再計算して preflight を確認し、allowlist の path だけを stage し、staging 後に index に対して再計算し、**commit の直前**に間へ何も挟まずもう一度 index に対して再計算する。review 時・verification 時・staged の identity が**厳密に一致**する時だけ進む。1 つでも不一致なら review と verification を無効化して停止し、`execute-plan` の final gate へ戻す。

## commit / push / MR / CI

equality gate を通ってから論理的に 1 つの commit を作り（`conventional-commit` に従い、ユーザー承認済み message と同一内容で）、記録済み branch を push し、固定 Worktrunk default branch を target に MR を開く。CI は全 required job を監視し、失敗時は同じ review / verification / snapshot gate を通した **in-scope な修正だけ**を行って再 push する。外部 blocker（CI / runner 障害等）は推測せずユーザー判断へ上げる。

MR ready を報告する時、session 引き継ぎ（`handoff` skill、既定 new-session）の要否を評価する。基準は `~/.claude/skills/product-discovery/references/session-handoff.md`。

## この phase が行わないこと

**merge しない。** release、tag、production 変更、credential / 権限の変更、local merge による override、scope 拡大もしない。未認可の shipping、evidence 不一致、外部 dirty state、protected contract の判断では停止する。**ready な MR がこの phase の終端**で、後から実際に merge されたときにだけ `post-merge-cleanup` を明示的に案内する。
