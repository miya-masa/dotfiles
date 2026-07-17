---
name: database-review
description: "PostgreSQL のクエリ最適化・スキーマ設計・セキュリティ(RLS)・パフォーマンス・並行性をレビューする観点集。SQL を書く / マイグレーション作成 / スキーマ設計 / DB パフォーマンス調査の時に reviewer agent が装着、または直接参照する。Supabase の postgres-best-practices を含む。"
---

# Database Review（PostgreSQL）

PostgreSQL のクエリ最適化・スキーマ設計・セキュリティ・パフォーマンスをレビューする観点集。DB コードがベストプラクティスに従い、パフォーマンス問題を防ぎ、データ整合性を保つことを確認する。Supabase の postgres-best-practices のパターンを取り込んでいる（credit: Supabase team）。

## レビューの主眼

1. **クエリ性能** — クエリ最適化、適切なインデックス、テーブルスキャンの回避
2. **スキーマ設計** — 適切なデータ型と制約を持つ効率的なスキーマ
3. **セキュリティ & RLS** — Row Level Security、最小権限アクセス
4. **コネクション管理** — プーリング、タイムアウト、上限の設定
5. **並行性** — デッドロック防止、ロック戦略の最適化
6. **モニタリング** — クエリ分析と性能トラッキング

## 診断コマンド

```bash
psql $DATABASE_URL
psql -c "SELECT query, mean_exec_time, calls FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"
psql -c "SELECT relname, pg_size_pretty(pg_total_relation_size(relid)) FROM pg_stat_user_tables ORDER BY pg_total_relation_size(relid) DESC;"
psql -c "SELECT indexrelname, idx_scan, idx_tup_read FROM pg_stat_user_indexes ORDER BY idx_scan DESC;"
```

## レビュー手順

### 1. クエリ性能（CRITICAL）
- WHERE/JOIN 列にインデックスがあるか
- 複雑なクエリに `EXPLAIN ANALYZE` を実行 — 大テーブルへの Seq Scan を確認
- N+1 クエリパターンに注意
- 複合インデックスの列順を確認（等価条件を先、範囲条件を後）

### 2. スキーマ設計（HIGH）
- 適切な型を使う: ID は `bigint`、文字列は `text`、タイムスタンプは `timestamptz`、金額は `numeric`、フラグは `boolean`
- 制約を定義: PK、FK（`ON DELETE` 付き）、`NOT NULL`、`CHECK`
- 識別子は `lowercase_snake_case`（クォートした mixed-case を使わない）

### 3. セキュリティ（CRITICAL）
- マルチテナントテーブルで RLS を有効化し `(SELECT auth.uid())` パターンを使う
- RLS ポリシーが参照する列にインデックス
- 最小権限アクセス — アプリユーザーに `GRANT ALL` しない
- public スキーマの権限を revoke

## 重要原則

- **外部キーにインデックス** — 例外なく常に
- **部分インデックス** — ソフトデリートには `WHERE deleted_at IS NULL`
- **カバリングインデックス** — `INCLUDE (col)` でテーブルルックアップを避ける
- **キューには SKIP LOCKED** — ワーカーパターンでスループット 10倍
- **カーソルページネーション** — `OFFSET` でなく `WHERE id > $last`
- **バッチインサート** — 複数行 `INSERT` か `COPY`。ループ内の個別 insert は禁止
- **短いトランザクション** — 外部 API 呼び出し中にロックを保持しない
- **一貫したロック順序** — デッドロック防止に `ORDER BY id FOR UPDATE`

## 検出すべきアンチパターン

- 本番コードでの `SELECT *`
- ID に `int`（`bigint` を使う）、理由のない `varchar(255)`（`text` を使う）
- タイムゾーンなし `timestamp`（`timestamptz` を使う）
- ランダム UUID を PK に（UUIDv7 か IDENTITY を使う）
- 大テーブルでの OFFSET ページネーション
- パラメータ化されていないクエリ（SQL インジェクションリスク）
- アプリユーザーへの `GRANT ALL`
- RLS ポリシーが行ごとに関数を呼ぶ（`SELECT` で包んでいない）

## レビューチェックリスト

- [ ] すべての WHERE/JOIN 列にインデックス
- [ ] 複合インデックスの列順が正しい
- [ ] 適切なデータ型（bigint, text, timestamptz, numeric）
- [ ] マルチテナントテーブルで RLS 有効
- [ ] RLS ポリシーが `(SELECT auth.uid())` パターンを使用
- [ ] 外部キーにインデックスがある
- [ ] N+1 クエリパターンがない
- [ ] 複雑なクエリに EXPLAIN ANALYZE 実行済み
- [ ] トランザクションが短い

## 補足

DB の問題はアプリ性能問題の根本原因になりがち。クエリとスキーマ設計を早期に最適化し、EXPLAIN ANALYZE で仮定を検証する。外部キーと RLS ポリシー列には必ずインデックスを張る。

*Patterns adapted from Supabase Agent Skills (credit: Supabase team) under MIT license.*
