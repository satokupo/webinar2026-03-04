# save-chatlog（チャットログ保存）

## 概要

セッションの会話ログを日付プレフィックス付きのマークダウン形式で保存するスキル。
YAML フロントマター（日付・タイトル・タグ・要約）を自動生成し、確認なしで即座に保存する。

ログは日付順に `_chatlog/YYYY/MM/` に格納され、フロントマターで検索性を上げているため、過去のチャットの内容を引っ張ってきて何か作業したいときにも便利。Claude Code はデフォルトだとチャットログが保存しにくいので、残しておきたいセッションを自分で明示的に保存していく運用になる。

もともとはただのチャット保存だけのスキルだったが、「セッションを閉じる」作業として使われるうちに、プランファイルのアーカイブ、一時ファイルのクリーンアップ、エラーログの収集といった後片付け機能が追加されていき、直列フローの最後尾でセッションの「閉じ」を一手に担うスキルになった。

---

## 内部フロー

### Step 1: フロントマター生成

LLM が会話履歴を見て直接生成する。Python スクリプトではなく Claude 自身が判断する工程。

```
入力: それまでの会話履歴
  ↓
生成するフィールド:
  - date: チャット開始日（YYYY-MM-DD）
  - title: 最初の数ターンから推測した主題
  - tags: 技術キーワード・作業種別（3〜5個）
  - summary: 2〜3行の要約
  - commits: セッション中の git commit ハッシュ（短縮形）一覧
  ↓
※ plan_file は Python 側が JSONL から自動検出するため、LLM は指定しない
```

---

### Step 2: 保存を実行

**Step 2-1: セッション ID 取得**

`current-session-id` スキルを呼び出してセッション UUID を取得する。

**関連スキル**: [current-session-id](../02_サブスキル/current-session-id.md)

**Step 2-2: マークダウン保存コマンド実行**

```
python3 chatlog_utils.py save \
  "<project>/_chatlog/" \
  --cwd "$(pwd)" \
  --title "タイトル" \
  --tags "tag1,tag2,tag3" \
  --summary "要約文" \
  --session-id "<UUID>" \
  --commits "abc1234,def5678" \
  --auto-merge
```

保存時に Python 側が自動処理する内容:

```
1. セッション JSONL を検索・パースして会話本文を抽出
2. YAML フロントマター + マークダウン本文を生成
3. --auto-merge: プランファイルの planning-session を検索し、
   計画セッションと実装セッションを自動マージ
4. プランファイルを plans/YYYY/MM/ にアーカイブ
5. {session_id}_ プレフィックス付き一時ファイルを一括削除
6. ファイル保存: _chatlog/YYYY/MM/YYYYMMDD-HHMMSS_タイトル.md
```

---

### Step 3: エラー/課題ログの収集（スキップ不可）

保存完了後、`error_collector.py` がセッション中のエラーを機械検出する。

```
検出対象: Assistant の発言のみ（User 発言は偽陽性対策で除外）
  ↓
検出パターン:
  - traceback: Python のスタックトレース
  - exit_code: 終了コード 0 以外
  - permission_denied: ツール使用の拒否
  - error: Error: を含む行
  ↓
除外: save-chatlog 自身のスクリプト関連のエラー
  ↓
エラーあり → LLM がログを生成し .claude/context/issues/ に保存
エラー対応後のコミット → git-commit-rules スキルを読み込み
```

**関連スキル**: [git-commit-rules](../02_サブスキル/git-commit-rules.md)

---

### Step 4: 完了報告

**Step 4-1: 保存内容の確認**

保存したファイルの先頭20行を `Read` ツールで実際に読み取り、フロントマターの内容を報告する。
LLM の推測ではなく、実ファイルの内容を表示する。

**Step 4-2: サウンド再生と後片付け**

```
1. 完了メッセージを出力（ファイルパス + フロントマター内容）
2. play_sound.py を実行（テッテレー.mp3 を再生）
3. check_cleanup.py を実行
  ↓
tmux 環境の場合 → AskUserQuestion で選択肢を提示:
  選択肢:
    1. タブをリセット（推奨）→ tab-reset スキルを発動
    2. タブを終了 → tmux ウィンドウを閉じる
```

