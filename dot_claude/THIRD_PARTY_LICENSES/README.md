# Third-Party Licenses

このディレクトリには、本リポジトリに含まれるサードパーティ由来コードのライセンス情報を格納する。

## ECC (everything-claude-code)

`dot_claude/` 配下の以下のファイル群は ECC（everything-claude-code, MIT License）から部分取り込みしたもの。

- 個別ファイルの出自は frontmatter の `ecc-source:` または `ecc-imports:` キーで識別可能
- 取り込み base commit: `4e66b2882da9afb9747468b08a253ca2f09c85f3`
- LICENSE 全文: `everything-claude-code-LICENSE.md`
- 取り込みファイル一覧の動的取得: `Skill: ecc-sync`（inventory モード）

ECC のライセンスが MIT 以外に変更された場合、ecc-sync 本実装（別途 spec で定義予定）が検出して停止する。それまでは MIT 前提で運用する。

## 私的情報の混入禁止

このディレクトリの汎用ファイル（LICENSE, README）は `master` および `master-upstream` 両ブランチで共有される。private 情報（API key, internal URL など）を絶対に含めない。
