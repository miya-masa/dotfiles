#!/usr/bin/env bash
# Remove only the unmodified legacy chezmoi-managed context guard.
set -o nounset
set -o errexit
set -o pipefail

readonly TARGET="$HOME/.local/bin/codex-context-guard"
readonly LEGACY_SHA256="0accc6b6ea29b5f7a3b20b93fe28327a8b3a520c562cb1584c5ded23a4fde9e9"

if [[ ! -e "$TARGET" && ! -L "$TARGET" ]]; then
  exit 0
fi

if [[ -L "$TARGET" || ! -f "$TARGET" ]]; then
  echo "WARNING: preserving $TARGET because it is not the legacy regular file" >&2
  exit 0
fi

if command -v sha256sum >/dev/null 2>&1; then
  hash_output="$(sha256sum "$TARGET")"
elif command -v shasum >/dev/null 2>&1; then
  hash_output="$(shasum -a 256 "$TARGET")"
else
  echo "ERROR: cannot verify $TARGET: neither sha256sum nor shasum is available" >&2
  exit 1
fi
read -r actual_sha256 _ <<<"$hash_output"
if [[ "$actual_sha256" != "$LEGACY_SHA256" ]]; then
  echo "WARNING: preserving modified $TARGET; legacy content does not match" >&2
  exit 0
fi

rm -- "$TARGET"
