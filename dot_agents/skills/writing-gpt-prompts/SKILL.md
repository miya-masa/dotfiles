---
name: writing-gpt-prompts
description: Use when authoring or refining a prompt for GPT-5.5 / OpenAI models (developer message, user message, tool description, agent instructions) to make it follow OpenAI's official prompt-guidance — covers outcome-first design, the Role / Personality / Goal / Success / Constraints / Output / Stop scaffold, markdown vs XML mixing, few-shot examples, agentic preambles, reasoning-effort and verbosity knobs, tool-persistence rules, and the phase parameter for the Responses API.
---

# Writing GPT-5.5 Prompts

## Overview

OpenAI 公式の **Prompt Guidance**（GPT-5.5 / Responses API 向け）+ **Prompt Engineering Guide** + **Using GPT-5.5** を統合した reference。GPT-5 系（特に 5.5）は **outcome-first**（destination を示し path はモデルに任せる）設計が前提で、Claude 4.x の「具体的・徹底的に書く」とは設計思想が異なる。

**Golden Rule（黄金律）:**
> **destination を定義し、効率的な path はモデルに選ばせる。** プロセスを step-by-step で規定するのではなく、達成すべき outcome / success criteria / constraints / stop rules を書く。

**核となる原則:**

- **Outcome-first**: 「A → B → C をやれ」ではなく「これが満たされたら成功」と書く
- **Markdown と XML の使い分け**: hierarchy / 見出しは markdown、コンテンツ境界（reference docs / 例）は XML
- **発話順序**: Identity → Instructions → Examples → Context（再利用部は前方に置いて prompt cache を効かせる）
- **絶対ルールを濫用しない**: `ALWAYS` / `NEVER` / `must` / `only` は本当の invariant にだけ使う
- **stop rules を必ず書く**: 「retry / fallback / abstain / ask / stop をいつ選ぶか」を明示
- **GPT-5.5 のデフォルトは concise & direct**: 温かいトーンが必要なときだけ明示する

**公式リファレンス:**

- https://developers.openai.com/api/docs/guides/prompt-guidance
- https://developers.openai.com/api/docs/guides/prompt-engineering
- https://developers.openai.com/api/docs/guides/latest-model（Using GPT-5.5）
- https://developers.openai.com/api/docs/guides/frontend-prompt
- https://developers.openai.com/api/docs/guides/citation-formatting
- https://developers.openai.com/api/docs/guides/migrate-to-responses

## When to Use

以下の場面で発火する:

- ユーザーが GPT-5.5 / GPT-5 / OpenAI モデル向けの prompt を「書いて／作って／改善して／レビューして」と言ったとき
- developer message / system 相当 / user message / tool description / agent instructions を新規作成・修正するとき
- OpenAI Responses API / Chat Completions API を使うアプリの prompt を設計するとき
- GPT-4.x → GPT-5 / GPT-5 → GPT-5.5 への移行で prompt を更新するとき
- ユーザーが「OpenAI のベストプラクティスに従って…」「prompt-guidance に沿って…」と明示したとき
- Codex CLI / Codex 拡張で内部の prompt を組み立てるとき（ただし `codex:gpt-5-4-prompting` skill がある場合はそちらを優先）

**使わない場面:**

- Claude / Anthropic 用の prompt → `writing-claude-prompts` を使う
- Gemini など他社 LLM 用 → そのモデル固有の reference を使う
- 単に文章を書くタスク（prompt 設計を含まない）

## Core Patterns

### 1. 7 要素スキャフォールド

OpenAI 公式の Suggested Framework。順序通りに書くと outcome-first の prompt が自然に組み上がる。

| 要素 | 内容 | 例 |
|------|------|----|
| **Role** | 1〜2 文で機能と context を定義 | "You are a customer-support agent for a SaaS billing system." |
| **Personality** | トーン / 振る舞い / 協働スタイル | "Patient, respectful, practical. Assume the user is competent and acting in good faith." |
| **Goal** | ユーザーから見えるアウトカム | "Resolve the customer's issue end to end." |
| **Success criteria** | 最終回答前に true でなければならない条件 | "Eligibility decision is made from policy and account data; allowed action is completed before responding." |
| **Constraints** | policy / safety / evidence / 副作用の制限 | "No refunds over $100 without manager approval. Cite policy IDs." |
| **Output** | セクション / 長さ / トーン | "Single message under 200 words, plain paragraphs." |
| **Stop rules** | retry / fallback / abstain / ask / stop の判断 | "If account data is unavailable, ask the user for the order ID instead of guessing." |

