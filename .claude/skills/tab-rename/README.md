---
public: true
---

# tab-rename

tmux または VS Code 統合ターミナルのタブをリネームするスキル。

## 対応環境

- **tmux**: 設定不要。tmux セッション内で自動検出される
- **VS Code 統合ターミナル**: 拡張機能のセットアップが必要（後述）
- macOS 前提（VS Code 連携で `open` コマンドを使用）

## VS Code セットアップ

```bash
python3 scripts/setup_tab_rename.py
```

実行後、VS Code のリロード（`Developer: Reload Window`）が必要。

## 使い方

Claude Code のスキルとして自動発動する。手動実行も可能:

```bash
python3 scripts/rename_tab.py "タイトル"
```

## ファイル構成

```
tab-rename/
├── SKILL.md                        # スキル定義
├── README.md                       # このファイル
├── scripts/
│   ├── rename_tab.py               # タブリネーム実行スクリプト
│   └── setup_tab_rename.py         # VS Code 拡張機能セットアップ
└── vscode-extension/
    ├── package.json                # 拡張機能マニフェスト
    └── extension.js                # 拡張機能本体（URI ハンドラ）
```
