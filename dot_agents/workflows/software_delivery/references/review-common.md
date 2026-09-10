# レビュー共通制約

spec / plan / 診断 brief / コードのどの成果物をレビューする時も共通で使う制約。レンズの定義（設計 / 実装後 / task / 診断）は [review-lenses.md](review-lenses.md) にある。

## 発動条件

レビューの深さは成果物のリスクで決める。

| リスク | 条件 | 体制 |
|---|---|---|
| 低 | 局所的で挙動が明白。契約、security、状態、並行処理、永続データに影響しない | 作成者の self-review |
| 中 | 低リスク条件を満たさない複数判断・非自明な挙動（ファイル数だけでは昇格しない） | fresh reviewer 1 体が該当レンズを 1 パス |
| 高 | protected contract（public API / DB schema / 認証認可 / 課金 / データ移行 / 外部契約）、不可逆処理、データ損失、外部 trust boundary、複雑な状態遷移・並行処理・resource lifecycle、または複数 module にまたがる設計変更 | fresh reviewer 1 体が該当レンズを担当。独立した security / failure analysis を統合すると見落とす具体的理由がある場合のみ 2 体に分け、lens は重複させない |

Codex の tier・人数・model・failure route は `~/.codex/review-policy.md` の canonical risk matrix が正本で、この表を重ねて適用しない。Claude の model / effort は runtime の roles.md に従う。

該当しないレンズは省く。常時多並列にしない。self-review を敵対的検証と呼ばない。

## 人間コードレビューの局所化

