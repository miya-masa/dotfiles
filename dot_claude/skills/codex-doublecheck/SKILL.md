---
name: codex-doublecheck
description: ユーザーの明示指示時に、spec 段 (mode=spec) または impl 段 (mode=impl) で Codex によるクロスモデルダブルチェックを行う。herdr ペイン内 (HERDR_ENV=1) では `herdr-delegate` の agent モードで codex を起動して結果まで回収し、それ以外では Claude が `/codex:review` 等を直接起動できないため (disable-model-invocation) ハンドオフテンプレートを出してユーザーの貼り付けを待つ。既定フローには含めない (明示指示時のみ)。1 周のみ (ループ廃止)。
---

# codex-doublecheck

spec / impl 段の必須クロスモデル検証 wrapper。**ハンドオフテンプレート生成 + 貼り付け結果パース** に役割を絞る (orchestration / job 管理 / 永続化はすべて廃止)。

## 不変条件

- `/codex:review` `/codex:adversarial-review` `/codex:status` `/codex:result` `/codex:cancel` の 5 つの slash command は frontmatter で `disable-model-invocation: true` が指定されており、**Claude (assistant) からは Skill / SlashCommand いずれの tool 経由でも起動不可**。これらはすべて **ユーザーが別ターミナルで自身で実行** する
- `/codex:setup` のみ model-invocable のため、Pre-flight チェックは Claude が直接実行可能
- **`Bash` tool で `codex` CLI / `codex-companion` runtime / `codex-companion.mjs` を直接起動することを禁止する** (抜け道防止)
  - **例外: herdr ペイン内での `herdr agent` 経由の codex 起動は可** (下記「herdr 経路」)。これは `/codex:*` slash command の `disable-model-invocation` を迂回するものではなく、**ユーザーが手で行っていた「別ターミナルで codex を起動し結果を貼り戻す」工程を herdr に代行させる**もの。`codex` を直接 `Bash` で叩くのは引き続き禁止
- 本 skill 自体の起動は `Skill` tool 経由で行う (`/codex-doublecheck` という slash command は存在しない)

## 起動方法

ユーザーの明示指示時に、controller (本体) または `product-discovery` / `execute-plan` から本 skill を `Skill` tool で起動する。

```
Skill(skill="codex-doublecheck", args="mode=spec spec=/abs/path/to/spec.md")
Skill(skill="codex-doublecheck", args="mode=impl spec=/abs/.../spec.md diff=/tmp/diff.txt plan=/abs/.../plan.md")
Skill(skill="codex-doublecheck", args="mode=tier2-adversarial spec=/abs/.../spec.md diff=/tmp/diff.txt")
```

## パラメタ

| パラメタ | mode=spec | mode=impl | mode=tier2-adversarial |
|---|---|---|---|
| `mode` | `spec` 必須 | `impl` 必須 | `tier2-adversarial` 必須 |
| `spec=<path>` | 必須 (spec ファイル絶対パス) | 必須 | 必須 |
| `diff=<path>` | 未使用 | 必須 (`git diff` 出力ファイル) | 必須 |
| `plan=<path>` | 未使用 | 必須 (plan ファイル絶対パス) | 未使用 |
| `round=<N>` | 任意 (互換のため受理、内部参照なし) | 任意 (同上) | 任意 (同上) |

`round` パラメタは旧仕様 (3 周ループ) の互換のため受理するが、本 skill 内部では参照しない (1 周のみ)。

## 失敗時挙動 (mode 別)

| 局面 | mode=spec | mode=impl | mode=tier2-adversarial |
|---|---|---|---|
| Pre-flight (`/codex:setup`) NG | **hard fail** (検証段に進まない) | **fail-soft** (警告転記、続行) | **fail-soft** |
| ユーザーが「Codex 検証スキップ」と返信 | warning レポート、検証段は Claude のみで完了 | 同左 (Step E に警告転記、MR/PR description にも記載) | 同左 |
| 貼り付けられた Codex 出力が空 / 200 字未満 / 重大度語彙を含まない | parse error として fail-soft 扱い | 同左 | 同左 |

## ステップ

### 1. Pre-flight

herdr 経路 (`HERDR_ENV=1`) と手貼り経路で確認内容が異なる。

**herdr 経路**: `herdr-delegate` の `agent` モード手順 1 に従い `command -v codex` で確認する。`/codex:setup` は踏まない。NG（PATH に無い）なら **mode を問わず fail-soft** とし、手貼り経路のハンドオフテンプレートに切り替える。**mode=spec の hard fail はここでは適用されない**（herdr 経路の失敗はユーザーの手貼り作業への切り替えであり検証自体が止まるわけではないため）。

