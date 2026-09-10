---
name: writing-claude-prompts
description: Use when authoring or refining a prompt for Claude (system prompt, user message, tool description, agent instructions) to make it follow Anthropic's official prompt engineering best practices — covers clarity, XML structure, few-shot examples, role, long-context layout, output format control, tool-use phrasing, and effort/adaptive-thinking knobs for the Claude 5 family (Fable 5.1 / Sonnet 5 / Opus 5).
---

# Writing Claude Prompts

## Overview

Anthropic 公式の prompt engineering best practices（Claude 5 family — Fable 5.1 / Sonnet 5 / Opus 5 / Haiku 4.5 — を含む現行モデル向け）に従って prompt を組み立てるための reference。

**Golden Rule（黄金律）:**
> プロンプトをタスクに関する最小限のコンテキストを持つ同僚に見せて、それに従うよう求めてください。彼らが混乱していたら、Claude も混乱します。

**核となる原則:**
- 望ましい動作は推測させず明示的に書く
- XML タグで指示・コンテキスト・入力・例を区別する
- 例は 3〜5 個、関連性・多様性・構造化された形で
- 長いコンテキストはドキュメントを上、クエリを下
- 「やらないで」より「こう書いて」（肯定的な指示）

**公式リファレンス:**
- 全モデル共通: https://platform.claude.com/docs/ja/build-with-claude/prompt-engineering/claude-prompting-best-practices
- Fable 5.1 固有: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-1

## When to Use

以下の場面で発火する:

- ユーザーが「prompt を書いて／作って／改善して／レビューして」と言ったとき
- system prompt / agent instructions / tool description を新規作成・修正するとき
- LLM 駆動アプリ（Anthropic SDK / Claude API）の prompt を設計するとき
- 既存 prompt が想定通り動かないので調整したいとき
- 旧世代モデル → Claude 5 family（Fable 5.1 / Sonnet 5 / Opus 5）への移行で prompt を更新するとき
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

**Fable 5.1 の向き:** 旧モデルは chat で bullet と太字を出しすぎたため抑制指示が広く書かれたが、Fable 5.1 は逆に振れており、太字・見出し・リストを控えめにする。chat 用途で構造が足りないと感じたら抑制指示を消すか、「使ってよい条件」を書いた規則（Snippet R）へ置き換える。レポート・長文ドキュメント生成での Snippet A は引き続き有効。

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

`effort` は intelligence / latency / cost のトレードオフを制御する主レバー。**Fable 5.1 / Sonnet 5 / Opus 5 はいずれも thinking 既定 ON（adaptive）**。Opus 5 は effort `high` 以下でのみ thinking を無効化できるが、無効化するより低い effort で回すほうが同コストで性能が出る（無効化時の副作用は項目 17）。`budget_tokens` による手動 extended thinking は使わず `effort` + `thinking: {type: "adaptive"}` に寄せる（Fable 5.1 / Mythos 5.1 / Sonnet 5 では 400 エラー）。

| モデル | effort の既定 | 早見表 |
|--------|--------------|--------|
| **Fable 5.1** | thinking 既定 ON。既定 `high` から始め、`low` / `medium` / `xhigh` / `max` を自前の eval で掃き直す | **effort 名の意味はモデル間で移らない**ので他モデルの掃き結果を流用しない。`medium` でも実用品質が出ることが多く、`low` はコスト当たりで Opus / Sonnet を上回る一方、検索・retrieval tool の呼び出しが減る。`xhigh` / `max` は長い成果物で thinking が伸びるため既定は `high` |
| **Sonnet 5** | thinking 既定 ON。既定 `high`（4.6 と同じ）。最難関のコーディング・エージェントタスクは `xhigh` へ | `low`/`medium` では**文字通りスコープ厳守**で動くため under-thinking のリスクがある。複雑な問題で浅い推論が見えたら、プロンプトで誤魔化さず effort を上げる |
| **Opus 5** | thinking 既定 ON。既定 `high` から始め、`low` / `medium` を token とレイテンシの第一レバーとして積極的に使う。難度の高い coding / agentic だけ `xhigh` へ上げる | 前モデルから effort 既定を持ち越したなら自前の eval で sweep し直す。code review は低い effort でも精度が落ちにくいので、速い 1 パス + 後で厚いパスという構成が取れる。1M context が既定かつ上限で、窓全域で指示追従・tool 呼び出しが安定する |