### 2. Outcome-first vs. Process-heavy

```text
# ❌ NG: process-heavy（GPT-5.5 が窮屈になる）
First inspect A, then inspect B, then compare every field,
then think through all possible exceptions, then decide which tool to call.

# ✅ OK: outcome-first
Resolve the customer's issue end to end.
Success means: the eligibility decision is made from available policy and
account data; any allowed action is completed before responding.
```

step-by-step が必要なのは「path 自体がプロダクトの一部」（規制対応 / 監査ログ / 教育アプリ）に限る。

### 3. メッセージロールの階層

| ロール | 用途 | 優先度 |
|--------|------|--------|
| **`developer`** | アプリ開発者の指示（旧 `system`） | 最高 |
| **`user`** | エンドユーザー入力 | 中 |
| **`assistant`** | モデル応答 | — |
| **`instructions` API param** | 振る舞いの上位ガイダンス（input prompt より優先） | developer 相当 |

`developer` を「関数定義」、`user` を「関数引数」と捉える。GPT-5.5 では `developer` を前方、`user` を後方に置くのが基本。

### 4. Markdown と XML の使い分け

| 目的 | 使うもの |
|------|----------|
| 階層 / セクション分け / 一覧 | **Markdown**（`##` 見出し、`-` リスト、表） |
| コンテンツ境界（参照ドキュメント / 例 / 入力データ） | **XML タグ**（`<reference_docs>`, `<example>`, `<input>`） |
| 複雑な指示ブロック | **XML タグ**（`<output_contract>`, `<verbosity_controls>` 等） |
| インラインコード / ファイルパス / コマンド | バッククォート |

XML タグは **一貫した命名** を使う。属性で metadata を表現できる（例: `<document index="1" source="policy.md">`）。

### 5. 推奨セクション順

```text
# 1. Identity         — Role, purpose, style, high-level goals
# 2. Instructions     — Rules, do's/don'ts, constraints, stop rules
# 3. Examples         — Input/Output pairs (few-shot)
# 4. Context          — Reference docs, proprietary data, retrieved chunks
# 5. User input       — 最後（ここに実際のクエリが来る）
```

再利用される部分（Identity / Instructions / Examples）を前方に置くと、Responses API の **prompt caching** が効いてコストとレイテンシが下がる。

### 6. Few-Shot Examples

3〜5 個の多様な input/output を `developer` メッセージ内に置く。XML タグで明示的に区切る。

```xml
<examples>
  <example>
    <product_review>This blender is loud but powerful.</product_review>
    <assistant_response>{"sentiment":"mixed","aspects":["noise","power"]}</assistant_response>
  </example>
  <example>
    <product_review>Stopped working after a week.</product_review>
    <assistant_response>{"sentiment":"negative","aspects":["reliability"]}</assistant_response>
  </example>
</examples>
```

エッジケース（曖昧 / 短すぎ / 多言語）も含める。

### 7. Reasoning Effort

| effort | 用途 | 備考 |
|--------|------|------|
| `none` | レイテンシ最優先 / 推論不要 | デフォルト化禁止 |
| `low` | レイテンシ感度高 + 複雑な指示あり | 短い指示・分類タスク |
| `medium` | **GPT-5.5 のデフォルト** | 品質 / レイテンシ / コストのバランス |
| `high` | eval で測れる優位がある時 | 多段推論 / 難問解決 |
| `xhigh` | 長時間 agentic タスクで知性 > 速度 | デフォルト化禁止。事前に `<completeness_contract>` `<verification_loop>` `<tool_persistence_rules>` を入れること |

```python
# 例: Responses API
response = client.responses.create(
    model="gpt-5.5",
    reasoning={"effort": "medium"},
    input=[{"role": "developer", "content": developer_msg}, ...],
)
```

### 8. Verbosity Control

GPT-5.5 のデフォルト文体は **concise & direct**。