**関連スキル**: [tab-reset](../02_サブスキル/tab-reset.md)

---

## フロー全体図

```
Step 1           Step 2                Step 3             Step 4
フロントマター → 保存実行          →   エラーログ収集  →  完了報告
LLMが直接生成    current-session-id     error_collector     Read で実ファイル確認
                 chatlog_utils.py       → issues/ に保存    play_sound.py
                 プランアーカイブ       git-commit-rules    check_cleanup.py
                 一時ファイル削除                            tab-reset（tmux）
```

---

## YAML フロントマターの構造

**単一セッションの場合:**

```yaml
---
date: 2026-01-15
session_id: <UUID>
plan_file: .claude/plans/2026/01/20260115-XXXXXX_タイトル.md
commits:
  - abc1234
  - def5678
title: 方向転換ブレスト
tags:
  - アーキテクチャ
  - React
summary: |
  方向転換を決定。技術選定とSaaS展開の方針を議論。
---
```

**複数セッション自動マージの場合:**

```yaml
---
date: 2026-01-22
session_ids:
  - c6dd2b20-...   # 計画セッション
  - 0331cd8f-...   # 実装セッション
plan_files:
  - .claude/plans/plan1.md
  - .claude/plans/plan2.md
commits:
  - abc1234
title: マージタイトル
tags:
  - ...
summary: |
  ...
---
```

`plan_file`（単数）と `plan_files`（複数）は自動で使い分けられる。

---

## このスキルで工夫したポイント

<div style="padding: 0 56px; display: flex; flex-direction: column; gap: 16px;">

<div style="border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden;">
<h3 style="margin: 0; padding: 12px 20px; font-size: 16px; font-weight: 700; border-bottom: 1px solid #bfdbfe; background: #dbeafe; color: #1d4ed8;">セッションが分かれてもログは1ファイルに収まる</h3>
<div style="padding: 12px 20px 16px;">

planmode-rules を使うと、プランニングと実装がセッションをまたぐことが多い。`--auto-merge` により、プランファイルの `planning-session:` フィールドを手がかりに計画セッションを自動検出し、両方のセッションの会話を引っ張ってきて1つのログファイルに統合する。

さらに、プランファイル自体もリネーム・アーカイブしてパスをフロントマターに埋め込むので、「そのセッションで何を決めて、何を作ったか」がログファイル1つでほぼ全部拾える状態になる。事前情報のないセッションでも実装できるように作られたプランファイルと、実際の会話ログが紐づいている形。

</div>
</div>

<div style="border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden;">
<h3 style="margin: 0; padding: 12px 20px; font-size: 16px; font-weight: 700; border-bottom: 1px solid #bfdbfe; background: #dbeafe; color: #1d4ed8;">一時ファイルの一括クリーンアップ</h3>
<div style="padding: 12px 20px 16px;">

セッション中にはいろんな一時ファイルが作られる（conversation.md、handover.md 等）。これらは `{session_id}_` プレフィックスを付けるという共通ルールがあるので、保存時に `.claude/temp/` 内の同じプレフィックスが付いたファイルをまとめて削除する。

マージモードでは統合された全セッションの ID が対象になるため、計画セッション側の一時ファイルも漏れなく回収できる。

</div>
</div>

<div style="border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden;">
<h3 style="margin: 0; padding: 12px 20px; font-size: 16px; font-weight: 700; border-bottom: 1px solid #bfdbfe; background: #dbeafe; color: #1d4ed8;">tmux 環境でのタブリセット</h3>
<div style="padding: 12px 20px 16px;">

tmux 環境が検出された場合、保存完了後に「タブをリセットするか」「タブを終了するか」をユーザーに確認する。リセットを選ぶと tab-reset スキルが発動し、タブの名前もデフォルトに戻る。

summon-experts で議題に応じて自動的に付けられたタブ名が、save-chatlog でリセットされてまた使える状態に戻る、というサイクルになっている。

</div>
</div>

</div>
