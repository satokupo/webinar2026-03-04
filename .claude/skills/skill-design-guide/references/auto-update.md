# 自動更新チェック 詳細フロー

SKILL.md のステップ2（件数チェック）で1件以上のスキル関連リリースが検知された場合に、
このファイルの手順に従う。

## ステップ3: 生データ取得（Haiku サブエージェント）

Task ツールで Haiku サブエージェントを起動し、リリースノートの生データを取得する。

- model: haiku
- 処理: `python3 scripts/check_updates.py "LAST_CHECKED_DATE" --details` を実行し、
  結果の JSON をそのままメインコンテキストに返す
- サブエージェントはフィルタや判断を行わない。生データの取得のみ

サブエージェントに分離する理由: リリースノート本文がメインコンテキストに直接載るのを防ぐ。

## ステップ4: 関連性判断（メインコンテキスト）

メインコンテキスト（Opus）がサブエージェントから受け取った生データを解析する:

1. 各リリースの body を読み、skill-design-guide のナレッジに影響する変更かを判断
2. 関連する変更を150字程度に要約

判断基準:
- スキルの仕様変更（フロントマター、ディレクトリ構造、実行方式等）→ 関連あり
- スキルの表示・UI改善のみ → 関連なし
- Claude Code 本体の機能追加でスキルに間接的に影響するもの → 関連あり

サブエージェントの報告を鵜呑みにせず、メインが自ら判断すること。

## ステップ5: ユーザー判断

要約をアラート形式で表示し、AskUserQuestion で選択肢を提示する:

表示フォーマット:
---
**⚠️ skill-design-guide ナレッジ更新検知**

前回チェック: {last_checked}
検知されたリリース: {バージョン} ({日付})

変更概要:
- {メインコンテキストが作成した要約}
---

選択肢（AskUserQuestion）:
- 「無関係 — スキル設計に関係ない変更なので続行」
- 「保留 — 関係はあるが今のスコープには影響しないので続行（別セッションで修正予定）」

ユーザーの選択に応じて:
1. history に記録（action: "irrelevant" or "deferred"）
2. last_checked を当日に更新
3. 通常フロー（参照ルーティング）へ進む

重要: 「変更があるが修正しない」という選択肢は用意しない。
irrelevant = そもそもスキル設計に無関係。deferred = 関係あるので別セッションで必ず修正する。

## update-log.yaml の更新パターン

### 変更なし（ステップ2で件数 = 0）
last_checked を当日に更新。history に追加:
- date: 当日, result: "no_change", summary: "スキル関連リリースなし", action: null

### 変更あり・無関係（ステップ5でユーザーが「無関係」を選択）
last_checked を当日に更新。history に追加:
- date: 当日, result: "changed", summary: "{変更内容}", action: "irrelevant"

### 変更あり・保留（ステップ5でユーザーが「保留」を選択）
last_checked を当日に更新。history に追加:
- date: 当日, result: "changed", summary: "{変更内容}", action: "deferred"

YAML の更新は Edit ツールで該当箇所を書き換える。

## gh CLI が使えない場合のフォールバック

gh コマンドが利用できない場合（コマンド未インストール、認証エラー等）:

1. WebFetch で https://github.com/anthropics/claude-code/releases を取得
2. プロンプト: 「{last_checked} 以降に公開された、本文に "skill" を含むリリースの件数を教えてください」
3. 件数が 0 → 変更なし、1以上 → ステップ3（Haiku）へ

WebFetch も失敗した場合（ネットワークエラー等）:
1. ユーザーに報告: 「自動チェックに失敗しました。https://github.com/anthropics/claude-code/releases を手動で確認してください」
2. last_checked は更新せず、history に result: "error" エントリを追加
3. 通常フロー（参照ルーティング）へ進む（チェック失敗で作業を止めない）