```python
text={"verbosity": "low"}    # 既にデフォルトが簡潔なので、さらに削るとき
text={"verbosity": "medium"} # 通常
text={"verbosity": "high"}   # 説明・教育用途で長くしたいとき
```

カスタマー向けで温かさが欲しい場合は `developer` 側で **personality を明示**（GPT-5.5 のデフォルトは事務的になりがち）。

### 9. Tool Preambles（ストリーミング応答性）

複数ステップの tool 呼び出しで「最初の tool call 前に短い user-visible なステータスを出す」ことで、ストリーミング UI の体感速度が上がる。

```text
Before your first tool call, send a short user-visible update that acknowledges
the request and states the first step you will take. After each notable tool
call, briefly state what you learned and what you will do next.
Do NOT add a preamble for trivial tool calls.
```

### 10. Phase Parameter（Responses API）

`previous_response_id` ではなく出力アイテムを毎ターン手動で渡し直す運用では、assistant 出力に乗っている `phase` を **そのまま保持して送り返す**。

| phase | 意味 |
|-------|------|
| `commentary` | 中間アップデート（「いま X を調べています」） |
| `final_answer` | 最終回答 |

- user メッセージには **phase を付けない**
- reasoning effort / preamble / 繰り返し tool 呼び出しがある場合は特に重要

### 11. Tool Use の規律

```xml
<tool_persistence_rules>
- Decompose multi-step requests into sub-tasks before calling tools.
- After each tool call, reflect on the result before continuing.
- Confirm each sub-task is complete before yielding control to the user.
- When uncertain, prefer one targeted tool call over several speculative ones.
- Do not invent tool arguments. If a required parameter is missing, ask the user.
</tool_persistence_rules>
```

並列呼び出しは **依存がないとき** だけ明示する。GPT-5.5 はデフォルトで控えめなので、並列を引き出したい場合のみブロックを入れる。

### 12. Citation / Grounding

ドキュメント参照ベースで答えさせる場合は retrieval budget を明示する。

```xml
<citation_rules>
For ordinary Q&A, start with one broad search using short, discriminative
keywords. If the top results contain enough citable support for the core
request, answer from those results without searching again.

Cite using inline markers like [doc:NAME §SECTION]. Do not cite passages you
did not actually retrieve.

If the available evidence is insufficient, say so explicitly and ask the user
for the missing piece. Do not infer "no" from absence of evidence.
</citation_rules>
```

### 13. Coding Tasks

```xml
<output_contract>
- Implement the requested change as a minimal patch.
- Add or update unit tests covering the new behavior.
- Run the most relevant validation available: targeted unit tests, type checks,
  lint checks, or minimal smoke tests.
- Report the validation command and its result.
- If validation fails, fix or roll back; do not paper over with broad excepts
  or silent defaults.
</output_contract>

<default_follow_through_policy>
Prefer making progress over stopping for clarification when the request is
already clear enough to attempt. Use context and reasonable assumptions to
move forward, and surface assumptions in the final report.
</default_follow_through_policy>
```

### 14. Frontend Engineering

GPT-5.5 推奨スタック: **Tailwind CSS / shadcn/ui / Radix Themes / Lucide icons / Motion**。

zero-to-one アプリ生成時は、AI 生成によくあるデフォルト（紫グラデ、Inter、center-aligned hero）を明示的に避けさせる。

```text
Avoid the following common generated-UI defaults:
- Purple gradients on white or dark backgrounds
- Inter / Roboto / system-ui as the only typeface
- Center-aligned hero with a single CTA and a placeholder illustration
- Card grids with no information density
Use a typographic system with at least one display face and one body face,
a constrained palette tied to the product, and component states (hover,
focus, disabled, loading, empty, error) explicitly defined.
```

### 15. Customer-Facing Workflows

```text
Persona: friendly senior support agent.
Channel: in-app chat.
Register: warm, plain-spoken, no jargon.
Format: prose only — no headers, no bullet lists, no bold.
Length: max 120 words.
```

「フォーマットを禁止する」「ハードな length 上限」を **明示**。GPT-5.5 はデフォルトで markdown を出す傾向があるので、prose 限定なら明示的に banned formatting を書く。

### 16. Research / Synthesis

```text
For research tasks, use the minimum evidence sufficient to answer correctly,
cite it precisely, then stop. If evidence is insufficient, say so and ask;
do not pad the answer with speculation.
```

