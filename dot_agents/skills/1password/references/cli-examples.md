# op CLI コマンド例 (secret-safe)

SKILL.md の「Secret-safe 運用」セクションを前提に、stdout に secret を返さないパターンを中心に並べる。

> **全 op 実行に token を前置する**: Claude セッションでは service account 方式を使う。以下の例は冗長を避けて prefix を省略しているものもあるが、実際には各 `op ...` の前に
> `OP_SERVICE_ACCOUNT_TOKEN="$(cat ~/.config/op/service-account-token)"` を付けて実行する (詳細は SKILL.md / get-started.md)。

## 認証確認 / vault (service account 方式)

```bash
op --version
# 状態確認 (値は返さない)
OP_SERVICE_ACCOUNT_TOKEN="$(cat ~/.config/op/service-account-token)" op whoami        # User Type: SERVICE_ACCOUNT
OP_SERVICE_ACCOUNT_TOKEN="$(cat ~/.config/op/service-account-token)" op user get --me  # 公式の確認コマンド
# vault / item 一覧 (名前のみ、値は出ない)
OP_SERVICE_ACCOUNT_TOKEN="$(cat ~/.config/op/service-account-token)" op vault list
OP_SERVICE_ACCOUNT_TOKEN="$(cat ~/.config/op/service-account-token)" op item list --vault MyVault
```

> マルチ vault の service account では `op item get/list` に `--vault <name>` が必須。

## Read: ファイル経由 (推奨)

```bash
# SSH 秘密鍵をファイルに書き出す (token prefix を付ける。以降の例は省略)
OP_SERVICE_ACCOUNT_TOKEN="$(cat ~/.config/op/service-account-token)" \
  op read --out-file ./id_ed25519 "op://Private/my-ssh-key/private key?ssh-format=openssh"
chmod 600 ./id_ed25519

# 証明書を取り出す
op read --out-file ./tls.crt op://Infra/web-tls/cert.pem
```

## Run: 環境変数経由でコマンドに渡す (推奨)

`.env` テンプレートに 1Password 参照を書き、`op run` がプロセス起動時に解決して環境変数として渡す。**プロセス終了とともに secret も消える**。

```bash
# .env (commit 可、値は op:// 参照のみ)
DB_PASSWORD="op://app-prod/db/password"
API_TOKEN="op://app-prod/service/token"

# 利用 (printenv は値を出すので NG。実コマンドに渡すのみ。token prefix を付ける)
OP_SERVICE_ACCOUNT_TOKEN="$(cat ~/.config/op/service-account-token)" op run --env-file=./.env -- ./run-migration.sh
OP_SERVICE_ACCOUNT_TOKEN="$(cat ~/.config/op/service-account-token)" op run --env-file=./.env -- docker compose up
```

`--no-masking` は debug 用途のみ。通常は付けない。

## Inject: テンプレート展開 (推奨)

設定ファイルテンプレートに `{{ op://... }}` を埋め込み、`op inject` で実体化。

```bash
# config.yml.tpl
# database:
#   password: {{ op://app-prod/db/password }}

OP_SERVICE_ACCOUNT_TOKEN="$(cat ~/.config/op/service-account-token)" op inject -i config.yml.tpl -o config.yml
```

生成後の `config.yml` は secret を含むため:
- `.gitignore` に追加
- 利用後は `shred -u config.yml` または `rm` で破棄
- 可能ならテンプレートを直接読むアプリ側で `op inject` に置き換える

## token を別 CLI に直接渡す (echo しない)

stdout を消費する右側 CLI にパイプで渡し、Claude context に値を残さない。

```bash
# gh auth (token を環境に残さず login)
OP_SERVICE_ACCOUNT_TOKEN="$(cat ~/.config/op/service-account-token)" \
  op read op://Private/github-pat/token | gh auth login --with-token
```

**注意**: パイプ全体を `command 2>&1 | tee log` などで logging すると secret が log に残る。安易に redirect しない。

## 禁止パターン (参考)

```bash
# NG: stdout に secret が出て Claude context に取り込まれる
op read op://vault/item/password
TOKEN=$(op read op://vault/item/token) && curl -H "Authorization: Bearer $TOKEN" ...
op item get my-item --fields password
op item get my-item --format json    # password フィールドが含まれる可能性

# OK: jq で必要なメタデータのみに絞る (値フィールドを除外)
op item get my-item --format json | jq '{id, title, tags, vault}'
```

## 複数 vault / 複数 service account

複数 vault は service account 作成時に `--vault` を繰り返して権限付与する (token は1つ)。別アカウント / 別権限を使い分ける場合は token ファイルを分け、注入時に切り替える。

```bash
# 複数 vault 権限を持つ service account を作成
op service-account create ci --expires-in 30d \
  --vault app-prod:read_items \
  --vault infra:read_items,write_items

# 別 token ファイルを使い分け
OP_SERVICE_ACCOUNT_TOKEN="$(cat ~/.config/op/token-work)" op run --env-file=./.env.work -- ./deploy.sh
```

`OP_ACCOUNT` / `op --account` は desktop integration 前提なので Claude セッションでは使わない。
