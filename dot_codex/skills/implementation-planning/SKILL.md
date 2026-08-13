---
name: implementation-planning
description: 承認済みspecを追加判断なく実行できる、review済みのvertical-slice実装計画へ変換する。仕様承認後の複数file変更、設計境界、依存順、検証手順の計画に使い、未確定のproduct判断や実装そのものには使わない。
---

# Implementation Planning

承認済みspecと証拠だけを入力に、named `planning` (Sol High, read-only)へ自己完結したpacketを渡し、Luna Max workerが追加判断なく実行できる最小planを作る。詳細な契約は[spec-and-plan.md](../../workflows/software_delivery/references/spec-and-plan.md)に置く。

## Gate and dispatch

- `context.json`、`spec.md`、review結果を検証し、scope内のopen decision、normative gap、未記録の明示spec承認があれば計画しない。
- Goal、acceptance criteria、owned paths、一次証拠、protected constraints、検証command、stop条件を含むbounded packetを渡す。short path taskや未承認specを入力にしない。
- planは独立検証可能なvertical sliceへ分解し、各taskにgoal、owned paths、成果物、依存、入出力interface、AC、検証command、期待するRED理由、stop条件を持たせる。task内部は2〜5分単位の固有actionとし、production code全文や共通TDD手順を貼らない。

## Review and stop

- specが十分ならplan reviewは不要。(1)specが明示承認済みでspec reviewに未解消findingが無い、(2)planがspecの決定をtaskへ落としただけでspecに無い設計判断を含まない、(3)protected contract/architecture/権限/永続化/分散状態に触れない、(4)各taskのACと検証commandがspecのACから一意に導ける、を**すべて**満たすならreviewをskipし、判断理由を`context.json`へ1行記録する。
- 1つでも欠けるか判断に迷うならskipせず、完成planを結論を共有しないfresh Sol High reviewer 1体へ渡し、**spec整合性**（specの要件が過不足なくplanに落ちているか）と**実装可能性**（追加判断なく実行できるか: decision completeness、依存順、interface、検証手順）だけをreviewさせる。設計品質やcode品質は見ない（`execute-plan`のfinal reviewの領分）。findingは採用/却下/ユーザー判断と理由を記録する。
- reviewerがnormativeなspec gapを見つけたらplanで補わず`product-discovery`へ戻る。protected contract、architecture、権限、永続化、分散状態の未決は停止する。
- review通過後（またはskip判定後）は実装を開始せず、`execute-plan`（local verificationで停止）または`execute-and-ship`（commit・push・MR・in-scope CIまで）の二択を提示し、追加されるshipping authorityを説明してユーザー選択を待つ。

reviewの判定は`~/.codex/review-policy.md`に従う。
