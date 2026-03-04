#!/usr/bin/env python3
"""tmuxウィンドウを終了するスクリプト（TMUX_PANEから安全にターゲティング）"""

import os
import subprocess
import sys


def main():
    # 1. TMUX環境変数チェック
    tmux_env = os.environ.get("TMUX")
    if not tmux_env:
        print("エラー: tmux環境ではありません", file=sys.stderr)
        sys.exit(1)

    # 2. TMUX_PANEからwindow_idを取得
    tmux_pane = os.environ.get("TMUX_PANE", "")
    if not tmux_pane:
        print("エラー: TMUX_PANEが未設定です", file=sys.stderr)
        sys.exit(1)

    result = subprocess.run(
        ["tmux", "display-message", "-p", "-t", tmux_pane, "#{window_id}"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("エラー: window_idの取得に失敗しました", file=sys.stderr)
        sys.exit(1)

    window_id = result.stdout.strip()
    if not window_id:
        print("エラー: window_idが空です", file=sys.stderr)
        sys.exit(1)

    # 3. tmux kill-windowを実行
    result = subprocess.run(["tmux", "kill-window", "-t", window_id])
    if result.returncode != 0:
        print("エラー: tmux kill-window に失敗しました", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