**手貼り経路**: `/codex:setup` slash command は **model-invocable** のため Claude が直接実行する。`SlashCommand` tool または slash command 起動経路を使い、以下を確認:

- Codex CLI が install 済み
- auth が有効
- `openai-codex` plugin が install 済みで `/codex:*` slash command がユーザー側で利用可能

`Bash` tool で `codex --version` を直接叩く実装は禁止。

**NG 時 (手貼り経路のみ):**
- `mode=spec` → hard fail。エラー出力 + 修復手順 (例: `1Password CLI でログイン後 codex auth login`) を提示し、検証段に進まない
- `mode=impl` / `mode=tier2-adversarial` → fail-soft。下記 fail-soft 警告フォーマットでレポートを返し、呼び出し元の判断に委ねる

### 2. 入力組み立て

#### mode=spec
- 入力 = `spec=` で指定された spec ファイル全文
- 0-context 原則: discovery の議論履歴・却下した代替案・確定済み設計判断の根拠は埋め込まない (spec ファイルのみ)

#### mode=impl
- 入力 = `diff=` (git diff) + `spec=` 全文 + `plan=` 全文 を結合
- 結合後の token 数が **10000 token を超える場合**、spec / plan は "## 設計詳細" 以下を切り出し、それ以外は省略
- 0-context 原則: 議論履歴は埋め込まない

#### mode=tier2-adversarial
- 入力 = `spec=` 全文 + `diff=` (git diff) + 「設計判断を pressure-test しろ」指示
- 重点: 命名 / API 一貫性 / 暗黙前提 / 代替案検討漏れ の adversarial 視点

### 3. 経路判定

```bash
test "${HERDR_ENV:-}" = 1
```

- **成立 → herdr 経路** (下記「herdr 経路」)。Step 3〜5 を置き換える。ユーザーへの貼り付け依頼は行わない
- **不成立 → 手貼り経路** (従来どおり Step 3〜5 を実行)

## herdr 経路 (HERDR_ENV=1 のとき)

`herdr-delegate` の `agent` モードに従う（手順・落とし穴回避は同契約に一本化し、ここでは再掲しない）。

- 委譲先への入力（`build-prompt` に渡すもの）は Step 2 で組み立てた prompt（0-context 原則込み）。
- Pre-flight は上記「1. Pre-flight」のとおり `command -v codex` を使う（`agent` モード手順 1）。NG なら mode を問わず fail-soft とする。
- 回収した md は `agent` モードの完了判定（終端マーカー付きファイル）を経てから読み、パース (Step 5) は手貼り経路と同一。`raw_output` には回収した md の内容を入れる。
- 終端状態の扱いは契約どおり: fail-soft（Pre-flight NG / `unknown` 等）は手貼り経路のハンドオフテンプレートへ切り替える。`blocked`（承認画面等）はペインを残し、画面内容・pane_id・到達手段をユーザーに提示して停止する。

### 3'. ハンドオフテンプレート生成 (手貼り経路のみ)

mode 別に以下のテンプレートを Markdown 文字列として組み立てる。プレースホルダ (`<REPO_ABS_PATH>` `<BASE_REF>` `<SCOPE>` 等) は実際の値で埋める。

````markdown
Codex によるクロスモデル検証をユーザー側で実行してください。

## 1. 別ターミナルで Codex を起動

別のターミナル (tmux pane / 別ウィンドウ) を開き、以下を実行:

```sh
cd <REPO_ABS_PATH>
codex
```

または別ターミナルで `claude` を起動して、以下の Claude Code slash command を打つ:

```
<推奨 slash command (mode 別、下表参照)>
```

## 2. 起動後、以下のプロンプトを貼り付け

```
あなたは検証エージェントです。discovery の議論履歴・却下案・確定済み設計判断の根拠は
渡されていません。下記の入力のみを情報源として独立検証してください。

# 入力
<spec / plan / diff 全文または "## 設計詳細" 以下の切り出し>

# 観点 (mode 別)
<spec の場合: 論理穴 / 不変条件破綻 / エッジケース漏れ>
<impl の場合: spec/plan と実装 (diff) の乖離>
<tier2-adversarial の場合: 設計判断を pressure-test、代替案検討漏れ>

# 重大度語彙
- Blocker: データ消失 / セキュリティ侵害 / データ整合性破綻に直結
- Major: 不変条件が崩れうる / defensive に明示すべき path
- Minor: 暗黙前提・エッジケース・運用 best practice
- Info: 実装計画段階で確定で十分 / 将来拡張対応可

# 出力フォーマット
## Blocker
### [BLOCK-N] タイトル
- 問題:
- 影響:
- 推奨:

## Major
## Minor
## Info
## Verified
```

## 3. Codex 出力を本セッションに貼り付けてください

