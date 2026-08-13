---
name: systematic-debugging
description: 原因不明の不具合、テスト失敗、障害、性能劣化、予期しない挙動を再現し、証拠からroot causeと修正条件を確定する。原因調査、再現して、なぜ失敗するか、直す前に調べたいという依頼で使う。原因と修正が既に明確な変更には使わない。
---

# Systematic Debugging

controllerが症状と証拠を固定し、boundedな探索は`explorer`、競合仮説や難しいroot causeはnamed `debugging` agentへ委譲する。このskillではコードを変更しない。

## 診断dispatch

- Expected、Actual、発生条件、頻度、影響、最小の再現手順または失敗testをpacketへ固定する。
- 実行経路、最近の変更、正常な近接case、参照箇所の列挙など、問いが明確な事実収集は`explorer`へ渡す。
- 再現後も最初の逸脱点やroot causeが確定しない、競合仮説が残る、証拠が理解を否定する、並行/永続/分散状態に関係する、または異なる修正が2回失敗した場合は`debugging`へ証拠packetを渡す。
- 同じ仮説をeffortだけ上げて再試行しない。結果が症状と全証拠を説明し、競合仮説を反証し、impact scopeと回帰test条件を限定しているか検査する。

## 停止とhandoff

- controller自身で深いroot cause分析や推測修正を行わない。
- 再現や証拠が不足する場合は、製品不具合と観測不足を分け、不足証拠と次の判別手段を報告して止める。
- 診断briefはExpected/Actual、Reproduction、first divergence、Root cause、Evidence、Impact scope、Regression test条件、Fix constraints、Unknownsを含む。
- critical review条件に該当する診断だけを`reviewer`へ渡す。
- 修正も依頼されている場合は確定したbriefを`implementation-planning`へ渡し、診断を繰り返さない。

reviewの判定は`~/.codex/review-policy.md`に従う。
