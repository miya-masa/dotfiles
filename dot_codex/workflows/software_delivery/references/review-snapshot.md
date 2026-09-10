# 不変レビュー・スナップショット

`review_snapshot.py` はreview、ローカル検証、後続のstageを一つのallowlist対象の
意図したtreeへ束ねます。Gitメタデータと選択したworktreeまたはindexを読み取り、
indexへ書き込みません。

```text
python review_snapshot.py \
  --repo ROOT \
  --base-commit FULL_COMMIT \
  --allowlist-json '{"version":1,"paths":["path/to/file"]}' \
  --source worktree|index \
  --output MANIFEST
```

allowlistはversion `1`で、正規化したリポジトリ相対のfile pathを含みます。重複path、
`..` escape、絶対path、末尾separator、シンボリックリンクのparent、`.git`メタデータ
pathは拒否します。完全に解決されたGit commit IDが必要で、省略形commitは拒否します。

## マニフェストとidentity

出力manifestはatomicに書き込まれ、次のexact shapeになります。

```json
{
  "base_commit": "<full lowercase commit id>",
  "paths": [
    {
      "content_sha256": "<raw content SHA-256 or null>",
      "mode": "100644|100755|120000|040000|160000 or null",
      "path": "repository/relative/path",
      "state": "present|deleted|absent"
    }
  ]
}
```

entryは正規化path順に並びます。`present`は選択した最終treeのmodeとraw byteを記録
します（シンボリックリンクはlink targetをhashします）。`deleted`は削除されたbase
entryにblobがあれば、そのmodeとcontent hashを保持します。`absent`はbase treeにも
選択treeにもpathがないことを示します。

snapshot IDは、canonical JSON（`sort_keys=True`、compact separator、末尾改行なし）で
encodeしたmanifestのUTF-8 byteに対する`sha256:<hex>`です。source selectorは
manifestの一部ではないため、同値のworktreeとindex treeは同じIDを生成します。base
commit、allowlist対象content、mode、または削除を変えるとIDも変わります。

## preflightと一致ゲート

標準出力はIDとpreflight結果を含む一つのJSON objectです。

```json
{
  "preflight": {
    "external_dirty_paths": [],
    "external_staged_paths": [],
    "shipping_blocked": false
  },
  "review_snapshot_id": "sha256:<hex>"
}
```

allowlist外のdirtyまたはstaged pathは別に報告し、identityから除外しますが、出荷は
引き続きblockします。`index` modeでは外部staged pathが一つでもあればhard error
（manifestは置き換えない）です。外部unstaged pathはblocking preflightとして観測
可能なままです。要求されたmanifestは、すべての検証とhashingが成功した後だけ、
同じdirectoryの一時fileと`os.replace`を使って置き換えます。

stage直前とcommit直前に、同じ完全なbase commitとallowlistでsnapshotを再計算します。
新しいIDがfinal reviewとローカル検証に記録されたIDと完全一致する場合だけ進み、
それ以外では両方のgateを無効化して、変更後snapshotで再実行します。
