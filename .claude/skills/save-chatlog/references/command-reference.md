# save-chatlog コマンドリファレンス

## ユーティリティコマンド

すべての操作は `chatlog_utils.py` で実行する：

```bash
# ディレクトリ作成
python3 .claude/skills/save-chatlog/chatlog_utils.py mkdir <path>

# ファイル書き込み
python3 .claude/skills/save-chatlog/chatlog_utils.py write <path> <content>

# .gitignoreにエントリ追加
python3 .claude/skills/save-chatlog/chatlog_utils.py gitignore <path> <entry>

# セッション一覧を表示（保存済み/未保存ステータス付き）
python3 .claude/skills/save-chatlog/chatlog_utils.py list-sessions "$(pwd)"

# 現在のセッションを保存（--session-id でセッションIDを直接指定、推奨）
# --auto-merge: プラン→実装セッションの場合、自動的にマージ
# コミットがあった場合は --commits でハッシュを指定
python3 .claude/skills/save-chatlog/chatlog_utils.py save "<project>/_chatlog/" \
  --cwd "$(pwd)" --title "タイトル" --tags "tag1,tag2" --summary "要約文" \
  --session-id "<セッションID>" --commits "abc1234" --auto-merge

# 過去のセッションを保存（--offset: 0=最新, 1=1個前, ...）
# ※ 並列稼働していない場合のみ使用
python3 .claude/skills/save-chatlog/chatlog_utils.py save "<project>/_chatlog/" \
  --cwd "$(pwd)" --title "タイトル" --tags "tag1,tag2" --summary "要約文" \
  --offset 1

# 複数セッションをマージして保存（推奨: --merge-id でセッションID指定）
python3 .claude/skills/save-chatlog/chatlog_utils.py save "<project>/_chatlog/" \
  --cwd "$(pwd)" --title "タイトル" --tags "tag1,tag2" --summary "要約文" \
  -g "ユーザーの日本語発言" \
  --merge-id "<計画セッションのID>"

# 複数セッションをマージして保存（従来方式: -m N、並列稼働時は使用注意）
python3 .claude/skills/save-chatlog/chatlog_utils.py save "<project>/_chatlog/" \
  --cwd "$(pwd)" --title "タイトル" --tags "tag1,tag2" --summary "要約文" \
  -m 1
```

## セッション一覧の確認

ユーザーが「どのセッションがあるか確認して」「過去のログを保存したい」等と言った場合：

```bash
python3 .claude/skills/save-chatlog/chatlog_utils.py list-sessions "$(pwd)"
```

出力例：
```
Offset Session ID                             Updated              Status
--------------------------------------------------------------------------------
0      0331cd8f-aab4-432d-945d-6b6f71d26f46   2026-01-24 19:02     未保存
1      6d27ff8c-a8af-4c5c-a2c9-f68ce1681e32   2026-01-24 18:38     保存済み
2      c6dd2b20-b12b-48b9-ba8d-cbf8865b48d1   2026-01-23 18:28     未保存
```

- **Offset**: save コマンドの `--offset` に指定する番号（0=最新）
- **Status**: `_chatlog/` 内に同じ session_id が存在するかで判定

## 過去のセッションを保存

1個前のセッション（コンテキストクリア前の会話など）を保存したい場合：

```bash
python3 .claude/skills/save-chatlog/chatlog_utils.py save \
  "<project>/_chatlog/" \
  --cwd "$(pwd)" \
  --title "タイトル" \
  --tags "tag1,tag2" \
  --summary "要約文" \
  --offset 1
```

## 複数セッションのマージ

プランモード→実装モードなど、関連する複数セッションを1つのファイルにまとめて保存する場合。

### 方法A: 自動マージ（推奨）

`--auto-merge` を使用すると、プランファイルから `planning-session:` を自動検出してマージする：

```bash
# --auto-merge でプランニングセッションを自動検出
python3 .claude/skills/save-chatlog/chatlog_utils.py save \
  "<project>/_chatlog/" \
  --cwd "$(pwd)" \
  --title "マージタイトル" \
  --tags "tag1,tag2" \
  --summary "複数セッションの要約" \
  --session-id "<現在のセッションID>" \
  --auto-merge
```

**動作**:
- 現在のセッションのプランファイルに `planning-session:` があれば自動マージ
- なければ単一セッションとして保存
- `--merge-id` の手動指定は不要

### 方法B: セッションID明示指定

自動検出ではなく明示的にセッションIDを指定する場合：

