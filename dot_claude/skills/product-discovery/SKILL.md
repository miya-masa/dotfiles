---
name: product-discovery
description: 曖昧な機能アイデアや要求を対話で実装可能な spec へ整え、fresh review を通してユーザー承認まで持っていく時に使う。「〜を作りたい」「〜できるようにしたい」「要件を整理して」「仕様を詰めたい」「ブレストしたい」などで起動。既に確定した spec の実装計画（implementation-planning）や、不具合の原因調査（bugfix）には使わない。
---

# Product Discovery

曖昧な要求を、実装可能で review 済みの spec に変える phase。controller は高影響な product 判断だけをユーザーと合意し、**コードや plan を変更しない**。

契約の詳細は [references/spec-and-plan.md](references/spec-and-plan.md)、起動体制と packet は [references/roles.md](references/roles.md) にある。

## 開始時

`workflow_artifact.py init` で `.aidocs/workflows/<workflow-id>/` を作り、`context.json` を phase `DISCOVERY` で初期化する（CLI は `~/.claude/skills/execute-plan/references/state-and-artifacts.md`）。init に失敗したら workflow を始めない。以後 phase 遷移は `workflow_state.py transition --expected-revision N` だけで行い、報告や `progress.md` から進めない。

## 対話と探索

- Goal、利用者、Context、Constraints、scope、non-goal、主要方針、失敗条件を確認する。
- **repository から分かる事実（コード / test / docs / schema / public interface）をユーザーに尋ねない。** 広く探す必要がある調査は `explorer` に委譲し、読む先が分かっているファイルは controller が読む。
- 方針は 2〜3 案と trade-off で示す。未決事項は依存順に整理し、`AskUserQuestion` で **1 ターン 1 問**だけ聞く。回答ごとに evidence packet を更新し、事実 / 推論 / 仮定 / 未決の分離と Given/When/Then を検査する。
- spec は `spec.md` として artifact に書く。

## spec review gate

draft が揃ったら、結論を互いに共有しない fresh `reviewer` を独立に起動する。既定レンズは Completeness / Soundness / Operability / Simplicity で、protected contract / security / migration / 並行・分散状態に触れる時だけ Adversarial を追加する。該当しないレンズは省く（局所的で契約・状態・並行処理に影響しない spec は Completeness と Simplicity だけでよい）。finding は `採用 / 却下（根拠付き）/ 要ユーザー判断` に分類して `reviews/` に記録し、採用分を反映したら影響した scope だけ再 review する。normative な gap は spec 起こしへ戻す。

herdr 内（`HERDR_ENV=1` かつ `~/.claude/data/harness/cross-model-off` 未設置 かつ `command -v codex` 成立）では、この reviewer と同時に Codex（`herdr-delegate` の `agent` モード）を並走させる。入力は spec 全文のみ（0-context）。突き合わせ（finding 単位の一致/単独検出判定、検出元を明記した `採用 / 却下（根拠付き）/ 要ユーザー判断` への分類、両者の結論を互いに共有しない、体制の網羅性同士は比較しない）の詳細は [references/roles.md](references/roles.md) の「herdr 内クロスモデル並走」を参照。Codex が fail-soft で終わった場合、gate は Opus reviewer 側だけで成立し、warning を `reviews/` に残す。

## 停止と handoff

- **review 反映済み spec をユーザーが明示承認するまで、実装に進まない。** 承認は `context.json` と `progress.md` に記録する。
- 通常経路では、次の phase として `implementation-planning` **だけ**を案内する。plan が無い段階で実行方法の選択を提示しない。
- ただし spec review に未解消 finding が無く、plan が spec の決定を task へ落とすだけになる（＝ `implementation-planning` の plan review skip 条件をすべて満たす）と判断できるなら、spec・plan・実行方法の二択を **1 回の提示にまとめてよい**。phase 遷移を確認するためだけの往復を作らない。この場合も spec 承認と実行方法の選択は個別に `context.json` へ記録し、記録するまで実装を始めない。
- 調査だけの依頼なら、spec と未決事項を出して停止する。
- short path の条件（要求・外部挙動・AC・validation が明確、実装時に残る設計判断が無い、protected contract / migration / architecture 判断 / 複雑な並行処理なし、既存の未コミット変更を安全に分離できる）を**すべて**満たす時だけ、`tasks/01-short-path.md` を作り、そのまま `execute-plan` / `execute-and-ship` の二択を提示する（追加される shipping 権限を説明する）。**ファイル数では判断せず、preflight review も挟まない**（差分全体は `execute-plan` の final review が見る）。short path でも実行方法のユーザー選択を省略しない。
- planning を案内する時、session 引き継ぎ（`handoff` skill、既定 compact）の要否を評価する。基準は `~/.claude/skills/product-discovery/references/session-handoff.md`。

## この phase が行わないこと

コード変更、plan 作成、実装、commit / push / MR、merge、cleanup。実装権限も shipping 権限もここでは発生しない。