いずれのモデルも `low`/`medium` は「頼まれたこと」に厳密にスコープを絞る（over-and-beyond をしない）。`max`/`xhigh` 実行時は `max_tokens` を **64k** から始めて調整する。プロンプト側で過度に思考しすぎる場合（大きい/複雑な system prompt でよく起きる）は以下で抑制:

```text
拡張思考は遅延を追加し、回答品質を有意に改善する場合にのみ使用してください。
通常、マルチステップ推論を必要とする問題の場合です。疑わしい場合は、直接応答してください。
```

### 11. プリフィル応答の廃止（Claude 4.6 以降 — Claude 5 family も含む）

Claude 4.6 系以降の全モデル（**Fable 5.1 / Mythos 5.1 を含む**）で、assistant の prefilled response（最後の assistant ターンへの部分応答の事前投入）は**非サポート**。使うと 400 エラーになる（単なる非推奨ではなく実際に壊れる）。代替:

| 旧用途 | 新代替 |
|--------|--------|
| JSON / YAML 強制 | [Structured Outputs](https://platform.claude.com/docs/ja/build-with-claude/structured-outputs) / Tool use |
| 前置き排除 | `Respond directly without preamble. Don't start with "Here is..."` |
| 拒否回避 | 不要（モデルが改善された） |
| 継続 | user メッセージに `Previous response was truncated, ending at \`[...]\`. Continue from where you left off.` |

### 12. モデル別の注意点（Claude 5 family）

**Fable 5.1:** 1ターンが数分〜数時間続く long-horizon autonomy が既定なので、クライアントタイムアウト・進捗表示を前提から見直す。instruction-following が非常に強く、簡潔な1文で複数の振る舞いを制御できるため、checkpoint/gate の個別列挙は「本当に必要な時だけ止まる」の一般原則へ集約してよい。サブエージェント委譲を積極的に行い、orchestrator は完了をブロッキング待ちしない（項目 16）。教訓をファイルへ記録するメモリシステムとの親和性も高い。調整が要りやすいのは次の 6 点で、症状別の対処は「Fable 5.1 固有の調整」節にある: ①ツール呼び出し中のユーザー向け進捗テキストが少ない、②coding / computer-use ループで並列ツール呼び出しが 1 ターン 1 件になることがある、③会話履歴の append-only が必須（thinking ブロックが生成した会話に束縛される）、④散文が密になりがちで、逆に chat の構造化は控えめ、⑤小さな変更でもファイル全体を書き直しがち、⑥`low` effort で検索せず記憶で答えがち。安全分類器の false positive は少なく、**ソースコードの脆弱性発見は許可**されている（誤検知を招きやすいのは「コンパイルが通るか」という問い方・マイナー言語・tool 出力の base64 の 3 つ）。既存 prompt/skill は過剰に prescriptive になりがちなので、デフォルト性能の方が良ければ古い指示は削ってよい。内部 thinking を応答テキストへ書き起こさせる指示は置かない（必要なら構造化 `thinking` ブロックを読む）。

**Sonnet 5:** 応答の冗長度はタスクの複雑さに応じて自動調整される（固定 verbosity が要る場合のみ追加指示）。`low`/`medium` effort では文字通りスコープ通りに動くため under-thinking リスクがある。より文字通りに(literal)指示に従い、ある項目への指示を他の項目に暗黙に一般化しない（範囲を広げたいなら「すべてのセクションに適用」等と明示）。`temperature`/`top_p`/`top_k` の非デフォルト値指定は 400 エラー（Sonnet 系で新しい制約）なので、スタイルの多様性はプロンプトで誘導する。

**Opus 5:** thinking 既定 ON。旧世代向けに書いた prompt はそのままでも良く動くが、調整が要りやすいのは次の 6 点。①ユーザー向け応答・作業中の narration・ディスクに書く成果物がいずれも長くなりがち（effort を下げても可視応答は短くならないので、簡潔さは明示指示で制御する: Snippet U）。②**自己検証を指示しなくても行う**ため、「最後に検証ステップを入れよ」「subagent に検証させよ」の類は削除する — 残すと over-verification になり、削っても品質は落ちない。harness 側に置いた別建ての検証段も同じ扱い。③自分のミスは指示なしで拾って直す一方、過去の発言の訂正を過剰に語る（Snippet X）。④タスクのスコープを自分の判断で広げることがあるので、狭いタスクでは明示的に絞る（Snippet V）。⑤subagent 委譲が多い。大きく独立して並列化できる作業だけに限り、自分の作業の二重確認には使わせない（Snippet W）。Claude Code / Agent SDK なら `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` / `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS` / SDK の `max_budget_usd` で決定論的な上限も掛けられる（Claude Code 2.1.217 以降）。⑥vision は chart / document / UI 再現に強く、旧モデル向けに入れた回避策は不要になっていることが多いので棚卸しする。thinking を無効化して運用する場合の副作用は項目 17。

**全モデル共通のコードレビュー注意**: 「high-severity のみ報告」「be conservative」等の指示は、現行モデルほど忠実に守りすぎて低重要度バグの報告を絞りすぎることがある（recall 低下に見えるが実態はハーネス効果）。`Report all issues you find, including ones you're uncertain about... Your goal is coverage.` で検出と報告のフェーズを分離すると復旧する。

### 13. 自律性 vs 安全性（エージェント）

長時間タスクで破壊的操作（rm / push --force / DB drop 等）を勝手にさせない:

```text
逆転が難しい、共有システムに影響を与える、または破壊的である可能性のあるアクションについては、
進める前にユーザーに確認してください。
```

Fable 5.1 のような長時間自律実行モデルでは、これに加えて「境界の明示」（問題の説明・質問には修正せず報告して止まる／システム状態を変える前に証拠が対象アクションを裏付けているか確認する）と、「進捗の証跡裏取り」（各主張をツール結果と突き合わせ、未検証は明示し、失敗は失敗と述べる）が有効性の確認された具体パターンとして推奨されている。後者は Anthropic の検証で、捏造された進捗報告を狙って誘発するタスクでもほぼ根絶したと報告されている。長時間の自律実行を任せる agent instructions では明示的に含める価値が高い。

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

### 16. サブエージェント委譲とメモリ（Fable 5.1 で特に有効）

Fable 5.1 は前世代より積極的に並列サブエージェントを dispatch する。委譲判断の基準（独立サブタスクは委譲し、完了を待つ間も作業を続ける。介入は脱線・情報不足時のみ）を明示すると効果が上がる。長時間実行での自己検証は、自己批判より**フレッシュコンテキストの verifier subagent**の方が有効性が高いと報告されている（「一定間隔でサブエージェントに仕様との突き合わせ検証をさせる」）。ハーネス側の作りとしては、subagent 起動 tool を即 return させ、結果は後続の user メッセージで lead へ渡し、待ちたい時用の tool を別に用意する — コーディングタスクでは lead を待たせないほうが品質・トークン・コストを保ったまま平均完了時間が縮む。

Fable 5.1 はセッションをまたぐ教訓の記録・参照とも相性が良い。**1教訓1ファイル・先頭に一行要約**、修正内容と確認済みアプローチを理由付きで記録、重複作成せず更新、誤りは削除、というメモリシステムの具体形が推奨されている（このリポジトリの `~/.claude/.../memory/` 運用と一致するパターン）。

### 17. thinking を無効化する場合の注意（Opus 5）

Opus 5 は thinking 既定 ON で、無効化できるのは effort `high` 以下のときだけ。**無効化より低い effort で回すほうが同コストで性能が出る**ので、まず effort を下げる方を試す。どうしても無効化する場合、可視応答に 2 種類の副作用が出ることがある。

- **tool 呼び出しがテキストとして漏れる**: 構造化 `tool_use` ブロックではなく本文に tool 呼び出しを書いてしまう。呼び出しは実行されず、agent ループでは漏れたテキストが履歴に残って後続ターンにも影響する。search のような tool 依存のワークロードで起きやすい。
- **内部 XML タグが出力に混ざる**: `<thinking>` などが可視応答に現れる。system prompt に「考えるな」「推論するな」という規則があると悪化するので削除する。

両方の緩和は Snippet Y の 1 ブロックで足りる。タグ名を名指しする指示（「`<thinking>` を出すな」）は一般形より効きが悪いので使わない。

## Fable 5.1 固有の調整

ここは**観測した症状から引く**節として使う。左列の症状が出ていなければ何も足さない。

| 症状 | 対処 |
|---|---|
| effort をどれにするか決まらない / 遅い・高い | 既定 `high` から始め、`low` / `medium` / `xhigh` / `max` を自前の eval で掃き直す。effort 名の意味はモデル間で移らないので他モデルの結果を流用しない |
| ツール呼び出しの合間にユーザー向けテキストが出ない | まず progress-update `thinking` ブロックを受け取れているか確認する（`thinking.display` の既定 `"omitted"` では空。beta header `thinking-display-updates-2026-08-18` で `display: "updates"`、`"summarized"` でも届く）。次に「所見は最終応答まで溜めろ」系の抑制指示を消す。それでも足りなければ Snippet S |
| coding / computer-use ループで 1 ターン 1 ツールになる | Snippet Q を、tool_result を返す user メッセージの直後に turn-scoped system message（`clear_at: "next_user_message"`、beta header `mid-conversation-system-clear-at-2026-08-21`）として毎ターン追記する。beta が使えなければ同じ user メッセージの `tool_result` ブロックの後ろに text ブロックとして置く |
| `bound to a different conversation` の 400 / cache が毎回落ちる | 会話履歴を append-only にする。thinking ブロックは生成した会話に束縛される（2026-08-31 以降作成のアカウントで強制、将来モデルは全アカウントで強制予定）。per-turn reminder の差し込みと削除、過去ターンの要約差し替え、session 途中の system prompt 変更をやめ、trim は server-side compaction / context editing に任せる。client 側で compact するなら履歴全体を要約 1 通 + 新しい user ターンに置き換え、thinking ブロックは持ち越さない |
| 散文が長く密で段落が少ない | Snippet M を user メッセージ（推奨）か system に足す |
| chat の構造化が足りない（太字・箇条書き・見出しが出ない） | 旧モデル向けの抑制指示を消す。必要なら Snippet R のように「使ってよい条件」を書いた規則に置き換える |
| 要約が出典の原文を引用と示さず引き写す | 正しい応答の**完全な例を 1 つ**（user 発話 + 応答 + なぜ正しいかの説明）system prompt に入れる。例中の tool 呼び出し行は自分の tool 名に書き換え、モデルが文字列として出力しないようにする |
| 依頼済みの作業の途中で許可を求めて止まる / 「次に〜します」で終わる | Snippet L の 2 ブロックを入れる（長さを削るなら前半だけでも大半の効果）。前半冒頭の「ユーザーは見ていない」の 1 文は原文のまま残す |
| client 側 compaction で制約・決定・固有名が落ちる | Snippet O を要約指示に使う（server-side compaction は対応済み） |
| 頼んでいない修正・過剰なテストファイルが混ざる | Snippet N。タスクが求めた挙動は完全に実装させる一文を必ず残し、萎縮させない |
| `low` effort で検索せず記憶で答える | 該当ターンだけ effort を上げる（mid-conversation の effort 変更）か、Snippet T を system に足す |
| 良性のコードタスクが `stop_reason: "refusal"` になる | 「コンパイルは通るか」→「バグはあるか」に言い換える / マイナー言語は仕様書へのアクセスを与える / tool 出力の base64 を除去する |
| 小さな変更でファイル全体を書き直す | Snippet P 前半を system か最初の user メッセージに足す |
| `xhigh` / `max` で長い成果物が遅い・`max_tokens` に当たる | 既定の `high` に戻すのが第一選択。上げるなら `max_tokens` を thinking + 応答の合計で確保し、Snippet P 後半を user メッセージ末尾に足す |
| lead agent が subagent の完了を待って遊ぶ | subagent 起動 tool を即 return させ、結果は後続 user メッセージで渡し、待つための tool を別に用意する（項目 16） |
| 密なチャート・画像の読み取りが粗い | crop / zoom できる tool、または PIL / OpenCV 入りのコンテナを渡す。crop tool 単体でも効果の大半が出る |

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
- [ ] **思考設定**: `effort` を明示したか（`budget_tokens` ではなく `effort` + `thinking: {type: "adaptive"}`）。現行モデルは thinking 既定 ON で、Opus 5 の無効化は `high` 以下限定という前提を踏まえたか
- [ ] **プリフィルなし**: user 末尾までで完結しているか（Claude 4.6 以降は Fable 5.1/Mythos 5.1 含め全面非サポート）
- [ ] **モデル文字列**: `claude-fable-5-1` / `claude-sonnet-5` / `claude-opus-5` / `claude-haiku-4-5-20251001` を正しく書いたか
- [ ] **thinking の扱い**: 内部 thinking を応答テキストへ書き出させる指示が残っていないか（必要なら構造化 `thinking` ブロックを読む）
- [ ] **履歴 append-only**（Fable 5.1 向け）: per-turn reminder の差し込み・過去ターンの書き換えをしていないか（turn-scoped system message に寄せたか）
- [ ] **フォーマット抑制の棚卸し**（Fable 5.1 向け）: 旧モデル向けの markdown / bullet 抑制指示が chat 用途に残っていないか
- [ ] **検証指示の棚卸し**（Opus 5 向け）: 「最後に検証ステップを入れよ」「subagent に二重確認させよ」が残っていないか（over-verification になる）

## Workflow（promptを作るときの手順）

1. **目的確認**: 何を達成したい prompt か / どのモデル（Fable 5.1 / Sonnet 5 / Opus 5）/ どの effort / どんな入出力フォーマットか をユーザーに聞き取り
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
| `budget_tokens` で思考量制御 | `effort` パラメータ + `thinking: {type: "adaptive"}` に移行（Fable 5.1 / Mythos 5.1 / Sonnet 5 では `budget_tokens` 指定は 400 エラー） |
| プリフィル `assistant: "Here is the JSON: {"` | Structured Outputs / Tool use / `Respond directly without preamble.` に置換 |
| 長文の **後** にクエリを書かない | 長文を上、クエリを下（最大 30% の品質改善） |
| Sonnet 5 / Opus 5 で旧モデルと同じ「徹底的に」プロンプト | 現行モデルは文字通り解釈する。スコープを明示し、過剰な「徹底」指示は削る |
| AI slop なデザインが出る | 具体的な palette / typeface を指定するか、構築前に複数案（4案程度）提案させる |
| recall が下がったコードレビュー | `Report all issues including uncertain/low-severity. Filtering happens in another step.` に書き換え |
| 説明だけで動かない | `<default_to_action>` ブロックで action を促す |
| Opus 5 の prompt / harness に検証ステップを足す | 自己検証は既定で行われる。足すと over-verification になり、削っても品質は落ちない |
| Opus 5 で応答や成果物が長い | effort を下げても可視応答は短くならない。簡潔さは Snippet U で明示する |
| agent instructions に thinking 書き起こし指示を残す | 削除し、必要なら `thinking` ブロックの構造化出力を読む |
| Fable 5.1 の checkpoint を個別列挙する | 「破壊的・不可逆・スコープ変更・ユーザーしか答えられない入力」の一般原則に集約する（項目 12 参照） |
| 他モデルで掃いた effort 設定をそのまま流用する | effort 名の意味はモデル間で移らない。`high` から掃き直す（`medium` / `low` も比較対象に入れる） |
| per-turn reminder を過去ターンへ差し込み直す | turn-scoped system message（`clear_at: "next_user_message"`）で毎ターン追記する。履歴の書き換えは cache 破棄と thinking ブロックの 400 を招く |
| 小さな修正でファイル全体を書き直させる | Snippet P 前半（surgical edit 優先）を足す |
| chat 用 prompt に旧モデル向けの markdown 抑制を残す | Fable 5.1 は元々フォーマットを控えるので、Snippet R のような条件付き規則に置き換える |

## Reference Snippets

そのまま埋め込める実用ブロック集。コピペして使う。

### A. Markdown 抑制（レポート・長文ドキュメント向け）

chat 用の prompt には入れない（Fable 5.1 は元々フォーマットを控えるため、Snippet R を使う）。

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
現在のモデルは Claude Fable 5.1 です。LLM が必要な場合は、
ユーザーが別途リクエストしない限り、Claude Fable 5.1 をデフォルトにしてください。
Claude Fable 5.1 の正確なモデル文字列は claude-fable-5-1 です。
```

他モデルのモデル文字列: Sonnet 5 = `claude-sonnet-5` / Opus 5 = `claude-opus-5` / Haiku 4.5 = `claude-haiku-4-5-20251001`。

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

### L. 自律実行を最後までやり切らせる（Fable 5.1）

長い非同期タスクで「次に〜します」と宣言して turn を終える／依頼済みの手順に許可を求める、を抑える。2 ブロックとも入れるのが既定で、長さを削るなら前半だけでも大半の効果が残る。原文ママで使う（冒頭の「ユーザーは見ていない」の 1 文が効果の中心）。

```text
You are operating autonomously. The user is not watching in real time and cannot answer questions mid-task, so asking 'Want me to…?' or 'Shall I…?' will block the work. For reversible actions that follow from the original request, proceed without asking. Stop only for destructive actions or genuine scope changes the user must decide. Offering follow-ups after the task is done is fine; asking permission before doing the work is not.

Exception: when the user is describing a problem, asking a question, or thinking out loud rather than requesting a change, the deliverable is your assessment. Report your findings and stop. Don't apply a fix until they ask for one.

Before ending your turn, check your last paragraph. If it is a plan, an analysis, a question, a list of next steps, or a promise about work you have not done ('I'll…', 'let me know when…'), do that work now with tool calls. That includes retrying after errors and gathering missing information yourself. Do not stop because the context or session is long. End your turn only when the task is complete or you are blocked on input only the user can provide.

Before running a command that changes system state (such as restarts, deletes, or config edits), check that the evidence actually supports that specific action. A signal that pattern-matches to a known failure may have a different cause.
```

```text
# Delivering work
The user's request — or the plan they approved — sets the scope, and the scope is the deliverable: don't quietly narrow, widen, or swap it. Read ambiguity the way a careful colleague would: make routine judgment calls yourself, and check in only when different readings would lead to materially different work. If you see a real problem with the task as specified, say so in a sentence or two and keep building under stated assumptions; if the user hears the concern and reaffirms, that is their decision, so deliver the full request.

If a question comes up partway, first do everything that doesn't depend on the answer; then state the assumption you made, or — when going ahead on a wrong guess would be unsafe or would make the work useless — put the question at the end of a turn that also delivers that progress. If one part turns out to be blocked, complete every other part in full and say exactly what you left out and why — the whole task is the deliverable, and scaling it down is the user's call, not yours. A step you have decided on is something to run, not to announce: describing the next step and ending the turn leaves it undone until the user replies.

Keep changes to what the request needs. Something else you notice worth doing — cleanup or documentation the task didn't call for, a change to a file the task didn't require — is a suggestion to make at the end, not a change to make; actions clearly beyond what the ask implies, and risky or destructive ones, still need the user's go-ahead.
```

このブロックは曖昧な依頼への確認も減らす方向に効くため、確認して欲しい場面がある製品では冒頭の直後に「止まるべきケース」を1文足す。

### M. 密な散文（mannered prose）の抑制

user メッセージ（推奨）か system に置く。短縮版 `Please remove all mannered prose.` でも効くことが多い。

```text
Mannered prose substitutes metaphor and flourish for direct statement. Instead of "a parameter worth varying," the mannered writer produces "a dial worth turning." Instead of "this point still matters," they write "this point earns its keep." The phrases exist to display the writer, not to convey the idea, and readers can tell. That is why mannered prose irritates: it makes the reader work harder so the writer can perform. It is also imprecise. Metaphors drag in connotations the writer did not choose and cannot control. The fix is to say what you mean. When a literal phrase is available, use it.
```

### N. スコープとテストを依頼どおりに保つ

頼まれていない周辺修正・拡張・過剰なテストファイルを抑える。最後の1文（求められた挙動は完全に実装する）を落とすと萎縮するので必ず残す。

```text
If, while working or testing, you find a pre-existing bug, a performance concern, or behavior the task doesn't mention, don't fix, optimize or extend it in this change unless the requested behavior cannot work without it; report it as a follow-up in your summary. Where the task is ambiguous, implement the reading its wording and the surrounding code most directly support, state that assumption in your summary, and don't build for the other readings as well. Verify your work however you like; scratch scripts and quick checks need not be kept. Commit tests only where the task asks for them or this repository already keeps tests for this kind of change, sized like the neighboring test files — roughly one focused test per stated behavior — and don't turn scratch checks into additional permanent test files. This is about extras only: implement every behavior the task asks for, completely.
```

### O. client 側 compaction の要約指示

server-side compaction を使う場合は不要。

```text
Summarize the transcript inside <summary></summary> tags. Include relevant information in the summary such that this conversation will be continued by a new context window without needing to redo work or be reprovided with relevant constraints or context. Be sure to preserve: (1) any difficulties or problems that came up, and how they were handled or resolved; (2) any possibilities, options, or approaches that were raised, tried, or set aside, and why; (3) anything that was asked for, decided, agreed, ruled out, or established as a preference, constraint, or boundary — stated exactly; (4) exactly where things stand now — what has been covered, settled, or completed so far; (5) anything still open, unresolved, promised, or expected to happen next; (6) specific details that would be hard to reconstruct — names, numbers, dates, exact wording, links or references — kept exactly. Be complete on these even at the cost of length; keep everything else concise. Weight the two voices differently: keep what the user said, asked for, shared, or established carefully and close to their own words; your own explanations and reasoning can be condensed much further, to what they concluded or produced — as long as nothing in the six items above is dropped.
```

### P. 出力トークンの節約（surgical edit / 長い成果物）

前半はファイル全体の書き直しを抑える（system か最初の user メッセージ）。後半は `xhigh` / `max` で長い成果物を書かせる時に user メッセージ末尾へ置き、`[max_tokens]` を実際の値（例: 64,000）に差し替える。

```text
The number of tokens used to edit files is best minimized, all else being equal. Therefore, when it will not affect the end result, try to surgically edit a file rather than rewrite the entire thing.
```

```text
Everything produced in one reply, including any reasoning or drafting it does before the reply, counts toward a single limit of about [max_tokens] tokens. If that limit is reached before the reply is finished, the person receives a cut-off response and has to start over. Composing an entire output or deliverable in full as reasoning and then again as a reply would double the length of the turn without improving the result, so don't do that.

Instead, when the person has asked for a long or effort-intensive deliverable such as a multi-section document, a large table or dataset, or a complete code file, spend extra effort on understanding the request, checking the inputs the answer depends on, settling the structure and other difficult decisions, and otherwise using the reasoning space to reason and the output space to write an output. Usually it is not needed to draft an output multiple times.
```

### Q. 独立ツール呼び出しのバッチ化（agent ループ）

tool_result を返す user メッセージの直後に turn-scoped system message として毎ターン追記する。古いコピーは消さずそのまま残す（消すと履歴の書き換えになる）。

```text
First privately list what you need next; then request every item that doesn't depend on another's result in this one response.
```

### R. chat のフォーマット規則（抑制指示の置き換え）

```text
Use lists and bullet points when asked to, or when the content is multifaceted enough that they help with clarity. If the person explicitly requests minimal formatting, always format your responses without bullet points, headers, lists, or bold emphasis, as requested. In conversational, personal, or emotional exchanges, keep to plain prose.
```

### S. 進捗更新とツール出力の見え方

前者は human-in-the-loop でユーザー向けテキストを増やしたい時。後者は tool 出力を UI が隠す製品で、モデルが「見せるため」に無駄なコマンドを打つのを防ぐ（turn-scoped system message で渡す）。

```text
Before you start, say in a line what you're about to do; brief updates while you work help the user follow along. Close with a short recap that stands on its own — what you found, what you did, and what's next — so a reader who only sees the last message has the full picture.
```

```text
Only you see that command's output — the user's terminal shows at most a few lines of it. If the user needs to read any of it, put it in your reply.
```

### T. `low` effort での検索トリガ

```text
When a query centers on a name you do not confidently recognize, or recognize from a fast-moving area like AI models and developer tools where the landscape shifts within months, the name itself is the thing to verify: search before answering, and include the name as the user wrote it in at least one query alongside any reformulations. This holds even when you have some background on it — partial background is exactly what makes an out-of-date answer sound authoritative, so familiarity is not a reason to skip the search.
```

### U. 長さの制御（Opus 5）

3 種類の「長さ」を別々に絞る。1 つ目は会話応答、2 つ目は長い system prompt の末尾に置くリマインダ、3 つ目は作業中の narration、4 つ目はディスクへ書く成果物。

```text
Keep responses focused, brief, and concise. Keep disclaimers and caveats short, and spend most of the response on the main answer. When asked to explain something, give a high-level summary unless an in-depth explanation is specifically requested.
```

```text
<tone_preference>
Keep outputs reasonably concise.
</tone_preference>
```

```text
Before your first tool call, say in one sentence what you're about to do. While working, give a brief update only when you find something important or change direction. When you finish, lead with the outcome: your first sentence should answer "what happened" or "what did you find," with supporting detail after it for readers who want it.
```

```text
Match the length of written documents to what the task needs: cover the substance, but do not pad with filler sections, redundant summaries, or boilerplate.
```

narration を増やす / 変える方向にも同じレバーが使える。その場合は「やめてほしいこと」ではなく、望むスタイルの肯定的な例を見せるほうが効く。

### V. スコープの固定（Opus 5）

```text
Deliver what was asked, at the scope intended. Make routine judgment calls yourself, and check in only when different readings of the request would lead to materially different work. If the request seems mistaken or a better approach exists, say so in a sentence and continue with the task as asked rather than quietly narrowing, widening, or transforming it. Finish the whole task, and stop short of actions that are clearly beyond what was asked.
```

### W. subagent 委譲の抑制（Opus 5）

```text
Delegate to a subagent only for large tasks that are genuinely independent and parallelizable, such as a wide multi-file investigation. Do not delegate work you can finish yourself in a handful of tool calls, and do not use subagents to verify or double-check your own work. If one subagent can complete the task, use one rather than several, and keep spawn counts low.
```

決定論的な上限が要るなら `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` / `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`、SDK なら `max_budget_usd`（Claude Code 2.1.217 以降）。

### X. 自己訂正の narration 抑制（Opus 5）

```text
Only correct an earlier statement when the error would change the user's code, conclusions, or decisions. State corrections plainly and briefly, then continue the task. For slips that change nothing for the user, make the fix and move on without noting it.
```

### Y. thinking 無効時の副作用の緩和（Opus 5）

tool 呼び出しのテキスト漏れと内部 XML タグの混入を 1 ブロックで抑える（項目 17）。

```text
When you use a tool, you may say a brief sentence first. If no tool can express what the user asked for, say so instead of guessing. Do not include internal or system XML tags in your response.
```

## Anti-Patterns

- **narrative example を入れる**: 「先日 X というケースで…」を skill に書かない（再利用性が下がる）
- **`Don't ...` だけで指示**: 何をすべきか肯定形で書く
- **checkpoint・過剰実装防止・進捗サマリー等を個別列挙で反復する**: Fable 5.1 は instruction-following が強く、一般原則1文への集約で足りることが多い（項目 12・16 参照）

その他の典型的な間違いは Common Mistakes 表を参照。

## Bottom Line

> 「Claude を、あなたの規範とワークフローのコンテキストに欠ける才能のある新しい従業員と考えてください」

具体的に・構造化して・理由を添えて・例を見せる。これが Claude を最大限引き出す方法。
