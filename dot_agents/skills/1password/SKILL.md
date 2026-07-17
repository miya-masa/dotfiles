---
name: 1password
description: 1Password CLI (op) でサインイン・vault 確認・secret 注入を行う時に使う。Claude セッションでは service account token (OP_SERVICE_ACCOUNT_TOKEN) をtoken ファイル (~/.config/op/service-account-token) から直前注入する方式を使い、op read の stdout を Claude context に流さない方針を強制する。「op signin」「op service-account」「op read」「op run」「op inject」「1Password から取って」などで発火。
origin: external-adapted
source:
  upstream: https://github.com/openclaw/openclaw/blob/main/skills/1password/SKILL.md
  upstream-commit-at-import: 7d6b7f434c2eac9aefc4bb314320e4f6d4d10c02
  imported-at: "2026-05-27"
  adapted: true
  adaptation-summary: tmux 必須化を撤去 (capture-pane が secret を context に取り込むため)。Claude Code の Bash tool で直接 op を呼ぶ前提に再構成。secret-safe 運用を不変条件として明記。さらに desktop app integration (op signin) 前提を service account token 方式 (OP_SERVICE_ACCOUNT_TOKEN を一時ファイルから直前注入) に切替 (Claude セッションでは生体認証プロンプトがブロックするため)。token 置き場所を /tmp/claude から ~/.config/op/service-account-token へ移動 (tmp 掃除で揮発したため, 2026-07-16)。
homepage: https://developer.1password.com/docs/cli/get-started/
---

# 1Password CLI (op)

## When to invoke

- 「op signin」「op whoami」「op vault list」など `op` コマンド全般
- 「op service-account」「サービスアカウントで」「1Password から API token 取って `<コマンド>` に渡したい」
- 他の skill や CLI が 1Password 経由で secret を扱う際の参照元

## 認証方式: service account (Claude セッション用)

Claude セッションの Bash tool は GUI プロンプトを受けられないため、desktop app integration の `op signin` (生体認証/Windows Hello) は**使えない**。代わりに **service account token** (`OP_SERVICE_ACCOUNT_TOKEN`) を token ファイルから各 `op` コマンドの**直前で注入**する。

- token 規定パス: `~/.config/op/service-account-token` (`chmod 600`、git/chezmoi 管理外・永続。旧 /tmp/claude/op-service-account-token は tmp 掃除で消えるため 2026-07-16 に移動)
- 注入パターン (1コマンドにスコープ、token を echo/Bash result に出さない):
  ```bash
  OP_SERVICE_ACCOUNT_TOKEN="$(cat ~/.config/op/service-account-token)" op read op://vault/item/field
  ```
- 確認: `OP_SERVICE_ACCOUNT_TOKEN="$(cat ~/.config/op/service-account-token)" op whoami` (User Type: SERVICE_ACCOUNT を返す)。公式の確認コマンドは `op user get --me`

## Pre-check

1. `op --version` — chezmoi script `13-install-1password.sh` で導入済を前提。`command not found` なら chezmoi apply を促す
2. `test -f ~/.config/op/service-account-token` — token ファイルの存在を確認。無ければ下記「Service account のセットアップ」をユーザーに依頼する
3. 疎通確認: `OP_SERVICE_ACCOUNT_TOKEN="$(cat ~/.config/op/service-account-token)" op whoami` (公式は `op user get --me`)
4. **Claude は `op signin` を呼ばない** (desktop app の生体認証/Hello プロンプトでブロックするため)
5. (併存注意) `OP_CONNECT_HOST` / `OP_CONNECT_TOKEN` がセットされていると `OP_SERVICE_ACCOUNT_TOKEN` より**優先される**。service account を使いたい場合は Connect の env を外す

## Service account のセットアップ (ユーザー作業)

token ファイルが無い / 失効した場合、ユーザーに以下を依頼する (Claude は token を作成・閲覧しない)。

1. service account を作成 (権限は最小限に):
   ```bash
   op service-account create <serviceAccountName> --expires-in <24h|30d|90d> \
     --vault <vault-name>:read_items[,write_items][,share_items]
   ```
   - 権限: `read_items` / `write_items` (read_items 必須) / `share_items` (read_items 必須)
   - 複数 vault は `--vault` を繰り返す。vault 作成も許すなら `--can-create-vaults`
   - read のみで足りるなら `read_items` だけにする。1Password に item を書き戻す用途では `write_items` が必要
