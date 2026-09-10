---
name: systematic-debugging
description: 原因不明の不具合、テスト失敗、障害、性能劣化、予期しない挙動を再現し、証拠から根本原因と修正条件を確定する。原因調査、再現して、なぜ失敗するか、直す前に調べたいという依頼で使う。原因と修正が既に明確な変更には使わない。
---

# 体系的デバッグ

`controller` が症状と証拠を固定し、限定的な探索は直接行い、独立した広い探索だけ`explorer`、競合仮説や難しい根本原因は名前付き `debugging` agentへ委譲する。診断段階と debugging agent はコードを変更しない。

## 診断ディスパッチ

- `Expected`、`Actual`、発生条件、頻度、影響、最小の再現手順または失敗testをpacketへ固定する。
- 実行経路、最近の変更、正常な近接case、参照箇所の列挙など、問いが明確な事実収集は直接行う。独立した広い探索だけ`explorer`へ渡す。
- 再現後も最初の逸脱点や根本原因が確定しない、競合仮説が残る、証拠が理解を否定する、並行/永続/分散状態に関係する、または異なる修正が2回失敗した場合は`debugging`へ証拠packetを渡す。
- 同じ仮説をかける負荷だけ増やして再試行しない。結果が症状と全証拠を説明し、競合仮説を反証し、影響範囲と回帰test条件を限定しているか検査する。

## 停止と引き継ぎ

- 調査量と停止条件は共有 `~/.agents/workflows/software_delivery/references/effort-policy.md` に従う。専門診断が必要な競合仮説を推測修正で埋めない。
- 再現や証拠が不足する場合は、製品不具合と観測不足を分け、不足証拠と次の判別手段を報告して止める。
- 診断briefは`Expected`/`Actual`、`Reproduction`、`first divergence`、`Root cause`、`Evidence`、`Impact scope`、`Regression test`条件、`Fix constraints`、`Unknowns`を含む。
- critical review条件に該当する診断だけを`reviewer`へ渡す。
- 修正も依頼され、確定した原因の修正が共通 effort-policy.md の直接完了条件を満たせば、診断 brief を確定して修正段階へ移り、controller が最小修正と targeted validation を行う。設計判断が残る場合は `product-discovery`、承認済み spec と実装順序の整理が必要なら `implementation-planning` へ渡し、診断を繰り返さない。

reviewの判定は`~/.codex/review-policy.md`に従う。
