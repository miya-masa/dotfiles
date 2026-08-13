# Codex Artifact Review Policy

reviewは差分の欠陥発見に必要な深さだけ行い、一般論による防御追加や依頼外の再設計を目的にしない。

## Risk tier

- **軽微**: 局所的で挙動と検証が明白、かつ契約、security、状態、並行処理、永続データに影響しない。作者のself-checkとfocused validationで完了できる。
- **通常**: 複数fileまたは非自明な挙動だが、下記のcritical triggerを含まない。controllerが成果物、直接影響、test結果を検査する。独立判断が有益な場合だけfresh reviewを使う。
- **高リスク**: security/trust boundary、公開API/wire format、永続データ/migration/後方互換性、認証認可、複雑な並行処理/retry/idempotency/transaction/cache/分散状態、データ損失/可用性、不可逆操作、重大なfailure recovery、plan逸脱のいずれか。named `reviewer`を使う。

## Artifact lens

- **仕様brief**: Goal、Non-goals、Constraints、normative behavior、状態/境界/不変条件、acceptance criteria、compatibility、未決事項。
- **診断brief**: Expected/Actual、再現、first divergence、root cause、競合仮説の反証、impact、回帰test条件、fix constraints。
- **実行計画**: 推奨案の根拠、依存順、各completion criteria、protected contract、test、該当するrollout/migration/rollback/observability。
- **コード**: 要件と実在する入口、外部挙動、security、data integrity、compatibility、failure/recovery、concurrency/retry/idempotency、test gap、差分の複雑性。

高リスクでは該当する **Correctness / Robustness / Security** または **Contract / Product-fit / Simplicity** のlensだけを選び、最大2つまでとする。

## Finding gate

Findingは、変更範囲または直接の下流影響で、既存入口から到達可能なscenario、具体的impact、一次証拠、最小修正または検証方法が揃う場合だけ報告する。根拠不足は`未検証事項`へ分ける。

- **Critical**: security、データ損失/破損、重大な契約違反や可用性障害。完了前に修正する。
- **Important**: 到達可能なbug、回帰、重要なtest gap、failure recovery欠陥。完了前に修正する。
- **Follow-up**: 今回の差分に直接関係する具体的改善。non-blocking、最大3件、自動実装しない。

style/nit、formatter/lint対象、根拠のない仮説、pre-existing issue、依頼外の再設計はFindingにしない。判断根拠は適用指示、一次仕様、production code/test、再現結果、実データ、一般的best practiceの順に置く。
