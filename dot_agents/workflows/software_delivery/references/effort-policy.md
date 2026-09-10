# 必要十分な作業量

Codex / Claude 共通の調査・委譲・effort・検証基準。ソフトウェア作業の経路を選ぶ時に一度参照し、下位 skill で再読・全文転記しない。権限・domain 規約・runtime の review gate は各正本に従う。

## Controller と role の分担

Controller は薄く広く、goal・scope・依存・状態・dispatch・結果検査・統合を保持する。通常は fresh な上位モデル（Codex では bounded な通常判断に Sol、影響範囲・不確実性・重大な境界判断に Astra）で仕様検討・計画を decision-complete にし、下位モデルへ実装を渡し、fresh な上位モデルで独立 review する。Codexのfresh reviewに使うSol/Astraの選択は下記のreview方針に従う。仕様や計画が既に十分なら作り直さず、その証拠を再利用する。単純な局所変更で委譲の説明・回収コストが作業を上回る場合は Controller が直接完了する。

詳細な計画とは長文やコードの先書きではなく、AC・interface・依存順・owned paths・検証・stop conditions が揃い、実装者に product / architecture 判断を残さないこと。通常の実装を Controller が抱え込まず、主要判断と実装 context を分離する。review の適用・人数・lens は runtime の既存 review policy に従う。

| 作業 | Codex の起動選択 | Claude Code の profile |
|---|---|---|
| Controller | `gpt-6-astra` / `low` | 本体 `opus[1m]` / `low` |
| 限定探索 | `explorer`: `gpt-5.6-luna` / `low` | `explorer`: sonnet / low |
| 機械的・既知パターン実装 | `worker`: `gpt-5.6-luna` / `low` | `implementer`: sonnet / medium |
| decision-complete な通常実装 | `worker`: `gpt-5.6-luna` / `max` | `implementer`: sonnet / medium |
| 実装固有の推論が難しい | `worker`: `gpt-5.6-terra` / `high` | `implementer-high`: opus / high |
| bounded な仕様・計画・診断 | `specification` / `planning` / `debugging`: `gpt-5.6-sol` / `high` | `deliberator`: opus / high |
| 重大な境界判断・難しい診断 | `specification` / `planning` / `debugging`: `gpt-6-astra` / `high` | `deliberator`: opus / high |
| fresh review（normal） | `reviewer`: `gpt-5.6-sol` / `high` を基本とし、Controllerが影響範囲・不確実性から `gpt-6-astra` / `high` を選択 | `reviewer`: opus / high |
| fresh review（high / independent-risk） | `reviewer`: `gpt-6-astra` / `high`、人数はreview matrixの既存値 | `reviewer`: opus / high |

Codex の controller は `gpt-6-astra` / `low` を維持し、roleごとの指定を受け取れない場合の fallback は `gpt-5.6-sol` / `medium` とする。fallback は重要な作業の判断に使わず、起動時の `model` / `reasoning_effort` 指定を優先する。`task-reviewer` は限定的な任意 preflight が必要な場合だけ Luna / low とし、fresh review の代替にしない。Terra/Luna は重大な境界判断や fresh review の代替にしない。Astra が必要と判断された仕事のfailureを理由に黙って降格しない。モデルの優位を名称だけで決めず、実taskの品質・再試行・latencyを見て選択を見直す。各taskでは性質に合う経路を選び、全段階を順番に実行せず、Solの後に定例のAstraを追加しない。

## 経路と context