```bash
# --merge-id で計画セッションのIDを指定、--session-id で現在のセッションを特定
python3 .claude/skills/save-chatlog/chatlog_utils.py save \
  "<project>/_chatlog/" \
  --cwd "$(pwd)" \
  --title "マージタイトル" \
  --tags "tag1,tag2" \
  --summary "複数セッションの要約" \
  --session-id "<現在のセッションID>" \
  --merge-id "c513221a-9e6c-444c-adde-4040dab7b189"
```

**ポイント**:
- `--merge-id` には計画セッションのIDを指定（古い方）
- `--session-id` で現在のセッションを特定（新しい方）
- 結合順序: `[merge-id, current-id]`（計画→実装の時系列順）

### 方法C: offset指定でマージ（従来方式）

**注意**: 並列稼働時は正確なセッション特定ができない場合があります：

```bash
# offset 0（最新）から 1（1個前）までをマージ（-m は --merge-until の短縮形）
python3 .claude/skills/save-chatlog/chatlog_utils.py save \
  "<project>/_chatlog/" \
  --cwd "$(pwd)" \
  --title "マージタイトル" \
  --tags "tag1,tag2" \
  --summary "複数セッションの要約" \
  -m 1
```

### マージ時のフロントマター形式

```yaml
---
date: 2026-01-22
session_ids:
  - c6dd2b20-b12b-48b9-ba8d-cbf8865b48d1  # 計画セッション（古い）
  - 0331cd8f-aab4-432d-945d-6b6f71d26f46  # 実装セッション（新しい）
plan_files:
  - .claude/plans/plan1.md
  - .claude/plans/plan2.md
commits:
  - abc1234
title: マージタイトル
...
---
```

- 会話は古いセッションから時系列順に結合される
- 複数セッションにプランファイルがある場合は `plan_files` 配列形式で記録される
- 単一のプランファイルのみの場合は `plan_file` 単数形式

## プランニング→実装セッションのマージ

プランモードを使った場合、セッションが2つに分かれる：
- **プランニングセッションID**: プランファイルの `planning-session:` に記載（UUID形式）
- **実装セッションID**: 現在のセッション（UUID形式）

### 推奨手順

1. 現在のセッションIDを取得（Step 2-1 参照）
2. `--auto-merge` で保存

```bash
python3 .claude/skills/save-chatlog/chatlog_utils.py save \
  "<project>/_chatlog/" \
  --cwd "$(pwd)" \
  --title "タイトル" \
  --tags "tag1,tag2" \
  --summary "要約文" \
  --session-id "<現在のセッションID>" \
  --auto-merge
```

**動作**: プランファイルに `planning-session:` があれば自動的にマージモードになる。

### 注意

- **セッションID（UUID形式）とプランファイル名（3単語ハイフン形式）は別物**
- プランファイル名の例: `dynamic-honking-sunbeam.md`
- セッションIDの例: `48b6292e-8dd5-4be6-85b6-2f0ad9cef670`
- プランファイル内の `planning-session:` がプランニングセッションのID

## プランファイルの自動アーカイブ

チャットログ保存時、検出されたプランファイルは自動的にタイムスタンプ付きディレクトリ構造にアーカイブされる：

```
.claude/plans/happy-fluttering-sedgewick.md
  → .claude/plans/2026/02/20260212-153000_プランファイルのアーカイブ機能を移設.md
```

- H1 見出しからタイトルを取得してファイル名に使用
- すでに年月ディレクトリ内にあるファイルはスキップ（二重アーカイブ防止）
- アーカイブ後のパスがフロントマターの `plan_file` に記録される

## `--auto-merge` の動作

- プランファイルに `planning-session:` が記録されている場合、自動的にマージモードで保存
- planning-session がなければ単一セッションとして保存（従来通り）
- 明示的な `--merge-id` 指定は不要

## エラー/課題の自動検出（stderr 出力）

`save` コマンド実行時、JSONL パース結果から以下のパターンを自動検出し、stderr に結果を出力する:

- `Traceback (most recent call last):` — Python トレースバック
- `Exit code: N`（N > 0）— コマンド実行失敗
- `Permission to use ... has been denied` — ツール実行拒否
- `Error:` を含む行 — 一般的なエラー

**stderr 出力例:**
```
=== Error Collection Results ===
Detected 2 error(s)/issue(s) in session abc12345-...
Error log path: /path/to/.claude/context/issues/20260217-143000_error-log.md

--- [1] type=permission_denied ---
Permission to use Bash has been denied

--- [2] type=exit_code ---
Exit code: 1

=== End Error Collection ===
```

- エラーが検出されなかった場合、stderr には何も出力されない
- 検出結果がある場合、LLM が `references/error-collection.md` の手順に従ってエラーログファイルを生成する
- エラーログの保存先: `<project>/.claude/context/issues/YYYYMMDD-HHMMSS_error-log.md`
