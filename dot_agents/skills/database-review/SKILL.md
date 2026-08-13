---
name: database-review
description: "PostgreSQL のクエリ最適化・スキーマ設計・セキュリティ(RLS)・パフォーマンス・並行性をレビューする観点集。SQL を書く / マイグレーション作成 / スキーマ設計 / DB パフォーマンス調査の時に reviewer agent が装着、または直接参照する。"
---

# Database Review（PostgreSQL）

一般知識では出てこない、性能に直結する非自明な癖のみを扱う。

## 診断コマンド

```bash
psql $DATABASE_URL
psql -c "SELECT query, mean_exec_time, calls FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"
psql -c "SELECT relname, pg_size_pretty(pg_total_relation_size(relid)) FROM pg_stat_user_tables ORDER BY pg_total_relation_size(relid) DESC;"
psql -c "SELECT indexrelname, idx_scan, idx_tup_read FROM pg_stat_user_indexes ORDER BY idx_scan DESC;"
```

## 非自明な癖

- **RLS ポリシーは行ごとに関数を呼ばない** — `current_setting('app.tenant_id')` 等は `(SELECT current_setting('app.tenant_id'))` で包み、行ごとの再評価を避ける
- **複合インデックスの列順** — 等価条件の列を先、範囲条件の列を後に置く
- **`SKIP LOCKED`** — キュー/ワーカーパターンでスループットが 10倍になる
- **部分インデックス** — ソフトデリートには `WHERE deleted_at IS NULL`
- **カバリングインデックス** — `INCLUDE (col)` でテーブルルックアップを避ける
- **外部キーには必ずインデックス** — 例外なく常に張る