### 17. Creative Drafting Guardrails

```text
Use retrieved or provided facts for concrete product, customer, metric,
roadmap, date, capability, and competitive claims, and cite those claims.
Do not invent specific names, first-party data claims, metrics, or customer
outcomes to make the draft sound stronger.
```

### 18. Instruction Priority と Task Update

会話途中でタスクが切り替わるアプリでは、developer 側の優先順位を明示する。

```xml
<instruction_priority>
1. Safety and policy constraints in this developer message.
2. The most recent <task_update> block in this conversation.
3. Earlier developer instructions.
4. User instructions.
When in conflict, follow the higher-priority source and tell the user briefly.
</instruction_priority>
```

タスク変更時は新しい `<task_update>` ブロックを developer 側で送る。

## Quick Reference（チェックリスト）

GPT-5.5 用 prompt を書き終わったら確認:

- [ ] **Outcome-first**: destination / success criteria / stop rules を書いたか
- [ ] **7 要素**: Role / Personality / Goal / Success / Constraints / Output / Stop が揃っているか
- [ ] **メッセージロール**: developer / user の優先順位を意識しているか
- [ ] **構造順序**: Identity → Instructions → Examples → Context → User input
- [ ] **Markdown と XML**: 階層は markdown、コンテンツ境界は XML タグ
- [ ] **Few-Shot**: 3〜5 個の例、エッジケース含む、`<example>` でラップ
- [ ] **絶対ルール**: `ALWAYS / NEVER / must / only` を invariant にだけ使ったか
- [ ] **Stop rules**: retry / fallback / abstain / ask / stop の判断を書いたか
- [ ] **Reasoning effort**: 明示したか（デフォルト `medium`、`xhigh` は乱用しない）
- [ ] **Verbosity**: 必要に応じて `low` / `medium` / `high` を指定したか
- [ ] **Preamble**: ストリーミング UX が要るならステータスアップデートを書いたか
- [ ] **Phase**: Responses API で手動 state 管理なら phase 保持を書いたか
- [ ] **Tool persistence**: 反映 / 確認 / 引数捏造禁止を書いたか
- [ ] **Citation / Evidence**: retrieval budget と「missing-evidence ≠ no」を書いたか
- [ ] **モデル ID**: `gpt-5.5` / `gpt-5` を正しく書いたか

## Workflow（promptを作るときの手順）

1. **目的確認**: 何を達成したい prompt か / どのモデル / どの effort / どの verbosity / 入出力フォーマットは何か をユーザーに聞き取り
2. **outcome 設計**: 「これが揃ったら成功」を 1 行で書けるまで詰める
3. **7 要素の骨格**: Role / Personality / Goal / Success / Constraints / Output / Stop の見出しで草稿
4. **構造化**: Identity → Instructions → Examples → Context の順に並べる
5. **Examples**: 3〜5 個の `<example>` を組み込む（必要なら）
6. **Reference docs**: 大きな参照は `<reference_docs>` で前方配置（cache 効率化）
7. **API knobs**: reasoning effort / verbosity / phase / preamble の必要性を判定して付与
8. **Anti-pattern チェック**: 絶対ルール濫用 / process-heavy / stop rule 欠如 を取り除く
9. **チェックリスト** で自己レビュー
10. **モデル別微調整**: GPT-5.5 なら concise デフォルトに合わせる、GPT-5 / 5.1 互換が要るなら effort のデフォルト差を考慮

## Common Mistakes

