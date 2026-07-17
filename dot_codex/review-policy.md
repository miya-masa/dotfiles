# Codex Artifact Review Policy

仕様、診断、計画、コードを、その成果物とリスクに必要な深さだけレビューする。
レビューは欠陥の発見を目的とし、一般論による防御追加や依頼外の再設計を目的にしない。

## Review tier

- **軽微**: 局所的で挙動が明白、かつ契約、security、状態、並行処理、永続データに影響しない。成果物の作成者がself-reviewする。
- **通常**: 複数ファイル、複数判断、または非自明な挙動を含む。実装文脈を与えすぎないread-only fresh reviewerが、該当レンズを1パスで確認する。
- **高リスク**: protected contract、不可逆処理、データ損失、認証認可、外部trust boundary、複雑な状態遷移・並行処理・resource lifecycleのいずれかに触れる。独立して確認できる場合に限り、次の2レンズから必要なものを最大2つに分ける。

高リスクのレンズは **Correctness / Adversarial** と **Contract / Product-fit / Simplicity** とする。常に2つ起動せず、該当しないレンズは省く。

## Artifact lenses

- **仕様brief**: Goal、Non-goals、Constraints、Done when、主要フロー、境界、不変条件、互換性、現実的な誤用・失敗が定義されているか。
- **診断brief**: Expected / Actual、再現、最初の逸脱点、root cause、競合仮説の反証、impact scope、回帰テスト条件、fix constraintsが証拠でつながるか。
- **実行計画**: decision-completeか、変更範囲と順序が最小か、依存、protected contract、検証、rollbackまたは安全な停止条件が明確か。
- **コード**: 要件と実際の実行経路に適合するか、回帰、契約、失敗時挙動、test gap、差分の複雑性に問題がないか。

## Adversarial thinking

攻撃だけでなく、正規操作の組合せ、前提を満たさない呼出し、順序変更、中断、部分失敗、retry、依存障害を検討する。指摘には守る対象または不変条件、実在する入口からの到達経路、具体的影響を示す。

想像上の利用環境、変更と無関係な攻撃面、所有境界の外での重複validation、「念のため」のfail-closed化は報告しない。到達可能性や影響を裏付けられなければ残リスクとして明示し、欠陥と断定しない。

## Product fit and simplicity

判断根拠は、適用されるAGENTS.mdやCONTRIBUTING、同一subsystemのproduction codeとtest、既存APIと観測済み挙動、一般的best practiceの順に確認する。

既存基準から外れる新規パターン、不要な抽象化、単発wrapper、投機的一般化、重複防御、失敗を隠すfallbackを確認する。短いこと自体や個人の好みは理由にせず、保守性、理解可能性、回帰リスクに実害がある場合だけ指摘する。一般的改善は今回の差分と直接関係し、具体的価値があるものだけFollow-upに分離し、自動実装しない。

## Finding gate and output

Findingは、変更範囲内または直接の下流影響であり、到達可能なシナリオ、具体的影響、コード・規約・再現結果の根拠、最小の修正または検証方法を示せる場合だけ報告する。style、nit、formatterやlintが扱う事項、pre-existing issue、依頼外の再設計は除外する。

- **Critical**: security、データ損失、重大な契約違反など。完了前に修正する。
- **Important**: 到達可能なbug、回帰、重要なtest gap、実害のある複雑性。完了前に修正する。
- **Follow-up**: 差分に直接関係する既存基準の改善案。非blocking、最大3件、ユーザー依頼なしに実装しない。

各Findingは severity、lens、対象箇所、シナリオと影響、根拠、最小修正を含める。actionable findingがなければ明言し、未確認範囲と残リスクを示す。controllerは結果を裏取りし、`今回修正 / Follow-up / 要判断`に分類する。
