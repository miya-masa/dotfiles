# ワークフロー成果物のライフサイクル

`workflow_artifact.py` が所有するのはプロジェクトローカルのディレクトリ
`.aidocs/workflows/<workflow-id>/` だけです。Python標準ライブラリと
リポジトリのGit CLIを使い、Gitメタデータがない、または書き込めない場合は
hard error（重大エラー）になります。

## 識別子とレイアウト

`new-id [slug]` は任意のslugを小文字ASCIIとハイフンに正規化し、38文字に
制限したうえで、現在のUTC秒とランダムな16進文字8文字を末尾に付けます。
結果は最大63文字で、`[a-z0-9][a-z0-9-]{0,62}` に一致します。`init` は
既存または衝突するワークフロー・ディレクトリを拒否し、traversal、絶対、
不正形式、シンボリックリンクのpathも拒否します。

```text
.aidocs/workflows/<workflow-id>/
├── spec.md
├── plan.md
├── progress.md
├── context.json
├── tasks/
├── reviews/
└── verification.md
```

初期化処理はschema-v1の`context.json`に、正規プロジェクトルート、成果物
ルート、Gitのdefault branch、完全なbase commitを記録します。初期状態は
revision `0`の`DISCOVERY`で、worktreeなし、出荷認可なし、空のtask履歴、
保留中の`spec_review`です。隣接する`workflow_state.py validate`の実装が
引き続きschema authority（スキーマの正）です。

`reviews/`配下では`reviews/final-review.md`がfinal reviewの正本（authoritative
copy）であり、`FINAL_REVIEW -> LOCAL_VERIFICATION`の`workflow_state.py transition`が
参照するのはこのfileだけです。過去roundのreportやcross-model reviewの出力は別名で
`reviews/`に併存でき、それらはlint対象ではありません。

## ignore設定の所有権

成果物を作る前に、helperは`.aidocs/`に対して`git check-ignore`を実行します。
プロジェクトがまだ無視していなければ、正確なルール`/.aidocs/`をリポジトリ
ローカルの`.git/info/exclude`へ一度だけ追記します。既存のバイト列を保持し、
繰り返しの初期化は冪等であり、追跡対象のプロジェクト`.gitignore`は編集しません。
シンボリックリンクまたは利用不能なGitメタデータpathは、別の場所へリダイレクト
せず拒否します。

## 最終削除

`remove` はfail-closedです。正規プロジェクトルート、シンボリックリンクでない
単一の直下workflow path、および一致する`context.json`のidentityを検証します。
contextはschema-validでphaseが`ARTIFACT_REMOVE`、呼び出し元が指定した
`--expected-revision`と完全一致していなければなりません。呼び出し元は明示的な
`--authorize ARTIFACT_REMOVE` gateも指定する必要があり、任意の
`--phase ARTIFACT_REMOVE`は指定時に検査します。認可の欠落や誤りを含め、少しでも
不一致があれば成果物を変更しません。削除直前にも共有 `~/.agents/workflows/software_delivery/references/evidence-contract.md` のv2 risk gate（v1 legacyは従来承認）と保持証跡の一致を再検査します。検証済みの一つのworkflow directoryだけを
削除し、`.aidocs/`、別workflow、シンボリックリンク先は決して削除しません。

```text
workflow_artifact.py new-id [slug] [--project-root ROOT]
workflow_artifact.py init --project-root ROOT --workflow-id ID
workflow_artifact.py remove --project-root ROOT --workflow-id ID \
  --expected-revision N --authorize ARTIFACT_REMOVE \
  [--phase ARTIFACT_REMOVE] [--context PATH]
```

`init`の任意の`--default-branch`と`--base-commit` flagはGit探索結果を上書き
します。削除はstate CLIが`ARTIFACT_REMOVE`へ到達した後の最終引き継ぎであり、
このhelperが`context.json`を進めたり書き換えたりすることはありません。