| よくある間違い | 修正 |
|----------------|------|
| `Step 1: ... Step 2: ... Step 3: ...` で全工程を規定する | outcome / success criteria / stop rules に置き換え。path はモデルに任せる |
| `ALWAYS`, `NEVER`, `MUST` を多用 | 真の invariant にだけ使う。それ以外は通常の declarative に書く |
| stop rules を書かない | 「retry / fallback / abstain / ask / stop」の判断を必ず明示 |
| markdown を全面的に禁止する単発指示 | banned formatting を箇条書きで列挙＋ length 上限を併記 |
| `system:` ロール名で書く | GPT-5.5 / Responses API では `developer` ロールに変更 |
| reasoning effort を書かず `xhigh` を恒常使用 | デフォルト `medium`。`xhigh` は agentic 長時間タスク限定 |
| `previous_response_id` 不使用かつ phase を返さない | 手動 state 管理時は assistant の phase を保持して再送 |
| evidence 不足時に「no」と答えてしまう | citation_rules で「missing ≠ no」「不足したら ask」と明示 |
| 並列ツール呼び出しが起きない | 依存なしの場合のみ並列を許可するブロックを developer に追加 |
| 創作で固有名詞・指標を捏造する | source-backed と creative wording を分離するガードを書く |
| customer-facing で素っ気ない | personality を明示。GPT-5.5 デフォルトは事務的 |
| `<example>` ラップなしで例を貼る | `<example>` / `<examples>` で構造化する |
| 長文ドキュメントを末尾に置く | 前方配置（Identity / Instructions の直後）。prompt cache が効く |

## Reference Snippets

そのまま埋め込める実用ブロック集。コピペして使う。

### A. Output Contract（汎用）

```xml
<output_contract>
- Format: <plain prose | markdown sections | JSON matching schema>.
- Length: <hard limit, e.g. ≤ 200 words>.
- Sections: <ordered list of required sections, or "single message">.
- Tone: <e.g. patient, plain-spoken, no jargon>.
- Banned: <e.g. headers, bullet lists, emojis> (when prose-only is required).
</output_contract>
```

### B. Verbosity Controls（developer 側で固定したい場合）

```xml
<verbosity_controls>
Default to concise, direct prose. Do not restate the user's question.
Do not add closing pleasantries. Use bullets or tables only when the content
is genuinely list-like or tabular. Each paragraph should end when the point
is made — no padding sentences.
</verbosity_controls>
```

### C. Default Follow-Through Policy

```xml
<default_follow_through_policy>
Prefer making progress over stopping for clarification when the request is
already clear enough to attempt. Use context and reasonable assumptions to
move forward, and surface those assumptions in the final report. Ask for
clarification only when the missing information would change the outcome.
</default_follow_through_policy>
```

### D. Tool Persistence Rules

```xml
<tool_persistence_rules>
- Decompose multi-step requests into sub-tasks before calling tools.
- After each tool call, reflect on the result before continuing.
- Confirm each sub-task is complete before yielding control to the user.
- When uncertain, prefer one targeted tool call over several speculative ones.
- Do not invent tool arguments. If a required parameter is missing, ask.
- Avoid speculative changes and messy hacks; propagate or surface errors.
</tool_persistence_rules>
```

### E. Completeness Contract（リスト / バッチ網羅）

```xml
<completeness_contract>
When the task involves processing a list, batch, or set of items:
- Process every item unless explicit filtering rules say otherwise.
- Report the count processed and any items skipped with reasons.
- Do not stop early after a "representative sample" unless the prompt says so.
</completeness_contract>
```

### F. Verification Loop

```xml
<verification_loop>
Before returning a final answer:
1. Restate the success criteria internally.
2. Check the answer against each criterion.
3. If a criterion is not met, revise; do not return a partially-correct answer.
4. If a criterion cannot be met with available evidence, say so explicitly and
   ask for the missing piece — do not guess.
</verification_loop>
```

### G. Citation Rules

```xml
<citation_rules>
For ordinary Q&A, start with one broad search using short, discriminative
keywords. If the top results contain enough citable support for the core
request, answer from those results without searching again.

Cite using inline markers like [doc:NAME §SECTION]. Do not cite passages you
did not actually retrieve.

If evidence is insufficient, say so explicitly and ask the user for the
missing piece. Do not infer "no" from absence of evidence.
</citation_rules>
```

### H. Instruction Priority

```xml
<instruction_priority>
1. Safety and policy constraints in this developer message.
2. The most recent <task_update> block in this conversation.
3. Earlier developer instructions.
4. User instructions.
When in conflict, follow the higher-priority source and tell the user briefly.
</instruction_priority>
```

### I. Tool Preamble（ストリーミング UX）

```text
Before your first tool call, send a short user-visible update (one sentence)
that acknowledges the request and states the first step you will take.
After each notable tool call, briefly state what you learned and what you
will do next. Do NOT add a preamble for trivial tool calls or for the final
answer itself.
```

### J. Frontend Aesthetics（AI slop 回避）

