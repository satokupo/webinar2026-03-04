#!/usr/bin/env python3
"""コンパクション後に二段階検知で入力受付を確認し、
tmux send-keys で続行メッセージを自動送信する。

Phase 1: "Compacted" 文字列で コンパクション完了を検知
Phase 2: "❯" マーカーで 入力受付可能を検知

sessionstart-load-handover.py からバックグラウンドプロセスとして起動される。
"""
import os
import shlex
import subprocess
import sys
import time

POLL_INITIAL_WAIT = 2   # 初期待機秒数（コンパクション後なので短め）
POLL_INTERVAL = 1       # capture-pane のポーリング間隔（秒）
PHASE1_TIMEOUT = 30     # Phase 1: Compacted 検知のタイムアウト（秒）
PHASE2_TIMEOUT = 15     # Phase 2: プロンプト検知のタイムアウト（秒）
POST_DETECT_DELAY = 1   # プロンプト検知後、メッセージ送信までの待機（秒）

# 検知パターン
COMPACTED_MARKER = "Compacted"  # Phase 1: コンパクション完了
PROMPT_MARKER = "❯"             # Phase 2: 入力受付可能


def capture_pane(pane_opt):
    """tmux capture-pane で現在のペイン内容を取得"""
    result = subprocess.run(
        ["tmux", "capture-pane"] + (pane_opt.split() if pane_opt else []) + ["-p"],
        capture_output=True,
        text=True,
        timeout=5,
    )
    return result.stdout.rstrip("\n").split("\n")


def poll_for_marker(pane_opt, marker, timeout):
    """指定マーカーを全行から検索するポーリングループ"""
    start = time.time()

    while time.time() - start < timeout:
        try:
            lines = capture_pane(pane_opt)
            for line in lines:
                if marker in line:
                    return True
        except (subprocess.TimeoutExpired, OSError):
            pass
        time.sleep(POLL_INTERVAL)

    return False


def main():
    tmux_pane = os.environ.get("TMUX_PANE", "")
    if not tmux_pane:
        sys.exit(0)

    pane_opt = f"-t {shlex.quote(tmux_pane)}"

    # 初期待機
    time.sleep(POLL_INITIAL_WAIT)

    # Phase 1: "Compacted" でコンパクション完了を検知
    if not poll_for_marker(pane_opt, COMPACTED_MARKER, PHASE1_TIMEOUT):
        sys.exit(0)

    # Phase 2: "❯" で入力受付可能を検知
    if not poll_for_marker(pane_opt, PROMPT_MARKER, PHASE2_TIMEOUT):
        sys.exit(0)

    # 検知後、少し待ってからメッセージ送信
    time.sleep(POST_DETECT_DELAY)

    message = "引き継ぎファイルの内容に基づいて、コンパクション前の作業をそのまま続行してください。"
    send_cmd = [
        "tmux", "send-keys", "-t", tmux_pane, "-l", message,
    ]
    enter_cmd = [
        "tmux", "send-keys", "-t", tmux_pane, "Enter",
    ]
    subprocess.run(send_cmd, capture_output=True, text=True)
    time.sleep(0.1)
    subprocess.run(enter_cmd, capture_output=True, text=True)


if __name__ == "__main__":
    main()