- 要求・既存挙動・範囲・検証が明確、局所・可逆で protected contract / security / 複雑な状態に影響しない変更で、委譲コストが作業を上回る小変更は直接完了する。ファイル数で full workflow に上げず、調査・計画・agent・artifact を前処理にしない。実装変更の完了は [review-common.md](review-common.md) のrisk分類に従い、v2 LOWは人間待ちなし、MEDIUMはsummary、HIGHはboundaryの明示承認、v1 legacyは従来承認とする。直接経路の記録は [evidence-contract.md](evidence-contract.md#人間レビューの記録と操作) に従う。
- 実装判断が残れば依存・AC・検証の短い計画、要求や外部挙動・契約が未定なら discovery を使う。durable resume / shipping は既存 state workflow を使い、開始済み workflow の gate は保持する。
- 既に承認された範囲の可逆作業は続ける。証拠から決められず回答で outcome / scope / protected contract が変わる時だけ質問する。実装依頼は shipping の許可ではない。
- 調査は具体的な問いに必要な関連 code → test / 近接実装 → local docs を優先する。最新仕様・外部 API・既知 issue など local evidence で解けない問いだけ外部検索する。答え・根拠・影響範囲・次の検証が揃えば終了し、全 repository / 全 reference や解決済みの問いを読み直さない。
- 同じ controller の phase 継続は context と evidence path を使い、差分・未決だけ更新する。resume は state と参照証拠の鮮度を検査し、完了済み作業を繰り返さない。
- 委譲は並列化の実益または独立した専門 context がある時だけ。説明・回収・裏取りの方が重い場合は直接処理する。packet は問い・scope・AC・制約・証拠 path・完了条件と runtime 必須項目だけにし、履歴や巨大な仕様を貼り直さない。

## effort と昇格

effort は探索・検証への投入量であり、モデルの能力順位ではない。上のrole選択を品質下限とし、その仕事に対応する最も軽い設定から始め、品質条件が満たせない仕事だけ深める。同名でもモデル間で投入量・品質は異なる。

| effort | 根拠 |
|---|---|
| low | 明確な局所修正、既知パターン、機械的変更、限定探索 |
| medium | 通常開発、依存する複数変更、実装案の比較 |
| high | 難しい診断、証拠矛盾、重要な設計・移行、独立したリスク反証 |
| xhigh | high でも解けない高不確実性・重大判断。根拠を残す例外 |
| max | decision-complete な通常実装の Luna の通常設定。通常実装以外では high でも解けない高不確実性・重大判断に限る例外 |

実装が止まったら、まず計画不足と実装固有の難しさを分ける。AC・interface・境界の未決は `specification` / `planning`（Claude は `deliberator`）へ戻し、worker の昇格で隠さない。計画は decision-complete でもアルゴリズム・型制約・並行処理の推論が難しい時だけ上位 worker を選ぶ。

失敗は環境・権限・入力・推論に分類して対処する。追加 reasoning が有効な時だけ調査・effort・専門 agent を増やす。1 回の失敗で最大 effort にせず、異なる修正が 2 回失敗、競合仮説、境界拡大なら runtime の専門診断へ渡す。必須の独立 review を軽量 agent や自己申告で代替しない。

この段階運用の初期評価は、通常実装を10件程度対象に、完了率、再試行率、重大指摘の有無、所要時間を既存の作業記録と検証結果から軽く確認する。新しい計測機構は設けない。

設定可能な時点だけ指定する。Codex は session 起動時の設定、subagent は spawn の `model` / `reasoning_effort` を両方指定する（role TOML の pin は外す）。Claude Code は session の `--effort` / `effortLevel` と subagent frontmatter を区別し、Agent tool に effort override がなければ上表の native profile を選ぶ。tool に切替機能がなければ現設定内で探索を調整し、必要な次の起動で指定する。プロンプトを書いただけで runtime effort が変わったと報告しない。

## 検証

観測可能な不具合は failing evidence → 最小修正 → targeted validation。共有実装・境界・回帰の懸念に応じて module / integration / broader suite へ広げる。無関係な全 suite、実装を写すだけの test は既定にしない。

同じ snapshot・入力・環境の成功 evidence は再利用する。変更・失敗・未解決の懸念・repository の追加 check 要求がある時だけ該当検証を行う。正式 workflow の snapshot 無効化規則を守り、品質条件を満たせば完了する。実測していない速度・料金・品質改善を断定しない。
