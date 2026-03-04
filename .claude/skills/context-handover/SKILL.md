---
name: context-handover
description: |
  Context handover utility. Generates a structured handover file preserving
  full context including user nuance, then sends /compact to free up the
  context window. The handover file is the primary output — rich in detail,
  no size limit.
  Trigger: 「コンパクションして」「コンテキスト圧縮して」「引き継ぎファイル作って」
user-invocable: true
---

# context-handover

コンテキストの重要情報を構造化して引き継ぎファイルに保存するスキル。ニュアンス・経緯を含む詳細な引き継ぎ資料を生成した後、/compact でコンテキストウィンドウを解放する。引き継ぎファイルが主たる成果物であり、情報量に制限はない。

## 処理フロー

### Step 1: 引き継ぎファイル生成（本スキルの主目的）

**情報の構造化保存が目的。引き継ぎファイルの情報量に制限はない。省略やダイエットは不要。**

**⚠ フォークセッション注意**: このセッションがフォークで開始された場合、コンテキストに残っているセッションIDはフォーク元のもの。以下の手順1で必ず `current-session-id` を再実行すること。

1. `current-session-id` スキルでセッションIDを取得する
2. `template.md` を Read し、その指示に従って引き継ぎファイルを生成する
   - 保存先: `.claude/temp/{session_id}_handover.md`
   - フロントマター: `source: skill` マーカーを必ず含める
   - 既存ファイルがある場合: `---` セパレータの後にタイムスタンプ付き新セクションを末尾に追記

### Step 2: /compact 送信（補助処理）

**コンテキストウィンドウの解放。引き継ぎファイル生成後の後処理。**

**tmux 環境の場合**:

`compact.py` を以下の引数で実行する:

```bash
python3 .claude/skills/context-handover/compact.py "会話の詳細は引き継ぎファイルに書き出し済み。サマリーには以下だけ残せ: (1) この会話の目的を1文で (2) 現在の作業段階を1文で (3) 引き継ぎファイル: .claude/temp/{session_id}_handover.md。それ以外は全て破棄してよい。コンパクション完了後はコンパクション前の作業をそのまま続行すること。" ".claude/temp/{session_id}_handover.md" &
```

※ `{session_id}` は Step 1 で取得済みのセッションIDを埋め込むこと

**非 tmux 環境の場合**:

以下のテキストを表示してユーザーに手動実行を依頼する:

```
/compact 会話の詳細は引き継ぎファイルに書き出し済み。サマリーには以下だけ残せ: (1) この会話の目的を1文で (2) 現在の作業段階を1文で (3) 引き継ぎファイル: .claude/temp/{session_id}_handover.md。それ以外は全て破棄してよい。コンパクション完了後はコンパクション前の作業をそのまま続行すること。
```

※ `{session_id}` は Step 1 で取得済みのセッションIDを埋め込むこと

### Step 3: 案内表示

以下を出力する:

> 引き継ぎファイルを生成し、コンパクションを送信しました。コンパクション完了後、作業を自動的に続行します。
