---
name: skill-creator
description: Claudeの能力を拡張する新規/既存スキルの設計・更新に使うガイド。専門知識、ワークフロー、ツール連携を備えたSkillを作るときに使用する。
license: Complete terms in LICENSE.txt
---

# Skill Creator

このスキルは、効果的なSkillを設計・作成するための実践ガイドである。

## Skillsについて

Skillは、Claudeの能力を拡張するためのモジュール式の自己完結パッケージである。特定領域の知識、手順、ツールを束ねることで、汎用エージェントを専門エージェントへと変換する。

### Skillsが提供するもの

1. 専門ワークフロー - 特定領域向けの多段手順
2. ツール連携 - 特定ファイル形式やAPIの扱い方
3. ドメイン知識 - 社内スキーマ、業務ロジック、制度情報
4. 同梱リソース - 繰り返し作業のためのスクリプトや参照資料

## コア原則

### 簡潔さが最重要

コンテキストウィンドウは共有資源である。Skillは、システムプロンプト、会話履歴、他Skillのメタデータ、ユーザー要望と同じ窓を分け合う。

**前提: Claudeは十分に賢い。** Claudeが既に知っていることは書かない。各情報について「本当に必要か」「トークンコストに見合うか」を常に検討する。

長い説明より短い例を優先する。

### 自由度の設定

タスクの壊れやすさとばらつきに合わせて、指示の厳密度を調整する。

**自由度 高 (テキスト指示)**: 複数の手段が妥当で、状況依存の判断が必要な場合。

**自由度 中 (疑似コード/パラメータ付きスクリプト)**: 推奨パターンがあり、ある程度の変化が許容される場合。

**自由度 低 (具体的手順/少数のパラメータ)**: 失敗コストが高く、厳密な手順が必要な場合。

狭い橋にはガードレールが必要で、広い野原では自由に歩けるという比喩を意識する。

### Skillの構成

各Skillは必須のSKILL.mdと任意の同梱リソースで構成される。

```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter metadata (required)
│   │   ├── name: (required)
│   │   └── description: (required)
│   └── Markdown instructions (required)
└── Bundled Resources (optional)
    ├── scripts/          - Executable code (Python/Bash/etc.)
    ├── references/       - Documentation intended to be loaded into context as needed
    └── assets/           - Files used in output (templates, icons, fonts, etc.)
```

#### SKILL.md (必須)

SKILL.mdは以下で構成される。

- **Frontmatter** (YAML): `name` と `description` を含む。これらだけがSkillの発火判定に使われるため、用途と利用条件を明確に書く。
- **Body** (Markdown): Skill利用時の指示本文。Skillが発火した後にのみ読み込まれる。

#### Bundled Resources (任意)

##### Scripts (`scripts/`)

決定論的な信頼性が必要な処理や、繰り返し書くコードを格納する。

- **入れるタイミング**: 同じコードを繰り返し書いている、または確実な再現が必要
- **例**: PDF回転の `scripts/rotate_pdf.py`
- **利点**: トークン節約、再現性向上、コンテキストに載せず実行可能
- **注意**: 環境依存の修正やパッチ時に読まれる場合がある

##### References (`references/`)

必要に応じて読み込むべきドキュメントや参考資料を置く。

- **入れるタイミング**: 作業中に参照すべき説明がある
- **例**: `references/finance.md`、`references/mnda.md`、`references/policies.md`、`references/api_docs.md`
- **用途**: DBスキーマ、API仕様、ドメイン知識、社内規程、詳細手順
- **利点**: SKILL.mdの肥大化を防ぎ、必要時のみ読み込める
- **ベストプラクティス**: 大きいファイル (>10k words) は、SKILL.mdにgrep用パターンを記載する
- **重複回避**: 詳細はreferencesに置き、SKILL.mdは中核の手順だけにする

##### Assets (`assets/`)

コンテキストに載せず、出力に使うためのファイルを置く。

