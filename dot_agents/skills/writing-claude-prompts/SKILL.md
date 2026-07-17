---
name: writing-claude-prompts
description: Use when authoring or refining a prompt for Claude (system prompt, user message, tool description, agent instructions) to make it follow Anthropic's official prompt engineering best practices — covers clarity, XML structure, few-shot examples, role, long-context layout, output format control, tool-use phrasing, and effort/adaptive-thinking knobs for the Claude 5 family (Fable 5 / Sonnet 5 / Opus 4.8).
---

# Writing Claude Prompts

## Overview

Anthropic 公式の prompt engineering best practices（Claude 5 family — Fable 5 / Sonnet 5 / Opus 4.8 / Haiku 4.5 — を含む現行モデル向け）に従って prompt を組み立てるための reference。

**Golden Rule（黄金律）:**
> プロンプトをタスクに関する最小限のコンテキストを持つ同僚に見せて、それに従うよう求めてください。彼らが混乱していたら、Claude も混乱します。

**核となる原則:**
- 望ましい動作は推測させず明示的に書く
- XML タグで指示・コンテキスト・入力・例を区別する
- 例は 3〜5 個、関連性・多様性・構造化された形で
- 長いコンテキストはドキュメントを上、クエリを下
- 「やらないで」より「こう書いて」（肯定的な指示）

**公式リファレンス:** https://platform.claude.com/docs/ja/build-with-claude/prompt-engineering/claude-prompting-best-practices

## When to Use

以下の場面で発火する:

- ユーザーが「prompt を書いて／作って／改善して／レビューして」と言ったとき
- system prompt / agent instructions / tool description を新規作成・修正するとき
- LLM 駆動アプリ（Anthropic SDK / Claude API）の prompt を設計するとき
- 既存 prompt が想定通り動かないので調整したいとき
- Opus 4.7 世代 → Claude 5 family（Fable 5 / Sonnet 5 / Opus 4.8）への移行で prompt を更新するとき
- ユーザーが「Anthropic のベストプラクティスに従って…」と明示したとき

**使わない場面:**
- 他社 LLM (OpenAI / Gemini / etc.) 用の prompt 作成 → そのモデル固有の reference を使う
- 単に文章を書くタスク（プロンプト設計を含まない）

## Core Patterns

### 1. 明確で直接的な指示

「望ましい出力」「制約」「順序」を具体的に書く。順序が重要なら番号付き / 箇条書き。

```text
# ❌ NG: 曖昧
分析ダッシュボードを作成してください

# ✅ OK: 具体的・修飾子付き
分析ダッシュボードを作成してください。関連するすべての機能とインタラクションを
含めてください。基本を超えて、完全に機能する実装を作成してください。
```

### 2. コンテキスト（Why）を添える

指示の理由を書くと精度が上がる。

```text
# ❌ NG
省略記号を決して使用しないでください

# ✅ OK
あなたの応答はテキスト読み上げエンジンによって読み上げられるため、
テキスト読み上げエンジンが発音方法を知らないため、省略記号を決して使用しないでください。
```

### 3. XML タグで構造化

指示・コンテキスト・例・入力を tag で区別する。一貫した命名・必要なら nest。

```xml
<instructions>
診断対象の患者情報を分析してください。
</instructions>

<documents>
  <document index="1">
    <source>patient_symptoms.txt</source>
    <document_content>
      {{PATIENT_SYMPTOMS}}
    </document_content>
  </document>
</documents>

<examples>
  <example>
    <input>...</input>
    <output>...</output>
  </example>
</examples>
```

### 4. 例（Few-Shot / Multi-Shot）

3〜5 個、`<example>` / `<examples>` でラップ。**関連性・多様性・構造化**の 3 条件を満たす。エッジケースもカバー。

### 5. ロール設定

system prompt にロールを書く。1 文でも効果がある。

```python
system="You are a helpful coding assistant specializing in Python."
```

### 6. 長いコンテキストの配置（20k+ トークン）

| 位置 | 配置するもの |
|------|--------------|
| **上部** | 長いドキュメント・データ（`<documents>`） |
| **下部** | クエリ・指示・例 |

> クエリの終わりは、テストで応答品質を最大 30% 改善できる。

複数文書は `<documents><document index="n"><source/><document_content/></document></documents>` で構造化。Claude にまず関連箇所を `<quotes>` で抜き出させてから回答させると、ノイズに強くなる。

