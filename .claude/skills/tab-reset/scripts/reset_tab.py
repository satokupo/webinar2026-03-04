"""Tab Reset - タブを待機状態にリセットするスクリプト"""

import os
import subprocess
import sys


def main():
    # 1. TMUX環境変数チェック
    tmux_env = os.environ.get("TMUX")
    if not tmux_env:
        print("エラー: tmux環境ではありません", file=sys.stderr)
        sys.exit(1)

    # 2. TMUX_PANE取得
    tmux_pane = os.environ.get("TMUX_PANE", "")
    if not tmux_pane:
        print("注意: TMUX_PANE未設定のためカレントウィンドウを対象にします", file=sys.stderr)

    # 3. タブ名をデフォルト（動的表示）に戻す
    reset_cmd = ["tmux", "set-window-option"]
    if tmux_pane:
        reset_cmd += ["-t", tmux_pane]
    reset_cmd += ["automatic-rename", "on"]

    result = subprocess.run(reset_cmd)
    if result.returncode != 0:
        print("エラー: tmux set-window-option に失敗しました", file=sys.stderr)
        sys.exit(1)

    # 4. /clear を遅延送信（バックグラウンドプロセス）
    # Claude Code がプロンプトに戻った後に送信するため、遅延が必要
    # テキスト送信と Enter 送信を分離しないと、ink TUI が
    # Enter を改行として処理してしまう（GitHub Issue #2929 参照）
    delay_seconds = 1
    pane_opt = f"-t '{tmux_pane}'" if tmux_pane else ""
    bash_cmd = (
        f"sleep {delay_seconds} && "
        f"tmux send-keys {pane_opt} -l '/clear' && "
        f"sleep 0.1 && "
        f"tmux send-keys {pane_opt} Enter"
    )

    subprocess.Popen(
        ["bash", "-c", bash_cmd],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )

    # 5. 成功メッセージ
    print(f"タブ名をデフォルト（動的表示）に戻しました。{delay_seconds}秒後に /clear を送信します。")


if __name__ == "__main__":
    main()
