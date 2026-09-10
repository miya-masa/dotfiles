---
name: implementation-planning
description: 承認済み spec を、実装者が追加判断なく実行できる review 済みの実装計画へ変換する時に使う。「計画を立てて」「plan を作って」「どう進めるか整理して」「タスクに分割して」などで、spec 承認後の複数ファイル変更・設計境界・依存順・検証手順を決める場面で起動。未確定の product 判断（product-discovery）や実装そのもの（execute-plan）には使わない。
---

# Implementation Planning

明示承認済みの spec と evidence **だけ**を入力に、implementer が追加判断なく実行できる最小の plan を作る phase。通常は `deliberator`（`task_kind=planning`）が plan を検討し、controller が証拠・AC・実装可能性を検査してartifactへ統合する。既存決定の機械的な転記だけなら直接行い、必要な fresh `reviewer` が反証する。

契約の詳細は `~/.claude/skills/product-discovery/references/spec-and-plan.md`、起動体制と packet は `~/.claude/skills/product-discovery/references/roles.md` にある。

## 入口 gate

`context.json`、`spec.md`、spec review の結果を検証する。scope 内の未決事項、normative な gap、**spec の明示承認が記録されていない**場合は計画しない（`product-discovery` へ戻す）。short path の task artifact や未承認 spec を入力にしない。

`product-discovery` が spec・plan・実行方法の二択を 1 回の提示にまとめ、選択が `context.json` に記録済みなら、この phase を改めて起動せず `execute-plan` / `execute-and-ship` へ進む。

## plan の形

独立に検証できる vertical slice へ分解し、各 task に次の 9 項目を持たせる。

`goal` / `owned paths` / `deliverables` / `dependencies` / `interfaces` / `acceptance criteria` / `validation`（実行できる command と期待結果）/ `RED 理由`（実装前に focused test が失敗するべき理由）/ `stop conditions`

task 内部は所要時間で刻まず、goal・制約・完了条件を示す。手順は依存や失敗しやすい操作に限る。production code を丸ごと貼らず、共通の RED/GREEN/refactor 手順を各 task に複製しない。plan は `plan.md` として artifact に書き、product や architecture を作り直さない。

task の順序は依存順を最優先し、依存順が許す範囲でリスクの高い task を先頭に寄せる（早く壊れるほど手戻りが小さい）。依存順とリスク順が競合したら依存順が勝つ。「リスクが高い」は「未使用の外部 API / library / protocol に初めて触る」「validation command が実行可能かどうかが未実証」「acceptance criteria の成立性が技術的に未実証（性能目標、互換性など）」の 3 つに限り、該当しなければ従来どおり依存順のみで並べる。

このリスク判定を理由に差し戻すのは RED 理由や validation command を一意に決められない場合だけで、validation command が実行可能かどうかが未実証であること自体は差し戻し理由にしない（入口 gate の差し戻し条件は別に適用する）。一意に決められないと判明したら plan を作らず、入口 gate と同じ扱いで `product-discovery` へ戻る（plan review が skip される経路でも同様）。ただし実証してからでないと決められない場合は `product-discovery` では解けないので、戻さず、新しい task 種別も作らず「要判断」としてユーザーへ上げる。

## plan review gate

spec が十分なら plan review は要らない。次を**すべて**満たすなら review を skip し、判断理由を `context.json` に 1 行記録して handoff へ進む。

- spec が明示承認済みで、spec review に未解消の finding が無い。
- plan が spec の決定を task へ落としただけで、spec に無い設計判断を含まない。
- protected contract / architecture / 権限 / 永続化 / 分散状態に触れない。
- 各 task の acceptance criteria と検証 command が spec の AC から一意に導ける。
- task 間をまたぐ interface（シンボル名、シグネチャ、入出力の形）が plan 内で前後一貫している。

1 つでも欠けるか判断に迷うなら skip せず、完成 plan を fresh `reviewer` 1 体（model / effort は roles.md）に渡し、次の 2 点**だけ**を見る軽量レビューにする。

- **spec 整合性**: spec の要件が過不足なく plan に落ちているか（漏れ / spec に無い追加）。
- **実装可能性**: implementer が追加判断なく実行できるか（decision completeness / 依存順 / interface / 検証手順が成立するか）。

設計の良し悪しやコード品質は見ない（`execute-plan` の final review の領分）。finding は `採用 / 却下（根拠付き）/ 要ユーザー判断` で記録する。

- reviewer が normative な spec gap を見つけたら、plan で回避せず `product-discovery` へ戻る。
- protected contract、architecture、権限、永続化、分散状態の未決があれば停止する。
- 「適切にエラー処理」「必要に応じて」「TBD」のように実装時の設計判断が残る記述は、decision-complete でないので直す。

レビューを skip した場合は、skip 理由を `context.json` と報告に 1 行書く。

## 停止と handoff

Controller は plan 確定後、final review 前に `evidence.json` の registry・固定 check・実 hash を登録する。重要ACのoracleは既存spec/short taskに実装前に固定し、TASKS入口で対応checkとともにhash freezeする。risk triggerごとの検証選定は共有 `review-common.md` を参照する。schema は `~/.agents/workflows/software_delivery/references/evidence-contract.md` に従う。

review 通過後は「既存の実行依頼」に従う。実行依頼がなければ実装を開始せず、計画を報告して停止する。実行の終端が未選択の場合だけ `execute-plan` / `execute-and-ship` の二択を提示する。追加されるのは shipping 権限だけであり、scope は広がらない。選択を `context.json` に記録する。session 引き継ぎは context の問題がある場合だけ、`session-handoff.md` に従って提案する。

## この phase が行わないこと

コード変更、実装、commit / push / MR、merge、cleanup。spec に無い要件を plan で足さない。

### 既存の実行依頼

`spec-and-plan.md` の同名節を正本とする。明示済みの実装依頼を phase 名で聞き直さず、選択を記録して続ける。plan のみの依頼では停止し、shipping は明示依頼なしに認可しない。
