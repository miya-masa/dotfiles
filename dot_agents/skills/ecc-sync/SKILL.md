---
name: ecc-sync
description: ECC取り込み済みファイルを表示する inventory スキル。ecc-source 系 metadata を集計する。
---

# ecc-sync (inventory only)

ECC 由来取り込みの一覧表示と整合性チェックを行う inventory スキル。本実装（追随機能）は別途 spec / plan で定義予定。

## 起動時の動作

ユーザが `Skill: ecc-sync` で呼ぶと、以下の bash スクリプトを実行して結果を表示する。

## 実装シェル（コピペ実行可）

### モード判別 + inventory 抽出

```bash
#!/usr/bin/env bash
set -euo pipefail

CCLAUDE="$HOME/.claude"
MANIFEST="$CCLAUDE/.ecc-manifest.json"

# モード判別
if [ -f "$MANIFEST" ]; then
  MODE="manifest"
else
  MODE="frontmatter"
fi

# 混在チェック
if [ "$MODE" = "manifest" ]; then
  hybrid=$(find "$CCLAUDE/agents" "$CCLAUDE/skills" -name '*.md' \
    -exec sh -c 'yq eval "select(.ecc-source != null or .ecc-imports != null) | filename" "$1" 2>/dev/null' _ {} \; | head -1)
  if [ -n "$hybrid" ]; then
    echo "ERROR: manifest mode but found ecc-source in: $hybrid" >&2
    exit 1
  fi
fi

echo "## ECC Inventory ($MODE mode)"
echo ""

if [ "$MODE" = "frontmatter" ]; then
  # ecc-source（新規取り込み）
  echo "### Imported Files (ecc-source)"
  echo ""
  echo "| local path | upstream path | upstream commit | imported at | adapted | adapted-for |"
  echo "|---|---|---|---|---|---|"
  find "$CCLAUDE/agents" "$CCLAUDE/skills" "$CCLAUDE/THIRD_PARTY_LICENSES" \
    -name '*.md' -type f 2>/dev/null | while read f; do
    local_path=${f#$CCLAUDE/}
    upstream_path=$(yq eval '.ecc-source.upstream-path // ""' "$f" 2>/dev/null)
    [ -z "$upstream_path" ] && continue
    upstream_commit=$(yq eval '.ecc-source.upstream-commit // ""' "$f")
    imported_at=$(yq eval '.ecc-source.imported-at // ""' "$f")
    adapted=$(yq eval '.ecc-source.adapted // "false"' "$f")
    adapted_for=$(yq eval '.ecc-source.adapted-for // [] | join(",")' "$f" 2>/dev/null)
    echo "| $local_path | $upstream_path | ${upstream_commit:0:8}... | $imported_at | $adapted | $adapted_for |"
  done
  echo ""

  # ecc-imports（既存統合）
  echo "### Integrated Files (ecc-imports)"
  echo ""
  echo "| local path | upstream paths | sections-merged | imported at |"
  echo "|---|---|---|---|"
  find "$CCLAUDE/agents" "$CCLAUDE/skills" \
    -name '*.md' -type f 2>/dev/null | while read f; do
    has_imports=$(yq eval '.ecc-imports // []' "$f" 2>/dev/null | grep -c "upstream-path" || true)
    [ "$has_imports" = "0" ] && continue
    local_path=${f#$CCLAUDE/}
    yq eval -o=tsv '.ecc-imports[] | [.upstream-path, (.sections-merged | join(";")), .imported-at] | @tsv' "$f" 2>/dev/null \
      | while IFS=$'\t' read up sm imp; do
        echo "| $local_path | $up | $sm | $imp |"
      done
  done
  echo ""
fi

# Integrity warnings
echo "### Integrity Warnings"
echo ""
issues=0

# 同名衝突検出
dup_agents=$(find "$CCLAUDE/agents" -maxdepth 1 -name '*.md' \( -type f -o -type l \) 2>/dev/null \
  | xargs -n1 basename 2>/dev/null | sort | uniq -d)
[ -n "$dup_agents" ] && { echo "- agents name collision: \`$dup_agents\`"; issues=$((issues+1)); }

dup_skills=$(find "$CCLAUDE/skills" -maxdepth 1 \( -type d -o -type l \) 2>/dev/null \
  | xargs -n1 basename 2>/dev/null | sort | uniq -d)
[ -n "$dup_skills" ] && { echo "- skills name collision: \`$dup_skills\`"; issues=$((issues+1)); }

[ "$issues" = "0" ] && echo "(no issues found)"
echo ""

# Summary
imported=$(find "$CCLAUDE/agents" "$CCLAUDE/skills" "$CCLAUDE/THIRD_PARTY_LICENSES" \
  -name '*.md' -type f 2>/dev/null | xargs -I{} sh -c "yq eval '.ecc-source.upstream-path // \"\"' {} 2>/dev/null" | grep -v '^$' | wc -l)
integrated=$(find "$CCLAUDE/agents" "$CCLAUDE/skills" \
  -name '*.md' -type f 2>/dev/null | xargs -I{} sh -c "yq eval '.ecc-imports[].upstream-path // \"\"' {} 2>/dev/null" | grep -v '^$' | wc -l)
echo "### Summary"
echo "- Imported files: $imported"
echo "- Integrated entries: $integrated"
echo "- Mode: $MODE"
echo "- Integrity issues: $issues"
```

## 実装メモ

- bash + yq v4+ で実装、外部依存最小
- 本実装（fetch / lock / classify / review / integrity check / apply / report / cleanup）は別 spec

## 起動例

セッションで `Skill: ecc-sync` を呼ぶと、上記スクリプトを実行して結果を表示する。
