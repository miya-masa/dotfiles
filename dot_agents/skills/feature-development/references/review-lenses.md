# レビューレンズ

feature-development の設計レビューと実装後レビューを、別コンテキストの fresh reviewer に分けて委譲するための雛形。role とモデルの選択は runtime の role config に任せる。

## 発動条件

次のいずれかに触れる場合に並列 fresh review を使う。

- public API / DB schema / 認証認可 / 課金 / データ移行 / 外部契約。
- 複数 module にまたがる新機能、設計変更、複雑な並行処理。

軽い変更は設計を controller が 1 パス、実装後を fresh reviewer 1 体で確認すればよい。常時多並列にしない。

## 全 reviewer 共通の制約

起動依頼に次を含める。

1. confidence 80 以上で、実際の実行経路または明文化された規約から裏取りできる問題だけ報告する。
2. Critical / Important のみ。nitpick、style、formatter/linter が捕捉する問題、pre-existing issue、変更外は除外する。
3. 実装量を増やす指摘には、安全性、互換性、データ整合性、法的要請などの正当性を添える。添えられなければ報告しない。
4. 割り当てられたレンズだけを担当し、重複を避ける。
5. read-only で調査し、変更しない。

## 設計 3 レンズ

各 reviewer に対象 spec と [analysis-techniques.md](analysis-techniques.md) を渡し、実装側の議論を与えない fresh context で確認させる。

| レンズ | 観点 |
|---|---|
| Completeness | 決定表、状態遷移、境界。未定義動作を探す |
| Soundness | 不変条件、敵対的思考、依存、時間軸。論理破綻と race を探す |
| Operability | 互換性、移行、rollback、観測性、test |

各 Gap に `v1 必須 / v1.x で可 / 将来拡張で十分` を付ける。

依頼例:

> 対象 spec `<path>` を Completeness レンズだけで fresh review してください。`analysis-techniques.md` の決定表、状態遷移、境界を使い、未定義動作を探してください。共通制約に従い、各 Gap に v1 必要性を付けてください。

## 実装後 4 レンズ

| レンズ | 観点 | 起動条件 |
|---|---|---|
| Correctness | spec 適合、ロジック、過不足、回帰 | 基本 |
| Robustness | 並行処理、状態遷移、resource、Close/Shutdown、retry、冪等性 | 基本 |
| Security | 認証認可、入力、secret、信頼境界 | 該当時 |
| Contract | public API、DB schema、後方互換、caller 影響 | 該当時 |

言語や専門領域の skill は reviewer 起動時に装着する。簡素化は reviewer の別観点として reuse、重複、効率、不要な抽象化を確認し、正しさのレンズと混同しない。

依頼例:

> `git diff` を Robustness レンズだけで fresh review してください。並行処理、状態遷移、resource lifecycle、失敗時挙動、retry、冪等性を確認し、共通制約に従って報告してください。read-only で変更しないでください。

## 採用判定

controller が全指摘を diff とコードで裏取りし、次に分類する。

- **今回修正**: 高 confidence で実害が明確、修正コストが正当。
- **見送り（根拠付き）**: YAGNI、実害が低い、pre-existing、スコープ外など。
- **要判断**: protected contract や追加スコープなど、ユーザー判断が必要。

採否は controller が決め、ユーザーが覆せる。技術根拠のない同意や盲従はしない。