- **入れるタイミング**: 出力に利用するファイルが必要
- **例**: `assets/logo.png`、`assets/slides.pptx`、`assets/frontend-template/`、`assets/font.ttf`
- **用途**: テンプレート、画像、アイコン、ボイラープレート、フォント
- **利点**: 出力素材の分離により、必要時に読み込まず利用できる

#### Skillに入れてはいけないもの

Skillは機能に直結する必須ファイルのみ含める。以下のような付随ドキュメントは作らない。

- README.md
- INSTALLATION_GUIDE.md
- QUICK_REFERENCE.md
- CHANGELOG.md
- etc.

SkillはAIエージェントが仕事をするための情報だけに絞る。作成経緯、セットアップ手順、ユーザー向け解説などの付随情報は不要である。

### Progressive Disclosureの設計原則

Skillは3段階の読み込みでコンテキストを節約する。

1. **Metadata (name + description)** - 常時読み込み (~100 words)
2. **SKILL.md body** - Skill発火時に読み込み (<5k words)
3. **Bundled resources** - 必要時のみ読み込み (スクリプトは読まずに実行可能)

#### Progressive Disclosureのパターン

SKILL.md本文は必要最小限に保ち、500行以内を目安にする。長くなる場合は分割し、どのタイミングで読むべきかをSKILL.mdで明示する。

**基本原則:** 複数のバリエーションやフレームワークに対応する場合、SKILL.mdには基幹手順と選択指針だけを書く。詳細は参照ファイルへ分ける。

**Pattern 1: High-level guide with references**

```markdown
# PDF Processing

## Quick start

Extract text with pdfplumber:
[code example]

## Advanced features

- **Form filling**: See [FORMS.md](FORMS.md) for complete guide
- **API reference**: See [REFERENCE.md](REFERENCE.md) for all methods
- **Examples**: See [EXAMPLES.md](EXAMPLES.md) for common patterns
```

Claudeは必要な時だけFORMS.mdやREFERENCE.mdを読む。

**Pattern 2: Domain-specific organization**

複数ドメインがある場合は、ドメイン別に分けて不要な読み込みを避ける。

```
bigquery-skill/
├── SKILL.md (overview and navigation)
└── reference/
    ├── finance.md (revenue, billing metrics)
    ├── sales.md (opportunities, pipeline)
    ├── product.md (API usage, features)
    └── marketing.md (campaigns, attribution)
```

ユーザーがsalesの質問をしたときだけsales.mdを読む。

同様に、複数クラウドや実装差分がある場合は、バリアント別に分ける。

```
cloud-deploy/
├── SKILL.md (workflow + provider selection)
└── references/
    ├── aws.md (AWS deployment patterns)
    ├── gcp.md (GCP deployment patterns)
    └── azure.md (Azure deployment patterns)
```

**Pattern 3: Conditional details**

基本内容だけ示し、条件付きで詳細へ誘導する。

```markdown
# DOCX Processing

## Creating documents

Use docx-js for new documents. See [DOCX-JS.md](DOCX-JS.md).

## Editing documents

For simple edits, modify the XML directly.

**For tracked changes**: See [REDLINING.md](REDLINING.md)
**For OOXML details**: See [OOXML.md](OOXML.md)
```

**Important guidelines:**

- **深い参照の連鎖を避ける** - 参照ファイルはSKILL.mdから1階層以内に留める
- **長い参照ファイルは構造化する** - 100行を超える場合は冒頭に目次を置く

## Skill作成プロセス

以下の順で進める。

1. 具体例でSkillの利用像を把握する
2. 再利用可能な内容を設計する (scripts/references/assets)
3. Skillを初期化する (init_skill.py)
4. Skillを編集する (SKILL.mdとリソース実装)
5. Skillをパッケージする (package_skill.py)
6. 実利用で反復改善する

理由がない限り順番通りに進める。

### Step 1: 具体例でSkillの利用像を把握する

利用パターンが十分に明確な場合のみ省略可能。既存Skillの改善でも有効。

有効なSkillを作るには、実際にどう使われるかの具体例を把握する。ユーザーの例を聞くか、仮の例を提示して確認を得る。

例: image-editor Skillの場合の質問例