Codex の出力全文を本セッションのプロンプトに貼り付けてください。
Claude 側で Blocker / Major / Minor / Info カウントを抽出し、検証段の判定を行います。

中止する場合: 「Codex 検証スキップ」と返信してください
(spec 段では検証 incomplete 扱い、impl 段では fail-soft 警告として MR/PR description に転記)。

## 補足: 推奨 slash command と --background

長時間 review (> 5 分目安) の場合は `--background` も可:
1. 別ターミナルで `<--background 版 slash command>` → job-id が返る
2. `/codex:status <job-id>` で完了待ち
3. 完了後 `/codex:result <job-id>` で結果取得 → 本セッションに貼り付け
````

mode 別の推奨 slash command:

| mode | 推奨 slash command (--wait) | --background 版 |
|---|---|---|
| `spec` | `/codex:review --wait --scope working-tree` | `/codex:review --background --scope working-tree` |
| `impl` | `/codex:review --wait --base <BASE_REF>` | `/codex:review --background --base <BASE_REF>` |
| `tier2-adversarial` | `/codex:adversarial-review --wait --base <BASE_REF>` | `/codex:adversarial-review --background --base <BASE_REF>` |

`<BASE_REF>` は呼び出し元から渡された diff の base ブランチ (デフォルト `main` または `master`)。

### 4. 呼び出し元へのハンドオフ (手貼り経路のみ)

ハンドオフテンプレートを文字列として呼び出し元に返す。呼び出し元 (Claude のメインターン) はこのテンプレートをユーザーに提示し、貼り付けを待つ。

**重要:** 本 skill は呼び出し元のターン内で完結する。ユーザー貼り付け待ちは呼び出し元のターン境界で行う (本 skill 内部で「待機」状態を持たない)。

### 5. ユーザー貼り付け結果のパース

ユーザーが Codex 出力を貼り付けた後、呼び出し元が再度本 skill を呼ぶ (or 直接パースロジックを参照する) 形で以下を実施:

**スキーマ違反判定 (fail-soft トリガー):**
- 出力が空
- 200 字未満
- "Blocker"、"Major"、"Minor"、"Info" のいずれの語も含まれない
- ユーザーが「Codex 検証スキップ」と返信した

→ いずれかに該当したら fail-soft 警告フォーマットを返す。

**正常パース時:**
- `## Blocker` / `## Major` / `## Minor` / `## Info` セクションを Markdown 見出しで分割
- 各セクション内の `### [XXX-N]` 見出しを数えて重大度別カウントを算出
- 集約結果を以下の形式で呼び出し元に返す:

```yaml
mode: spec | impl | tier2-adversarial
status: success | fail-soft | skipped
blocker_count: N        # status=success のみ
major_count: N
minor_count: N
info_count: N
warning: <内容>          # status=fail-soft / skipped のみ
raw_output: <貼り付けられた Codex 出力全文>
```

呼び出し元はこの結果を見て判定:
- `status=success` かつ `blocker_count=0` → 検証 PASS
- `status=success` かつ `blocker_count>0` → 呼び出し元の修正サイクルに 1 回だけ反映 (再 Codex 起動なし、本 skill は 1 周のみ)
- `status=fail-soft` / `skipped` → 警告転記、検証段は Claude のみで完了

## fail-soft 警告フォーマット

```
⚠️ Codex 検証スキップ
  - mode: spec | impl | tier2-adversarial
  - 理由: setup gate fail / parse error / ユーザースキップ / 貼り付け空
  - 影響: 当該段では Claude 検証のみで完了しています
  - 推奨: 後でユーザーが Codex を別ターミナルで実行可能
```

`mode=impl` / `mode=tier2-adversarial` の場合、出荷時に MR/PR description にも転記する (詳細は `ship-change` skill 参照)。

## 廃止された旧仕様 (互換情報)

旧 spec では以下を本 skill が担っていたが、`/codex:*` 系 5 command が `disable-model-invocation: true` であるため Claude から起動不能。**すべて廃止**:

- `/codex:review --background` の Claude 直接起動
- background job の poll (`/codex:status`)
- 結果回収 (`/codex:result`)
- キャンセル (`/codex:cancel`)
- `/compact` 抑止 (走行中 job との連携)
- シリアル化 gate (Tier 2 adversarial と Step F.5 の並行衝突回避)
- 3 周ループ判定 (1 周のみに変更)

これらの管理は plugin 側 (codex CLI / `openai-codex` plugin) に完全に委ねる。

## 関連 skill

- ワークフロー: `product-discovery`（spec review gate）/ `execute-plan`（final review）。転記先は `ship-change`。本 skill は既定フローに含めず、ユーザー明示指示時のみ起動する。