### 7. 出力フォーマット制御

| やること | 効果 |
|----------|------|
| **「こうして」と書く（NOT「こうしないで」）** | 肯定的指示の方が効く |
| **XML フォーマットインジケータ** | `<smoothly_flowing_prose_paragraphs>` で囲ませる |
| **prompt 自体のスタイルを揃える** | prompt が markdown だらけだと出力も markdown だらけ |
| **詳細な指示** | リスト抑制 / 数式表記抑制など、明示的に書く |

例: markdown を抑制したい場合は SKILL 末尾の Reference に書いた `<avoid_excessive_markdown_and_bullet_points>` ブロックを system prompt に入れる。

### 8. ツール使用 / アクション動作

| 望む挙動 | フレーズ |
|----------|----------|
| **action を取らせる** | "Modify this function" / "Make these edits" |
| **suggestion だけ** | "Could you suggest some changes" |
| **デフォルトで action** | system に `<default_to_action>` ブロック |
| **デフォルトで保守的** | system に `<do_not_act_before_instructions>` ブロック |

**重要:** Claude の現行モデルは総じてシステムプロンプトに敏感で、強い表現を書くほど従順に反応する。`CRITICAL: You MUST...` のような力技の強調は、旧モデルの undertrigger 対策として書かれたものが多いが、現行モデルでは **過剰トリガー（overtrigger）** の原因になる。`Use this tool when ...` 程度の通常表現に弱め、「迷ったら使え」的なブランケット指示も「〜のときに使う」という条件付きに直す。

ただし、これは"ツール起動を煽る"文脈に限った話であり、投機禁止・事実確認のような**ハルシネーション防止の文脈**では強い言い回し（`MUST` を含む）が公式にも推奨例として使われている（本ページ末尾の Reference Snippet H 参照）。強調語の tone down は機械的に全箇所へ適用せず、文脈で判断する。

### 9. 並列ツール呼び出し

依存のない複数ツール呼び出しを並列化させたいときは system に追加:

```text
<use_parallel_tool_calls>
複数のツールを呼び出す予定があり、ツール呼び出し間に依存関係がない場合は、
独立したすべてのツール呼び出しを並列で実行してください。
（…ツール呼び出しでプレースホルダーを使用したり、不足しているパラメータを推測したりしないでください）
</use_parallel_tool_calls>
```

### 10. 思考（Thinking）と effort

`effort` は intelligence / latency / cost のトレードオフを制御する主レバー。**Fable 5 と Sonnet 5 は thinking が既定 ON（adaptive）**、**Opus 4.8 は既定 OFF**（明示的に `thinking: {type: "adaptive"}` を設定しない限り思考しない）という向きの違いに注意。`budget_tokens` による手動 extended thinking は Opus 4.7 以降・Fable 5/Mythos 5・Sonnet 5 のいずれでも 400 エラーになる（後述の migration 注意参照）。

| モデル | effort の既定 | 早見表 |
|--------|--------------|--------|
| **Fable 5** | thinking 既定 ON。`high` を大半のタスクの既定に、`xhigh` は最も難度の高いタスクのみ、`medium`/`low` はルーティン作業向け | 低い effort でも旧モデルの `xhigh` 相当以上の性能が出ることが多い。タスクが終わるが時間超過気味なら effort を下げてよい |
| **Sonnet 5** | thinking 既定 ON。既定 `high`（4.6 と同じ）。最難関のコーディング・エージェントタスクは `xhigh` へ | `low`/`medium` では**文字通りスコープ厳守**で動くため under-thinking のリスクがある。複雑な問題で浅い推論が見えたら、プロンプトで誤魔化さず effort を上げる |
| **Opus 4.8** | thinking 既定 OFF（明示設定が必要）。coding/agentic は `xhigh` を既定に、知能重視タスクでも最低 `high` | 4.8 は前世代 Opus よりさらに effort 依存度が高い。アップグレード時は積極的に検証する |

いずれのモデルも `low`/`medium` は「頼まれたこと」に厳密にスコープを絞る（over-and-beyond をしない）。`max`/`xhigh` 実行時は `max_tokens` を **64k** から始めて調整する。プロンプト側で過度に思考しすぎる場合（大きい/複雑な system prompt でよく起きる）は以下で抑制:

```text
拡張思考は遅延を追加し、回答品質を有意に改善する場合にのみ使用してください。
通常、マルチステップ推論を必要とする問題の場合です。疑わしい場合は、直接応答してください。
```

