---
name: tab-reset
description: |
  Reset a tab to standby state: restore automatic-rename (dynamic display) and send /clear.
  tmux only.
  Trigger: 「待機にして」「このタブ終わり」「リセットして」「タブリセット」
user-invocable: true
---

# Tab Reset

作業完了したタブを「待機状態」にリセットするスキル。タブ名をデフォルト（動的表示）に戻し、/clear を送信してコンテキストをクリアする。

## 前提条件

- tmux環境のみ対応
- TMUX_PANEで特定されるウィンドウ（タブ）が対象

## 処理フロー

### ステップ1: スクリプト実行

確認不要。即座に実行する。

```bash
python3 .claude/skills/tab-reset/scripts/reset_tab.py
```

### ステップ2: 結果報告

スクリプトの stdout をそのまま伝える。

## 重要な制約

- **軽量化**: サブエージェント・ファイル読み込み等の重い処理は行わない
- **追加の調査やファイル読み込みは一切行わない**
