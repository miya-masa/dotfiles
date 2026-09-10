# Codex Artifact Review Policy

reviewは差分の欠陥発見に必要な深さだけ行い、一般論による防御追加や依頼外の再設計を目的にしない。

model / effortは共通 `~/.agents/workflows/software_delivery/references/effort-policy.md` の選択表に従う。fresh reviewはnormalでは `gpt-5.6-sol` / `high`を基本とし、影響範囲・不確実性からControllerが `gpt-6-astra` / `high`を選択できる。high / independent-riskは `gpt-6-astra` / `high`を使い、人数は既存matrixの値を維持する。人数・lens・failure routeは以下だけを正本とする。

実装完了時の人間コードレビューは `~/.agents/workflows/software_delivery/references/review-common.md` を正本とする。v2 LOWは人間待ちなし、MEDIUMはsummary、HIGHはboundaryの明示承認を要求し、v1 legacyは従来承認を維持する。承認はこのAI review matrixの人数・lens・Finding gateを免除しない。

## Canonical risk matrix

この節だけをreview tier、人数、role/model、lens、failure routeの正本とする。phase文書はこのmatrixを参照し、複製しない。判定inputは`artifact_kind, normalized_trigger_set, dependency_cone, active_ac_set`、outputは`tier, reviewer_count, role, model, lenses, scope, failure_route`とする。triggerは下記の順に正規化し、入力順や反復で結果を変えない。

tierの表示名は`minor=軽微`、`normal=通常`、`high/independent-risk=高リスク`とする。named `reviewer`のcanonical lens集合は **Completeness / Correctness / Robustness / Security / Contract / Product-fit / Simplicity / Spec compliance / Feasibility** とする。

1. **独立Risk trigger**: security/trust boundary、認証認可、課金、データ損失、破壊的migration、不可逆操作、複雑な並行/分散状態のうち、攻撃者視点またはfailure analysisを他lensへ統合すると独立性を損なうもの。`independent-risk`、fresh `gpt-6-astra` / `high` reviewer 2体、相互に重複しないlens。failureはstopまたはnarrow redispatch。
2. **その他high-risk trigger**: 公開API/wire format、永続データ/migration/後方互換性、複雑なretry/idempotency/transaction/cache、可用性、重大なfailure recovery、plan逸脱。`high`、fresh `gpt-6-astra` / `high` reviewer 1体、該当lens最大2つ。failureはstopまたはnarrow redispatch。
3. **minorの全条件**: 局所的、可逆、挙動と検証が明白、protected contract/security/状態/並行処理/永続データへ影響しない。`minor`、reviewer 0、Controller self-checkとfocused validation。
4. **上記以外**: `normal`、fresh `gpt-5.6-sol` / `high` reviewer 1体を基本とし、影響範囲・不確実性からControllerが fresh `gpt-6-astra` / `high`を選択できる。artifact別lens最大2つ。failureはstopまたはnarrow redispatch。

triggerの有無またはminor全条件を一次証拠から判定できない場合はminorへ落とさず、停止するか該当するSol/Astra specialistへ再分類する。通常riskの独立reviewは品質と再現性を保つ既定gateであり、Sol reviewの後に定例のAstra reviewを追加せず、phase名を理由に同じsnapshotへtask reviewとfinal reviewを重複させない。

### Artifact lens

- **仕様brief**: Goal、Non-goals、Constraints、normative behavior、状態/境界/不変条件、acceptance criteria、compatibility、未決事項。
- **診断brief**: Expected/Actual、再現、first divergence、root cause、競合仮説の反証、impact、回帰test条件、fix constraints。
- **実行計画**: 推奨案の根拠、依存順、各completion criteria、protected contract、test、該当するrollout/migration/rollback/observability。
- **コード**: 要件と実在する入口、外部挙動、security、data integrity、compatibility、failure/recovery、concurrency/retry/idempotency、test gap、差分の複雑性。

artifact別の候補は、仕様brief=`Completeness / Product-fit / Simplicity / Security`、診断brief=`Correctness / Robustness`、実行計画=`Spec compliance / Feasibility / Simplicity`、コード=`Correctness / Robustness / Security / Contract / Simplicity`とする。1 reviewerあたり最大2 lensとし、独立Risk reviewer間ではlensを重複させない。closure review範囲は`spec-and-plan.md`を参照する。

## Finding gate

Findingは、変更範囲または直接の下流影響で、既存入口から到達可能なscenario、具体的impact、一次証拠、最小修正または検証方法が揃う場合だけ報告する。根拠不足は`未検証事項`へ分ける。

- **Critical**: security、データ損失/破損、重大な契約違反や可用性障害。完了前に修正する。
- **Important**: 到達可能なbug、回帰、重要なtest gap、failure recovery欠陥。完了前に修正する。
- **Follow-up**: 今回の差分に直接関係する具体的改善。non-blocking、最大3件、自動実装しない。

style/nit、formatter/lint対象、根拠のない仮説、pre-existing issue、依頼外の再設計はFindingにしない。ただしspec reviewのSimplicity lensが示す既存機構での代替（同じoutcomeをより小さい変更で得る案）は「依頼外の再設計」に当たらず報告してよい（final reviewや他lensには広げない）。判断根拠は適用指示、一次仕様、production code/test、再現結果、実データ、一般的best practiceの順に置く。