Codex / Claude の新規変更は evidence v2 の `assurance` を正本とする。判断は impact × assurance strength × residual risk に基づき、AI が迷ったかどうかだけで決めない。正式/直接経路とも [evidence-contract.md#人間レビューの記録と操作](evidence-contract.md#人間レビューの記録と操作) の helper で現在の品質を再検査する。risk 情報のない旧 v1 record は旧承認を維持し、LOW と推定しない。

| risk | 条件と人間が見る範囲 |
| --- | --- |
| LOW | 既存契約に沿う、影響が局所・可逆、十分な自動 oracle があり、追加 risk trigger・protected boundary がない。必須検証と既存 AI review policy が要求する self-check / fresh review が成功すれば自動完了。人間コードレビューと routine self-approval は不要 |
| MEDIUM | 変更挙動、重要な証跡、残余リスクを短く提示し、現在対象への承認を得る。人間固有の局所判断がある場合だけ該当 symbol と直接依存をカードにする。full diff 精読は要求しない |
| HIGH | 認証認可/security、課金、破壊・migration、公開互換性、rollout/rollback、大きな影響範囲等の具体的な境界を人間が確認する。境界ごとの scenario・impact・証跡・必要な symbol を提示し承認を必須にする。AI が判断に迷わなくても省略しない |

`adequate_oracle` が不明/false、未解決 blocker、必須検証不足では完了しない。未検証を人間承認で代替しない。LOW の自動通過も reviewer 数・必須検証・shipping 認可を免除しない。分類理由は既存 `reason` と一次根拠にまとめ、別の報告書へ複写しない。

| 残る問題 | 次の処理 |
| --- | --- |
| 実バグ (`bug`) | 修正と回帰検証 (`fix`) |
| test gap / 環境・権限不足 (`test_gap`, `environment`) | 必要な実行手段を確保し検証 (`verify`) |
| 技術的不一致 (`technical_disagreement`) | 証拠を集め診断 (`diagnose`) |
| 仕様・権限・状態境界の未決 (`specification`) | 仕様合意へ戻る (`specification`) |

既存の局所判断カードは、①今回の実装判断、②到達可能な scenario と影響、③規約で選べない複数の妥当案、④人間固有の保守運用知識が必要、⑤外部仕様/scopeを変えない、の五条件すべてを満たす場合だけ使う。HIGH の境界確認カードには五条件や複数案を要求せず、`boundary` と問い・コード範囲・scenario・impact・evidence・回答範囲を示す。存在しない選択肢を作らない。

MEDIUM/HIGH の現在提示への明示承認は helper で記録する。無回答、時間経過、assistant 宣言、過去の実装依頼から承認を推論しない。snapshot・判断・検証前提・証跡の変更や撤回で再検査し、単なる resume や予定済み CI 成功では承認を反復しない。旧 v1 の対象なし提示だけは従来の「セルフレビューで通してください」の承認を維持する。

分類・oracle の意味・引用の真正性は Controller の責務であり、schema の PASS を判断精度の証明としない。意味の照合は既存 reviewer の反例検討へ統合する。

## Risk に応じた検証の選択

共通経路は対象 repository の既存 test / lint / build の適用分だけ。以下は該当 trigger がある時だけ既存 check ID へ対応させる。同一 check が複数 trigger/AC を検証するなら一回の実行を共有し、AC ごとに suite を再実行しない。

| trigger | 追加する検証（該当するものだけ） |
| --- | --- |
| concurrency | Go の `-race`、または順序・競合・再試行を検出する適切な並行処理 test |
| persistence | 既存データ・migration・互換性・rollback の変更部分を確認 |
| api | 公開契約・後方互換性の contract test / 比較 |
| security | 拒否ケース・権限境界・bypass の検証 |
| integration | 実際の連携境界、または明示した制約内の契約/失敗ケース検証 |
| performance | 測定可能な要件がある時だけ、閾値を固定した benchmark |

trigger の見落としと検証の十分性は Controller と既存 reviewer が一次根拠で判断する。機械 gate は選定した check の存在と成功を検査し、ラベルだけから意味的な保証を主張しない。LOW に E2E/fuzz/scan/benchmark を一律追加しない。

## 敵対的検証の原則

fresh review は「確認」ではなく敵対的検証として運用する。成果物を作った本人とは別の reviewer が、「間違っているのでは」という前提であえて反証を試みることで品質を確かめる。

- **独立性**: 作成時の議論や implementer の報告を与えず、fresh context で起動する。渡すのは成果物・受入基準・一次証拠の場所だけで、作者の会話や採用案を正当化する説明は渡さない。
- **役割づけ**: 起動依頼で「レビュー」ではなく「反証を試みる」役割を明示する。
- **反例**: AC・実装・test がすべて PASS でも要求に反する具体例（仕様漏れ、弱い assertion、test blind spot、共有した仮定、negative case 欠落）を試し、既存 check が検出するか照合する。見つからなければ一行で終了し、別 agent・長大な analysis を追加しない。
- **接地**: 反証は一次情報（spec 本文、実コード、実行結果、明文化された規約）に基づいて裏取りする。印象や一般論で指摘しない。
- **判定形式**: 指摘には深刻度、根拠、確度を付ける。全体判定は `反証成立 / 条件付きで成立 / 反証できず` とする。

敵対的検証は健全な成果物にも指摘を出す（過剰指摘）。採否は採用判定で controller と人間が行い、指摘を無条件に採用しない。

## 全 reviewer 共通の制約

**絞り込みは二段構え**にする。reviewer 側に「重大なものだけ報告せよ」と指示すると報告が実際に減る（言われたとおり保守的になる）ため、**足切りは reviewer に課さず、controller の採用判定に集約する**。

起動依頼に次を含める。

1. 役割は反証。成果物が正しいことの確認ではなく、間違っている前提で反証を試みる。
2. Finding gate（Claude Code は `~/.claude/agents/reviewer.md`、Codex は `~/.codex/review-policy.md` に定義）を通る問題は、severity や確度で自主的に落とさず報告する。確度は各指摘に添える（低くてよい）。
3. 割り当てられたレンズだけを担当し、重複を避ける。
4. read-only で調査し、変更しない。
5. 末尾に `反証を試みたが壊せなかった点`、未確認範囲、残リスクを書く。

## 採用判定

reviewer は足切りせずに出す設計なので、**絞り込みはここが本番**。controller が全指摘を一次情報（spec 本文 / diff / コード / 実行結果）で裏取りし、次に分類する。

- **今回修正**: 実害が明確で、修正コストが正当。
- **見送り（根拠付き）**: 確度が低い、実害が軽微、YAGNI、pre-existing、スコープ外など。**根拠を1行で書く**（黙って捨てない）。
- **要判断**: protected contract や追加スコープなど、ユーザー判断が必要。

裏取りせずに採用も却下もしない。reviewer が確度「低」で出した指摘も、controller が読んで実害を確認できれば採用してよい（確度は reviewer の自己申告であって判定ではない）。採否は controller が決め、ユーザーが覆せる。技術根拠のない同意や盲従はしない。

- **severity と verdict は自己申告**: reviewer の severity・verdict は自己申告であり、controller が裏取りした後の分類が優先する。severity の維持・変更は controller の裁量とし、変更したら根拠を1行残す。
- **approve の基準は完璧さではなく改善**: 変更が全体を確実に良くし既存の規約に沿うなら、「自分ならこう書く」という差だけで gate を止めず見送りへ回す。
- **runtime の停止基準に該当する指摘を見送らない**: runtime の review 契約が完了前の修正または未解決時の停止を定めた severity（およびそれより重い severity）の指摘は、見送りに分類しない（Claude: execute-plan/SKILL.md:42, task-execution.md:89 / Codex: review-policy.md:24-25）。
  - 修正するなら今回修正とし、見送ると判断した場合だけ controller 単独で決めず要判断へ上げる。
  - 該当性は裏取り後に controller が確定した severity で判定する。実害が軽微という理由だけで severity を下げて該当から外さない。
  - 裏取りで指摘の事実前提そのものが崩れた場合はこの限りでなく、根拠を添えて見送ってよい。
- **gate 通過の3分岐**:
  - 要判断が1件以上残る場合、final review では `USER_DECISION_REQUIRED`、spec / plan review ではユーザー判断を仰ぐまで gate を通さない。
  - 要判断がゼロで今回修正が残る場合、final review では `CHANGES_REQUIRED`、spec / plan review では反映して再 review する。
  - どちらもゼロなら finding 側の gate は通過する（final review は `APPROVED`）。spec review ではこれは finding の解消のみを指し、spec-and-plan.md:28 のユーザー明示承認要件を置き換えない。
- **verdict の3値は final review 専用**: `APPROVED` / `CHANGES_REQUIRED` / `USER_DECISION_REQUIRED` は final review にのみ用いる。spec / plan review では同じ判定を gate 通過可否として適用し、3値を持ち込まない（reviewer が verdict を返すこと自体は妨げない）。
- **分類語の写像**: spec / plan review が使う `採用 / 却下（根拠付き）/ 要ユーザー判断` は、それぞれ `今回修正 / 見送り（根拠付き）/ 要判断` と同義である。

`未検証事項` は Finding とは別に扱い、確認が安ければ確認し、高ければ残リスクとして報告に載せる。
