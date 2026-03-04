# 後片付け（tmux環境のみ）

## tmux判定

Bashツールで TMUX 環境変数の有無を確認する。

**TMUX環境変数が未設定の場合**: このステップをスキップする（何も表示しない）。

## AskUserQuestion（TMUX環境変数が設定されている場合）

- question: 「次のアクションを選択してください」
- header: 「セッション終了」
- multiSelect: false
- 選択肢1（デフォルト）:
  - label: 「タブをリセット (Recommended)」
  - description: 「tab-reset スキルを発動し、タブを待機状態にリセットします」
- 選択肢2:
  - label: 「タブを終了」
  - description: 「タブを閉じます（最後のタブの場合はセッションも終了します）」

## 選択後の動作

- **選択肢1** → Skill ツールで `tab-reset` を発動する
- **選択肢2** → 以下を実行する:
  ```bash
  python3 .claude/skills/save-chatlog/kill_tmux_window.py
  ```
  ※ このコマンド実行後、タブ（tmux window）とClaude Codeが同時に終了するため、応答は返らない
- **Other** → ユーザーのフリーテキスト入力内容に応じて対応する