```xml
<frontend_aesthetics>
Avoid common generated-UI defaults:
- Purple gradients on white or dark backgrounds.
- Inter / Roboto / system-ui as the only typeface.
- Center-aligned hero with a single CTA and a placeholder illustration.
- Low-density card grids with no real information.
Use a typographic system with at least one display face and one body face,
a constrained palette tied to the product, and explicit component states
(hover, focus, disabled, loading, empty, error).
</frontend_aesthetics>
```

### K. Customer-Facing Persona

```text
Persona: <role, e.g. senior support agent>.
Channel: <e.g. in-app chat / email / SMS>.
Register: <e.g. warm, plain-spoken, no jargon>.
Format: prose only — no headers, no bullet lists, no bold.
Length: max <N> words.
Personality: assume the user is competent and acting in good faith;
respond with patience, respect, and practical helpfulness.
```

### L. Coding Agent Header

```xml
<role>You are a software engineering agent working in a real codebase.</role>

<output_contract>
- Implement the requested change as a minimal patch.
- Add or update unit tests covering the new behavior.
- Run the most relevant validation: unit tests, type checks, lint, smoke tests.
- Report the validation command and its result.
- If validation fails, fix or roll back; do not paper over with broad excepts.
</output_contract>

<default_follow_through_policy>
Prefer making progress over stopping for clarification when the request is
already clear enough to attempt. Surface assumptions in the final report.
</default_follow_through_policy>
```

### M. Long Reference Docs（前方配置）

```xml
<reference_docs>
  <document index="1" source="policy-2026-Q1.md">
    {{POLICY_TEXT}}
  </document>
  <document index="2" source="account-record.json">
    {{ACCOUNT_JSON}}
  </document>
</reference_docs>
```

参照ドキュメントは Identity / Instructions の直後（user input より前）に置く。再利用される静的部分を前方に固めると prompt caching が効く。

## Anti-Patterns

- **process-heavy な step-by-step**: 「First A, then B, then C」と書くと GPT-5.5 が窮屈になる。outcome を書く
- **絶対ルールの濫用**: `ALWAYS / NEVER / MUST / ONLY` を装飾的に使うと、本当に守るべき invariant が埋もれる
- **stop rules の欠如**: 「いつ retry する」「いつ ask する」「いつ stop する」が無いと、agentic 設定で暴走しやすい
- **silent default で誤魔化す**: 例外を握り潰したり、evidence なしで「no」と答えるのは禁則
- **`system:` ロール名**: Responses API / GPT-5.5 では `developer` ロール
- **`xhigh` をデフォルト化**: コスト / レイテンシが膨れる。長時間 agentic タスク限定
- **ロングドキュメントを末尾に置く**: cache 効率を落とす。前方に置く
- **markdown 全面禁止だけ書く**: 「禁じる formatting」を列挙し、length 上限を併記
- **創作で固有名詞 / 指標を捏造**: source-backed と creative wording を分離するガードを書く
- **`<example>` 無しで貼る**: 構造化されないと few-shot が効きにくい
- **phase を user に付ける**: assistant 側のみに保持。user メッセージに足してはならない

## GPT-5.5 vs GPT-5 / 5.1 の差分（移行時の注意）

| 項目 | GPT-5 / 5.1 | GPT-5.5 |
|------|-------------|---------|
| reasoning effort のデフォルト | 明示が無いと不定 | `medium` がデフォルト |
| 文体のデフォルト | 通常 | concise & direct |
| phase parameter | 任意 | Responses API で重要 |
| outcome-first 推奨度 | 推奨 | **強く推奨**（process-heavy で性能低下） |
| markdown の出方 | 多め | 控えめ |
| customer-facing の温かさ | 自然に出る | personality 明示が要る |

GPT-5 / 5.1 で動いていた process-heavy な prompt は、GPT-5.5 で **必ず outcome-first にリファクタ**する。「step 1 でやりすぎ・step 2 でサボる」のような偏りが出やすい。

## Bottom Line

> 「GPT-5.5 はシニアの同僚。destination を渡せば path は自分で選ぶ。junior 向けの細かい手順書を渡すと、かえって遅く / 浅くなる。」

**outcome を定義する。constraints を絞る。stop rules を必ず書く。** これが GPT-5.5 を最大限引き出す方法。
