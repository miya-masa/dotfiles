---
name: implementation-planning
description: 承認済み spec を、実装者が追加判断なく実行できる review 済みの実装計画へ変換する時に使う。「計画を立てて」「plan を作って」「どう進めるか整理して」「タスクに分割して」などで、spec 承認後の複数ファイル変更・設計境界・依存順・検証手順を決める場面で起動。未確定の product 判断（product-discovery）や実装そのもの（execute-plan）には使わない。
---

# Implementation Planning

明示承認済みの spec と evidence **だけ**を入力に、implementer が追加判断なく実行できる最小の plan を作る phase。controller が plan を書き、fresh `reviewer` が反証する。

契約の詳細は `~/.claude/skills/product-discovery/references/spec-and-plan.md`、起動体制と packet は `~/.claude/skills/product-discovery/references/roles.md` にある。

## 入口 gate

`context.json`、`spec.md`、spec review の結果を検証する。scope 内の未決事項、normative な gap、**spec の明示承認が記録されていない**場合は計画しない（`product-discovery` へ戻す）。short path の task artifact や未承認 spec を入力にしない。

`product-discovery` が spec・plan・実行方法の二択を 1 回の提示にまとめ、選択が `context.json` に記録済みなら、この phase を改めて起動せず `execute-plan` / `execute-and-ship` へ進む。

## plan の形

独立に検証できる vertical slice へ分解し、各 task に次の 9 項目を持たせる。

`goal` / `owned paths` / `deliverables` / `dependencies` / `interfaces` / `acceptance criteria` / `validation`（実行できる command と期待結果）/ `RED 理由`（実装前に focused test が失敗するべき理由）/ `stop conditions`

task 内部の action は 2〜5 分単位の固有手順にする。production code を丸ごと貼らず、共通の RED/GREEN/refactor 手順を各 task に複製しない。plan は `plan.md` として artifact に書き、product や architecture を作り直さない。

## plan review gate

spec が十分なら plan review は要らない。次を**すべて**満たすなら review を skip し、判断理由を `context.json` に 1 行記録して handoff へ進む。

- spec が明示承認済みで、spec review に未解消の finding が無い。
- plan が spec の決定を task へ落としただけで、spec に無い設計判断を含まない。
- protected contract / architecture / 権限 / 永続化 / 分散状態に触れない。
- 各 task の acceptance criteria と検証 command が spec の AC から一意に導ける。

1 つでも欠けるか判断に迷うなら skip せず、完成 plan を fresh `reviewer` 1 体（opus xhigh）に渡し、次の 2 点**だけ**を見る軽量レビューにする。

- **spec 整合性**: spec の要件が過不足なく plan に落ちているか（漏れ / spec に無い追加）。
- **実装可能性**: implementer が追加判断なく実行できるか（decision completeness / 依存順 / interface / 検証手順が成立するか）。

設計の良し悪しやコード品質は見ない（`execute-plan` の final review の領分）。finding は `採用 / 却下（根拠付き）/ 要ユーザー判断` で記録する。

- reviewer が normative な spec gap を見つけたら、plan で回避せず `product-discovery` へ戻る。
- protected contract、architecture、権限、永続化、分散状態の未決があれば停止する。
- 「適切にエラー処理」「必要に応じて」「TBD」のように実装時の設計判断が残る記述は、decision-complete でないので直す。

skip した場合は skip 理由を `context.json` と報告に 1 行書く。

## 停止と handoff

review 通過後（または skip 判定後）は**実装を開始せず**、次の二択を提示してユーザーの選択を待つ。

- `execute-plan`: task 実行・review・local verification まで行い、そこで止まる。
- `execute-and-ship`: 同じことをした上で、別途認可された commit / push / MR / in-scope CI まで続ける。

この選択が増やすのは **shipping 権限だけ**で、承認済み scope は広がらないことを説明する。選択を `context.json` に記録するまで実装を始めない。

選択を `context.json` に記録した直後、実装 dispatch の前に session 引き継ぎ（`handoff` skill、既定 new-session）を提案する。基準は `~/.claude/skills/product-discovery/references/session-handoff.md`。

## この phase が行わないこと

コード変更、実装、commit / push / MR、merge、cleanup。spec に無い要件を plan で足さない。