### 11. プリフィル応答の廃止（Claude 4.6 以降 — Claude 5 family も含む）

Claude 4.6 系以降の全モデル（**Fable 5 / Mythos 5 を含む**）で、assistant の prefilled response（最後の assistant ターンへの部分応答の事前投入）は**非サポート**。使うと 400 エラーになる（単なる非推奨ではなく実際に壊れる）。代替:

| 旧用途 | 新代替 |
|--------|--------|
| JSON / YAML 強制 | [Structured Outputs](https://platform.claude.com/docs/ja/build-with-claude/structured-outputs) / Tool use |
| 前置き排除 | `Respond directly without preamble. Don't start with "Here is..."` |
| 拒否回避 | 不要（モデルが改善された） |
| 継続 | user メッセージに `Previous response was truncated, ending at \`[...]\`. Continue from where you left off.` |

### 12. モデル別の注意点（Claude 5 family）

**Fable 5:** 1ターンが数分〜数時間続く長時間実行（long-horizon autonomy）が既定なので、クライアントタイムアウト・進捗表示を前提から見直す。instruction-following が非常に強く、簡潔な1文で複数の振る舞いを制御できるため、checkpoint/gate の個別列挙は「本当に必要な時だけ止まる」という一般原則に集約してよい。サブエージェント委譲を積極的に行い、orchestrator は完了をブロッキング待ちせず非同期に扱うことが推奨される。教訓をスクラッチファイルに記録するメモリシステムとの親和性が高い（項目 16 参照）。**`reasoning_extraction` refusal に注意**: 内部 thinking の書き起こし・説明をレスポンステキストとして要求する指示は refusal（Opus 4.8 への fallback 増加）を誘発しうるため、「thinking を書き出せ」的な指示は削除し、必要なら構造化 `thinking` ブロックを読む方に置き換える。既存 prompt/skill は過剰に prescriptive になりがちなので、デフォルト性能の方が良ければ古い指示は削ってよい。

**Sonnet 5:** 応答の冗長度はタスクの複雑さに応じて自動調整される（固定 verbosity が要る場合のみ追加指示）。`low`/`medium` effort では文字通りスコープ通りに動くため under-thinking リスクがある。より文字通りに(literal)指示に従い、ある項目への指示を他の項目に暗黙に一般化しない（範囲を広げたいなら「すべてのセクションに適用」等と明示）。`temperature`/`top_p`/`top_k` の非デフォルト値指定は 400 エラー（Sonnet 系で新しい制約）なので、スタイルの多様性はプロンプトで誘導する。

**Opus 4.8:** thinking は既定 OFF。推論(reasoning)をツール呼び出しより優先しがちなので、ツール使用を増やしたいなら effort を上げるか明示指示を足す。より文字通りに指示に従う（Sonnet 5 と同様の傾向）。subagent 生成が既定で少なめなので、積極的に使わせたいなら明示的にガイダンスを与える。デザイン/フロントエンドで強い house style（クリーム背景・セリフ体・テラコッタ）が既定で出るため、避けたいなら「使うな」ではなく具体的な代替パレットを指定するか、構築前に複数案(4案程度)を提案させる。

**全モデル共通のコードレビュー注意**: 「high-severity のみ報告」「be conservative」等の指示は、現行モデルほど忠実に守りすぎて低重要度バグの報告を絞りすぎることがある（recall 低下に見えるが実態はハーネス効果）。`Report all issues you find, including ones you're uncertain about... Your goal is coverage.` で検出と報告のフェーズを分離すると復旧する。

### 13. 自律性 vs 安全性（エージェント）

長時間タスクで破壊的操作（rm / push --force / DB drop 等）を勝手にさせない:

```text
逆転が難しい、共有システムに影響を与える、または破壊的である可能性のあるアクションについては、
進める前にユーザーに確認してください。
```

Fable 5 のような長時間自律実行モデルでは、これに加えて「境界の明示」（問題の説明・質問には修正せず報告して止まる／システム状態を変える前に証拠が対象アクションを裏付けているか確認する）と、「進捗の証跡裏取り」（各主張をツール結果と突き合わせ、未検証は明示し、失敗は失敗と述べる）が有効性の確認された具体パターンとして推奨されている。後者は Anthropic の検証で、捏造された進捗報告を狙って誘発するタスクでもほぼ根絶したと報告されている。長時間の自律実行を任せる agent instructions では明示的に含める価値が高い。

### 14. 過度な熱心さの抑制

Claude の現行モデルは不要な抽象化・追加ファイル・防御的コードを書きがちな傾向が残っている。抑制プロンプト:

```text
過度な設計を避けてください。直接要求されたか、明らかに必要な変更のみを行ってください。
- スコープ: 要求された以上のことをしない
- ドキュメンテーション: 触らないコードに注釈を付けない
- 防御的コーディング: 起こらないシナリオの error handling を足さない
- 抽象化: 単一用途のヘルパーを作らない
```

### 15. 幻覚の抑制（コーディング）

```text
<investigate_before_answering>
開いていないコードについて推測しないでください。ユーザーが特定のファイルを参照する場合は、
回答する前にファイルを読む必要があります。
</investigate_before_answering>
```

これは投機禁止・事実確認の文脈であり、公式ドキュメント自身が `MUST` を含む強い表現を推奨例として示している（項目 9 の注記参照）。

### 16. サブエージェント委譲とメモリ（Fable 5 で特に有効）

Fable 5 は前世代より積極的に並列サブエージェントを dispatch する。委譲判断の基準（独立サブタスクは委譲し、完了を待つ間も作業を続ける。介入は脱線・情報不足時のみ）を明示すると効果が上がる。長時間実行での自己検証は、自己批判より**フレッシュコンテキストの verifier subagent**の方が有効性が高いと報告されている（「一定間隔でサブエージェントに仕様との突き合わせ検証をさせる」）。

Fable 5 はセッションをまたぐ教訓の記録・参照とも相性が良い。**1教訓1ファイル・先頭に一行要約**、修正内容と確認済みアプローチを理由付きで記録、重複作成せず更新、誤りは削除、というメモリシステムの具体形が推奨されている（このリポジトリの `~/.claude/.../memory/` 運用と一致するパターン）。

## Quick Reference（チェックリスト）

prompt を書き終わったら以下を確認:

- [ ] **黄金律**: タスク文脈の薄い同僚に見せても伝わるか
- [ ] **明確性**: 望ましい出力・制約・順序が具体的か
- [ ] **Why**: 重要な制約には理由が添えられているか
- [ ] **XML 構造**: instructions / context / examples / input が区別されているか
- [ ] **例**: 3〜5 個、`<example>` でラップ、エッジケース含む
- [ ] **ロール**: system に役割が 1 文以上書かれているか
- [ ] **長文配置**: ドキュメント上 / クエリ下になっているか
- [ ] **肯定形**: 「こうして」になっているか（「するな」になっていないか）
- [ ] **ツール表現**: 強すぎる "CRITICAL: MUST" を tone down したか（投機禁止等の文脈は例外）
- [ ] **思考設定**: `effort` を明示したか（`budget_tokens` ではなく `effort` + `thinking: {type: "adaptive"}`）。Opus 4.8 は thinking 既定 OFF、Fable 5 / Sonnet 5 は既定 ON という向きの違いを踏まえたか
- [ ] **プリフィルなし**: user 末尾までで完結しているか（Claude 4.6 以降は Fable 5/Mythos 5 含め全面非サポート）
- [ ] **モデル文字列**: `claude-fable-5` / `claude-sonnet-5` / `claude-opus-4-8` を正しく書いたか
- [ ] **reasoning_extraction 回避**（Fable 5 向け）: thinking の内容を書き出させる指示が残っていないか

## Workflow（promptを作るときの手順）

1. **目的確認**: 何を達成したい prompt か / どのモデル（Fable 5 / Sonnet 5 / Opus 4.8）/ どの effort / どんな入出力フォーマットか をユーザーに聞き取り
2. **構造設計**: XML タグの骨格を決める（`<instructions>`, `<context>`, `<examples>`, `<input>`, `<output_format>` 等）
3. **指示本体**: 黄金律と明確性を満たす本文を書く
4. **理由付け**: 重要な制約に Why を添える
5. **例**: 3〜5 個の `<example>` を組み込む（必要なら）
6. **長文配置**: 大きな文書は最上部に置く
7. **ツール / 思考 / 並列 / 過度抑制** など現行モデル固有のフレーズを必要に応じて追加
8. **チェックリスト** で自己レビュー
9. **モデル別微調整**: 対象モデルに応じて literal 解釈・トーン・subagent・design・effort の既定 ON/OFF に注意（項目 12 参照）

## Common Mistakes

| よくある間違い | 修正 |
|----------------|------|
| `Don't use markdown` だけ書く | `Respond in flowing prose paragraphs. Use markdown only for inline code, code blocks, and headings.` のように **やってほしいこと** を書く |
| `<example>` ラップなしで例を貼る | `<example>` / `<examples>` で構造化する |
| `CRITICAL: You MUST always...`（ツール起動を煽る文脈） | `Use this tool when...` に弱める（現行モデルは過剰反応しやすい。投機禁止文脈は例外） |
| `budget_tokens` で思考量制御 | `effort` パラメータ + `thinking: {type: "adaptive"}` に移行（Opus 4.7 以降・Fable 5/Mythos 5・Sonnet 5 では `budget_tokens` 指定は 400 エラー） |
| プリフィル `assistant: "Here is the JSON: {"` | Structured Outputs / Tool use / `Respond directly without preamble.` に置換 |
| 長文の **後** にクエリを書かない | 長文を上、クエリを下（最大 30% の品質改善） |
| Sonnet 5 / Opus 4.8 で旧モデルと同じ「徹底的に」プロンプト | 現行モデルは文字通り解釈する。スコープを明示し、過剰な「徹底」指示は削る |
| Sonnet 5 / Opus 4.8 で AI slop なデザインが出る | 具体的な palette / typeface を指定するか、構築前に複数案（4案程度）提案させる |
| recall が下がったコードレビュー | `Report all issues including uncertain/low-severity. Filtering happens in another step.` に書き換え |
| 説明だけで動かない | `<default_to_action>` ブロックで action を促す |
| Fable 5 の agent instructions に thinking 書き起こし指示を残す | `reasoning_extraction` refusal を誘発しうる。削除し、必要なら `thinking` ブロックの構造化出力を読む |
| Fable 5 の checkpoint を個別列挙する | 「破壊的・不可逆・スコープ変更・ユーザーしか答えられない入力」の一般原則に集約する（項目 12 参照） |

## Reference Snippets

そのまま埋め込める実用ブロック集。コピペして使う。

### A. Markdown 抑制

```text
<avoid_excessive_markdown_and_bullet_points>
レポート、ドキュメント、技術説明、分析、または長編コンテンツを書く場合、
完全な段落と文を使用して、明確で流れるような散文で書いてください。
標準的な段落区切りを組織に使用し、マークダウンを主に `inline code`、
コードブロック（```...```）、および単純な見出し（###、および ###）に予約してください。
**太字**と*イタリック*の使用を避けてください。

順序付きリスト（1. ...）または順序なしリスト（*）を使用しないでください。
ただし、a）リスト形式が最良のオプションである真に離散的なアイテムを提示している場合、
または b）ユーザーが明示的にリストまたはランク付けをリクエストしている場合を除きます。
</avoid_excessive_markdown_and_bullet_points>
```

### B. LaTeX 抑制（プレーンテキスト数式）

```text
応答をプレーンテキストのみでフォーマットしてください。
LaTeX、MathJax、または \( \)、$、または \frac{}{} などのマークアップ表記を使用しないでください。
標準的なテキスト文字を使用してすべての数学式を書いてください
（例えば、除算の場合は「/」、乗算の場合は「*」、指数の場合は「^」）。
```

### C. 並列ツール呼び出し最大化

```text
<use_parallel_tool_calls>
複数のツールを呼び出す予定があり、ツール呼び出し間に依存関係がない場合は、
独立したすべてのツール呼び出しを並列で実行してください。
順序立てて実行するのではなく、アクションを並列で実行できる場合は常に
ツールを同時に呼び出すことを優先してください。

ただし、一部のツール呼び出しが前の呼び出しに依存してパラメータなどの依存値を通知する場合は、
これらのツールを並列で呼び出さず、代わりに順序立てて呼び出してください。
ツール呼び出しでプレースホルダーを使用したり、不足しているパラメータを推測したりしないでください。
</use_parallel_tool_calls>
```

### D. デフォルトで action

```text
<default_to_action>
デフォルトでは、提案するだけでなく変更を実装してください。
ユーザーの意図が不明な場合は、最も有用な可能性のあるアクションを推測し、
推測する代わりにツールを使用して欠落している詳細を発見して進めてください。
</default_to_action>
```

### E. デフォルトで保守的

```text
<do_not_act_before_instructions>
変更を明確に指示されない限り、実装またはファイルの変更にジャンプしないでください。
ユーザーの意図が曖昧な場合は、情報提供、研究、および推奨事項の提供ではなく、
アクションを取ることをデフォルトにしてください。
</do_not_act_before_instructions>
```

### F. 安全性（破壊的操作の確認）

```text
逆転が難しい、共有システムに影響を与える、または破壊的である可能性のあるアクションについては、
進める前にユーザーに確認してください。

確認が必要なアクションの例：
- 破壊的な操作：ファイルまたはブランチの削除、データベーステーブルの削除、rm -rf
- 逆転が難しい操作：git push --force、git reset --hard、公開されたコミットの修正
- 他の人に見える操作：コードのプッシュ、PR/イシューへのコメント、メッセージの送信
```

### G. 過度な設計の抑制

```text
過度な設計を避けてください。直接要求されたか、明らかに必要な変更のみを行ってください。

- スコープ：要求されたもの以上の機能を追加したり、コードをリファクタリングしたり、
  「改善」を行ったりしないでください。
- ドキュメンテーション：変更しなかったコードに docstring、コメント、または型注釈を追加しないでください。
- 防御的コーディング：発生する可能性のないシナリオのエラーハンドリング、フォールバック、
  または検証を追加しないでください。
- 抽象化：ワンタイム操作のためのヘルパー、ユーティリティ、または抽象化を作成しないでください。
```

### H. 幻覚抑制（コード調査）

```text
<investigate_before_answering>
開いていないコードについて推測しないでください。ユーザーが特定のファイルを参照する場合は、
回答する前にファイルを読む必要があります。質問に答える前に、関連するファイルを調査して読んでください。
確実でない限り、調査する前にコードについて主張しないでください。
根拠のある幻覚のない回答を提供してください。
</investigate_before_answering>
```

### I. コードレビューでの recall 確保

```text
不確実なまたは低重大度と考えるものを含む、見つけたすべての問題を報告してください。
この段階で重要性または信頼度をフィルタリングしないでください。
別の検証ステップがそれを行います。あなたの目標はカバレッジです。
後でフィルタリングされる調査結果を表面化する方が、黙って実際のバグをドロップするよりも優れています。
各調査結果について、信頼レベルと推定重大度を含めて、
ダウンストリームフィルタがそれらをランク付けできるようにしてください。
```

### J. モデル自己認識

対象モデルに応じてモデル名・モデル文字列を書き換えて使う（コピペしたまま放置すると誤ったモデル自己申告になるため、実際に紐付くモデルへ必ず差し替える）:

```text
アシスタントは Claude であり、Anthropic によって作成されました。
現在のモデルは Claude Fable 5 です。LLM が必要な場合は、
ユーザーが別途リクエストしない限り、Claude Fable 5 をデフォルトにしてください。
Claude Fable 5 の正確なモデル文字列は claude-fable-5 です。
```

他モデルのモデル文字列: Sonnet 5 = `claude-sonnet-5` / Opus 4.8 = `claude-opus-4-8` / Haiku 4.5 = `claude-haiku-4-5-20251001`。

### K. フロントエンド美学（AI slop 回避）

```text
<frontend_aesthetics>
過度に使用されるフォントファミリー（Inter、Roboto、Arial、システムフォント）、
決まり文句のカラースキーム（特に白または暗い背景の紫グラデーション）、
予測可能なレイアウトとコンポーネントパターン、およびコンテキスト固有の文字に欠ける既製の
デザインなどの一般的な AI 生成美学を決して使用しないでください。
ユニークなフォント、統一されたカラーとテーマ、およびエフェクトと
マイクロインタラクションのアニメーションを使用してください。
</frontend_aesthetics>
```

## Anti-Patterns

- **narrative example を入れる**: 「先日 X というケースで…」を skill に書かない（再利用性が下がる）
- **`Don't ...` だけで指示**: 何をすべきか肯定形で書く
- **checkpoint・過剰実装防止・進捗サマリー等を個別列挙で反復する**: Fable 5 は instruction-following が強く、一般原則1文への集約で足りることが多い（項目 12・16 参照）

その他の典型的な間違いは Common Mistakes 表を参照。

## Bottom Line

> 「Claude を、あなたの規範とワークフローのコンテキストに欠ける才能のある新しい従業員と考えてください」

具体的に・構造化して・理由を添えて・例を見せる。これが Claude を最大限引き出す方法。
