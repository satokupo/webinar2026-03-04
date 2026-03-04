---
name: current-session-id
description: |
  Retrieve the session ID of the current Claude Code chat.
  Use when the session ID is needed for log saving,
  file path construction, or any session-specific operation.
user-invocable: true
---

# セッションID取得

現在のセッションにマーカーを書き込み、JSONLファイルを検索してセッションIDを特定する。
直接取得するAPIがないための間接的手法。

## 手順

1. 同ディレクトリの `stamp.py` を `python3` で実行し、出力されたマーカー文字列を記録する（`python3 stamp.py`）
2. 同ディレクトリの `find.py` を `python3` で実行する（`python3 find.py --marker <手順1の出力>`）
3. セッションID（JSONLファイル名のベースネーム、UUID形式）のみ出力する
