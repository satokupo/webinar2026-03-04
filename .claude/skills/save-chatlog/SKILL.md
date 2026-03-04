---
name: save-chatlog
description: |
  Save current chat log to project's _chatlog/ as markdown with auto-generated
  YAML frontmatter (date, title, tags, summary). Saves immediately without confirmation.
  Trigger: 「ログ保存して」「チャット記録を残して」「履歴を保存」「この会話を保存」
user-invocable: true
---

# チャットログ保存スキル

ユーザーがチャットログの保存を依頼した場合、または `/save-chat` コマンドが実行された場合にこのスキルを使用する。

**重要**: このスキルは確認なしで即座に保存を実行し、完了後に報告する。

## トリガー条件

以下のような発言でこのスキルを起動する：
- 「ログ保存して」「ログを保存」
- 「チャット記録を残して」
- 「履歴を保存」
- 「この会話を保存」
- `/save-chat` コマンド

## 処理手順

### Step 1: フロントマターを生成

会話履歴を見て以下を生成する（Claudeが直接生成、Bash不要）：
- **date**: チャット開始日（YYYY-MM-DD）
- **title**: 会話の主要な話題（最初の数ターンから推測）
- **tags**: 技術キーワード、作業種別（3-5個）
- **summary**: 2-3行の要約
- **commits**: セッション中に行った git commit のハッシュ（短縮形）一覧（コミットがない場合は省略）

※ **plan_file/plan_files** はJSONLから自動検出されフロントマターに追加される（手動指定不要）

### Step 2: 保存を実行

フロントマター生成後、**確認なしで即座に保存を実行**する：

#### 2-1. 現在のセッションIDを取得（必須）

`/current-session-id` を実行してセッションIDを取得する。

取得したUUIDを `--session-id` で渡す。

#### 2-2. マークダウン保存（ディレクトリ作成・.gitignore追加も自動）

```bash
python3 .claude/skills/save-chatlog/chatlog_utils.py save \
  "<project>/_chatlog/" \
  --cwd "$(pwd)" \
  --title "タイトル" \
  --tags "tag1,tag2,tag3" \
  --summary "要約文" \
  --session-id "<取得したセッションID>" \
  --commits "abc1234,def5678" \
  --auto-merge
```

**ファイル名形式**: `YYYYMMDD-HHMMSS_タイトル.md`（Python側で `start_time` から自動生成。LLMがタイムスタンプを指定する必要はない）

※ コミットがないセッションでは `--commits` を省略する

`--auto-merge` やマージオプションの詳細は `references/command-reference.md` を参照。

### Step 3: エラー/課題ログの収集

save コマンドの実行後、`references/error-collection.md` を読み込み、手順に従ってエラー/課題を収集する。**このステップはスキップ不可**（stderr の有無に関わらず必ず実行する）。

エラー対応完了後のコミット時は、Skillツールで `git-commit-rules` を読み込んでからコミットフローに入ること。

### Step 4: 完了報告

#### Step 4-1: フロントマター読み取り

**重要**: 保存完了後、**実際に保存されたファイルのフロントマター部分を Read ツールで読み取る**。
`plan_file` 等は `chatlog_utils.py` がJSONLから自動検出して追加するため、自分で推測した内容ではなく実際のファイル内容を報告する。

Read ツールで保存したファイルの先頭20行を読む。

**※ このステップでは play_sound.py を実行しないこと（フロントマター読み取りとサウンド再生の並列実行は禁止）**

#### Step 4-2: 完了報告とサウンド再生

フロントマターの内容を確認した上で、以下の順序で実行する：
1. 報告メッセージを**テキストとして出力する**（下記例の通り）
2. `python3 .claude/skills/save-chatlog/play_sound.py` を**実行して**通知サウンドを再生する
3. `python3 .claude/skills/save-chatlog/check_cleanup.py` を**実行する**。出力に後片付け指示がある場合は「後片付け（tmux環境のみ）」セクションに進む

報告例：
```
✨📝 チャットログ保存完了 📝✨
_chatlog/2026/01/20260115-122733_方向転換ブレスト.md

---
date: 2026-01-15
plan_file: .claude/plans/eager-floating-lantern.md
commits:
  - abc1234
  - def5678
title: 方向転換ブレスト
tags:
  - アーキテクチャ
  - React
  - 方向転換
summary: |
  WordPressリファクタリングからReact管理アプリ開発への方向転換を決定。
  技術選定（React + Vite）、SaaS展開の方針を議論。
---
```

**注意**: `plan_file` はプランモードを使用したセッションで自動追加される。プランファイルがない場合は省略される。

ユーザーが修正を希望した場合は、指示に従ってファイルを編集する。

### 後片付け（tmux環境のみ）

tmux環境の場合のみ実行する。check_cleanup.py の出力で誘導される。

詳細手順は `references/tmux-cleanup.md` を参照。

## 注意事項

- 日本語ファイル名を使用可能（macOS/Linux環境）
- **確認なしで即座に保存**し、完了後に報告する
- フロントマターの修正が必要な場合は、ユーザーが報告後に指示する
- 初回実行時は `.gitignore` への追加も行う
- すべての操作は `python3 chatlog_utils.py <command>` 形式なので、許可設定1つで対応可能

## 参照

詳細なコマンドリファレンスは `references/command-reference.md` を参照。