2. 作成時に表示される token (`ops_` で始まる) を**直ちに**token ファイルへ書く (**token は1回しか表示されない**):
   ```bash
   # token をコピーして貼り付け、ファイルに保存
   mkdir -p ~/.config/op && install -m 600 /dev/null ~/.config/op/service-account-token
   # エディタ等で token を書き込む (echo で履歴に残さない方が安全)
   ```
3. token は 1Password 本体にも保存しておくと再注入できる (公式推奨)。プレーンな永続保存は避ける

## Secret-safe 運用 (この skill の中核)

Claude Code の Bash tool は stdout/stderr を **全て Claude context に取り込む**。`op read op://...` の出力をそのまま Bash result として返すと、その secret が会話履歴に残り後続ターンで再利用される。これを防ぐため:

### 不変条件

- **`op read` の出力を Bash tool result として返さない**
- 必要な場合は以下のいずれかの間接経路を使う:

| やりたいこと | 安全パターン |
|---|---|
| service account token を op に渡す | `OP_SERVICE_ACCOUNT_TOKEN="$(cat ~/.config/op/service-account-token)" op <cmd>` (1コマンドにスコープ。token を echo/printenv しない) |
| ファイル (証明書・SSH 鍵など) を取り出す | `op read --out-file ./key.pem op://vault/item/key.pem` (ファイル経由) |
| env var として 1 コマンドに渡す | `op run --env-file=./.env -- <command>` (`.env` には `VAR="op://vault/item/field"` 形式) |
| テンプレートに埋め込んで設定ファイルを生成 | `op inject -i config.yml.tpl -o config.yml` |
| token をそのまま別 CLI に流す (echo しない) | `op read op://vault/item/token | gh auth login --with-token` (パイプ右側で消費、stdout を返さない) |

### 禁止パターン

```bash
# NG: secret が Bash result として Claude context に入る
op read op://vault/item/password
TOKEN=$(op read op://vault/item/token) && echo "$TOKEN"
op item get "$ITEM" --fields password   # 同様に stdout 出力

# NG: service account token そのものを Claude context に出す
cat ~/.config/op/service-account-token   # 単独実行で token が stdout に出る
echo "$OP_SERVICE_ACCOUNT_TOKEN"
printenv OP_SERVICE_ACCOUNT_TOKEN
# token は OP_SERVICE_ACCOUNT_TOKEN="$(cat <tokenfile>)" op <cmd> の $(...) サブシェル内でのみ消費する
```

### グレーゾーン

- `op vault list` / `op item list` / `op account list` は **項目名のみ** で値は出ないため、stdout を返してよい
- `op whoami` / `op user get --me` も状態確認のみ (User Type 等) で secret を含まないため OK
- `op item get <item>` (フィールド指定なし) はメタデータのみだが、念のため `--format json | jq` 等で必要フィールドに絞る
- service account が複数 vault を持つ場合、`op item get/list` は `--vault <name>` の指定が必須

## tmux は使わない

openclaw 版は `op` を tmux session 内で実行し `capture-pane` でスクロールバックを取り込む方式を必須化していたが、本 skill では **使わない**。理由:

- Claude Code の Bash tool は TTY を持つので desktop integration プロンプトを直接受けられる (tmux 不要)
- `capture-pane -S -200` はスクロールバック全体を Claude に返してしまい、過去の secret 出力が漏出する経路になる

## 複数 vault / 複数 service account

- 1 つの service account token = 1 アカウント。複数 vault にアクセスしたい場合は **作成時に `--vault` を繰り返して** 権限を付与する:
  ```bash
  op service-account create ci --expires-in 30d \
    --vault app-prod:read_items \
    --vault infra:read_items,write_items
  ```
- 別アカウント / 別権限の service account を使い分ける場合は **token ファイルを分け**、注入時に切り替える:
  ```bash
  OP_SERVICE_ACCOUNT_TOKEN="$(cat ~/.config/op/token-work)" op vault list
  OP_SERVICE_ACCOUNT_TOKEN="$(cat ~/.config/op/token-personal)" op vault list
  ```
- `OP_ACCOUNT` / `op --account` / `op signin --account` は desktop integration 前提なので Claude セッションでは使わない。

> GUI 環境 (人間が手元で使う) で desktop app integration を使う場合の `op signin --account` 等は [`references/get-started.md`](references/get-started.md) の参考節に残してある。

## References

- [`references/get-started.md`](references/get-started.md) — OS 別の install / desktop integration / sign-in 手順 (公式 docs サマリ)
- [`references/cli-examples.md`](references/cli-examples.md) — secret-safe な `op` コマンド集 (`read --out-file` / `run` / `inject` 中心)
- 公式: https://developer.1password.com/docs/cli/get-started/
