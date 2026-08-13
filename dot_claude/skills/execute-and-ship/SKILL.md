---
name: execute-and-ship
description: review 済みの実装計画を実行し、そのまま commit・push・MR・in-scope CI まで続けて MR ready で止まる合成 phase。ユーザーが実行方法としてこの合成を明示選択した時にだけ起動する。local verification で止めたい場合は execute-plan、既に local 完成している変更の出荷だけなら ship-change を使い、この合成は使わない。
---

# Execute and Ship

`execute-plan` と `ship-change` を続けて実行する合成 phase。review 済み plan（または review 済み short-path task）に対して、ユーザーが**この合成を明示選択した時だけ**使う。

```text
execute-plan → ship-change
```

## 認可

dispatch の前に `context.json` へ `shipping_authorized: true` を記録する。これは **bounded な commit / push / MR / in-scope CI ループに対する包括認可**であって、それ以外の外部操作への認可ではない。認可が記録されていなければ実行しない。

## 進め方

1. まず `execute-plan` を、その直列 TDD・final review・snapshot・local verification の gate 付きで実行する（契約は `~/.claude/skills/execute-plan/references/task-execution.md`）。**実行中は commit しない。**
2. `LOCAL_COMPLETE` が一致したら、**shipping の可否を改めて質問せず** `ship-change` へ handoff する。`ship-change` は evidence を再検証し、sanitize gate と snapshot equality gate を通してから MR ready まで進む（契約は `~/.claude/skills/ship-change/references/shipping.md`）。
3. 各 phase の resume は最初の未完了 gate から行い、完了済みの外部 write を重複させない。
4. `LOCAL_COMPLETE` → shipping の内部境界では session 引き継ぎ（`handoff` skill）を提案しない。
5. MR ready を報告する時は session 引き継ぎ（`handoff` skill、既定 new-session）の要否を評価する。基準は `~/.claude/skills/product-discovery/references/session-handoff.md`。

## この phase が行わないこと

discovery と planning を含まない（未確定の要求は `product-discovery` へ、plan 作成は `implementation-planning` へ戻す）。**merge、post-merge cleanup、release、tag、production 変更、credential / 権限の変更、scope 拡大は認可しない。** 認可の欠落、snapshot の変化、protected contract の判断、外部 CI / runner の失敗、evidence の不一致では停止する。
