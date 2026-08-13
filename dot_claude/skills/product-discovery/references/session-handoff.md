# session 引き継ぎ（`handoff` skill）を提案する基準

phase 境界で**session 引き継ぎ**（`handoff` skill の compact / new-session）を提案するかどうかの判定基準とモード規則の正規定義。既存の phase 間 handoff（`## 停止と handoff` 等）とは別の概念なので、本ファイルおよび参照側では概念を指す時は「session 引き継ぎ（`handoff` skill）」と表記する。

## 評価する時点

各 phase skill は、**次 phase を案内する時点、または phase の終端を報告する時点**で、境界表の基準により session 引き継ぎ（`handoff` skill）の要否を必ず評価する。評価そのものを省略しない。

## 境界表

| 境界 | trigger となる時点 | 促す条件 | 既定モード |
|---|---|---|---|
| `product-discovery` → `implementation-planning` | spec 承認後、planning を案内する時 | warning 条件 | compact |
| `implementation-planning` → 実行 phase | 実行方法の選択を `context.json` に記録した直後、実装 dispatch の前 | 常に | new-session |
| `execute-plan` → `ship-change` | `LOCAL_COMPLETE` を報告する時 | 常に | new-session |
| `ship-change` → `post-merge-cleanup` | MR ready を報告する時（merge 後の案内時ではない） | warning 条件 | new-session |

既定モードは new-session。`product-discovery` → `implementation-planning` の境界だけ compact（spec 議論の含みが plan 作成で直接効くため）。既定であって、ユーザーが別モードを選ぶことを妨げない。

- **warning 条件** = 当該セッションで `<context-size-warning>` が注入されている。
- **2 境界（`implementation-planning → 実行 phase` と `execute-plan → ship-change`）を無条件にする根拠**: どちらも次 phase の入力が artifact（`plan.md` / `verification.md` + `context.json`）に完備しており、それまでの探索・実装 context を丸ごと捨てられる。特に `execute-plan` は phase 中にユーザー入力が入らないため warning が phase 開始時の値のまま更新されず、条件付きにすると最も context を食う境界で検出できなくなる。
- 代理 signal（subagent 起動数 / 完了 task 数 / worktree 作成の有無）は採らない。既定運用でほぼ常に真になり判別力を持たない。

## 促さない境界

- **short path**（`product-discovery` → 実行 phase）: 定義上 1〜2 ファイルの局所変更で context 消費が小さい。
- **`execute-and-ship` の内部境界**（`LOCAL_COMPLETE` → shipping）: 合成 phase は shipping 可否を再質問せず続行する契約を持つ。ここで提案しても停止せず進むため引き継ぎ md が即 stale になる。合成を選んだ場合は **`ship-change` 段の MR ready 境界**（境界表の 4 行目）で評価する。
- `post-merge-cleanup` の終端。
- 差し戻し辺と `DEBUGGING` の出入り。

## 抑制

ユーザーが 1 度断ったら、**そのセッションでは以降どの境界でも促さない**。この抑制は境界表の「常に」にも優先する。再促しの例外は設けない（warning は毎プロンプト再注入されるため、注入の有無を例外条件にすると抑制が無効化される）。

**「断った」の判定**: 明示的な拒否に加え、提案に応じずに次の作業を指示した場合も断ったとみなす。

## 提案の形

促す時は、次 phase の案内と**同じ応答内に 1 ブロック**で次の 4 項目を出す。

1. 該当した条件（1 行、なぜ今提案するか）
2. 境界表の既定モード
3. ユーザーが応じる場合の起動文（モードを明示する）
4. 「不要ならそのまま続行できる」ことの明示

**controller は `handoff` skill を自分で起動しない。** 起動はユーザーが応じた時に行う（先に起動すると、応じない場合も md を書いて context を消費し、書いた md が即 stale になる）。同じ境界で 2 度以上繰り返さない。

## 既存 hook との関係

`<context-size-warning>` は `warn-context-size.sh`（UserPromptSubmit hook）が出す phase 非依存の汎用警告で、controller はそれを**読む側**にとどまる。警告の抑止も置換もしない。境界で提案する時は、汎用の `/clear` / `/compact` 案内ではなく `handoff` skill（引き継ぎファイル書き出しを伴う）へ誘導する。
