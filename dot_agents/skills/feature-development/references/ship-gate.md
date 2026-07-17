# Ship Gate

feature-development の実装と review が完了した後、commit、sanitize、PR、CI を順に確認する。runtime 固有の hook に依存せず controller が各 gate の evidence を保持する。

## 1. 統合テスト

- README、Makefile、CI config、リポジトリ規約から正規 command を確認して実行する。
- mock だけで終えず、可能な限り API / CLI / UI / message / device など実際の入口から確認する。
- 失敗は記録し、原因を修正して再実行する。test の skip/delete で通さない。

## 2. Review gate

push や PR 作成の前に次を満たす。

- 実装文脈を持たない fresh reviewer を最低 1 体通した。
- 大規模または protected contract の変更は [review-lenses.md](review-lenses.md) の該当レンズを追加した。
- controller が全指摘を裏取りし、「今回修正 / 見送り（根拠付き）/ 要判断」に分類した。
- 採用した指摘の修正後に verifier が再検証した。

runtime 固有の review command はユーザー明示時だけ追加で使い、gate の前提にはしない。

## 3. Commit

- `conventional-commit` とリポジトリ規約に従う。
- commit 対象と `git diff --cached` を確認し、既存の未コミット変更を混ぜない。
- ローカル専用 spec や plan の path を commit message に含めない。

## 4. Sanitize gate

push や PR 作成の前に、PR description 候補と送信対象 diff を確認する。

- token、password、API key、credential。
- `/home/<user>/...` などの内部 path。
- 本番 / 社内 host、非公開 URL、顧客情報、社外秘。
- ローカル専用 spec / plan への path や link。

controller は承認を求める前に、PR description 候補と送信対象の `git diff` をユーザーへ提示する。diff が長大なら、sanitize 判断に必要な要約、送信対象の範囲、完全な diff の参照方法を提示する。判断材料を示さずに承認を求めない。

ユーザーに `sanitize OK / 修正が必要 / 中止` を active runtime の質問手段で確認する。`sanitize OK` 以外では push と PR 作成を行わない。修正後は gate を再実行する。

## 5. Push と PR

ユーザーの明示許可後に push する。対象 forge の skill または CLI と、リポジトリの PR template を使う。本文にはローカル spec の参照ではなく、目的、scope、主要変更、検証結果を要約する。

## 6. CI gate

- active runtime で利用できる forge skill / CLI を使い、全 required job が終わるまで監視する。
- 失敗時はログを取得し、root cause を調査して最小修正、focused test、push、再監視を行う。
- 2 回の修正または同等の調査でも原因が絞れない場合は、別コンテキストの fresh explorer / reviewer に read-only 診断を委譲する。失敗ログ、試した修正、結果、関連 path を渡し、仮説を検証してから採用する。
- 外部 service 障害、runner / cache / secret manager、再現困難な複数 system、acceptance 自体の矛盾、protected contract 変更が必要な場合はユーザー判断を得る。

CI 全 pass の evidence を確認してから finishing-a-development-branch へ進む。CI 未完了や未確認を「完了」と報告しない。