- "What functionality should the image-editor skill support? Editing, rotating, anything else?"
- "Can you give some examples of how this skill would be used?"
- "I can imagine users asking for things like 'Remove the red-eye from this image' or 'Rotate this image'. Are there other ways you imagine this skill being used?"
- "What would a user say that should trigger this skill?"

一度に質問を詰め込みすぎない。まず重要な質問から始め、必要に応じて追加する。

このステップは、Skillが担う範囲が明確になった時点で完了とする。

### Step 2: 再利用可能な内容を設計する

具体例を次の観点で分析する。

1. 例をゼロから実行するとしたらどう進めるか
2. 反復作業を支えるscripts/references/assetsは何か

例: `pdf-editor` Skillの場合

1. PDF回転のコードを毎回書き直している
2. `scripts/rotate_pdf.py` を用意する

例: `frontend-webapp-builder` Skillの場合

1. フロントエンドのボイラープレートを毎回書いている
2. `assets/hello-world/` にテンプレートを置く

例: `big-query` Skillの場合

1. 毎回スキーマを探している
2. `references/schema.md` を用意する

各例から再利用素材を抽出し、必要なファイル一覧を作る。

### Step 3: Skillを初期化する

新規Skillを作る場合は必ず `init_skill.py` を実行する。既存Skillの改善のみなら省略可能。

```bash
scripts/init_skill.py <skill-name> --path <output-directory>
```

このスクリプトは以下を自動生成する。

- 指定パスにSkillディレクトリを作成
- 適切なfrontmatterとTODOを含むSKILL.mdテンプレート
- `scripts/` `references/` `assets/` の例ディレクトリ
- それぞれの例ファイル

初期化後に不要な例ファイルは削除し、必要な内容に置き換える。

### Step 4: Skillを編集する

Skillは別のClaudeが使う前提で設計する。Claudeが知らない手順やドメイン知識、再利用可能な資産を明確に書く。

#### 実績ある設計パターンを参照する

- **複数ステップの手順**: references/workflows.md
- **出力形式や品質規定**: references/output-patterns.md

#### 再利用素材から実装する

設計で定めた `scripts/` `references/` `assets/` を先に整備する。必要ならユーザーから資料を受け取る。

追加したスクリプトは実際に実行して検証する。類似スクリプトが多数ある場合は代表的なものを試験し、全体の信頼性を担保する。

初期化で生成された不要な例ファイルは削除する。

#### SKILL.mdを更新する

**記述ルール:** 必ず命令形/不定詞形で書く。

##### Frontmatter

`name` と `description` のみを書く。

- `name`: Skill名
- `description`: Skillの主要トリガー。何をするSkillか、どの文脈で使うかを具体的に書く。
  - 「いつ使うか」の情報は必ずdescriptionに書く
  - 本文の "When to Use" セクションは不要 (本文は発火後に読み込まれるため)
  - 例: `docx` Skillのdescription

Do not include any other fields in YAML frontmatter.

##### Body

Skillの使い方と同梱リソースの扱い方を説明する。

### Step 5: Skillをパッケージする

完成したSkillは配布用の `.skill` にパッケージする。パッケージ前に自動バリデーションが走る。

```bash
scripts/package_skill.py <path/to/skill-folder>
```

出力先指定:

```bash
scripts/package_skill.py <path/to/skill-folder> ./dist
```

パッケージスクリプトは以下を行う。

1. **Validate** (自動検証)
   - YAML frontmatter形式と必須項目
   - Skillの命名規則とディレクトリ構成
   - descriptionの品質と完成度
   - ファイル構成と参照の整合性

2. **Package** (生成)
   - `my-skill.skill` のような名称でSkillを作成
   - `.skill` はzip形式で、必要ファイルを全て含む

検証に失敗した場合はエラーを修正して再実行する。

### Step 6: 反復改善する

Skillは実利用から改善されることが多い。使った直後が最も改善点を見つけやすい。

**Iteration workflow:**

1. Use the skill on real tasks
2. Notice struggles or inefficiencies
3. Identify how SKILL.md or bundled resources should be updated
4. Implement changes and test again
