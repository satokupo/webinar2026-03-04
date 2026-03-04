#!/usr/bin/env python3
"""tmux send-keys で /compact コマンドを Claude Code に送信する"""
import os
import re
import shlex
import subprocess
import sys
import time

COMPACT_DELAY = 1       # /compact 送信前の待機秒数


def get_pane_opt(tmux_pane: str) -> str:
    """tmux ペイン指定オプションを構築"""
    return f"-t {shlex.quote(tmux_pane)}" if tmux_pane else ""


def is_copy_mode(pane_opt: str) -> bool:
    """ペインがコピーモード（スクロールバックモード）かどうかを確認"""
    result = subprocess.run(
        f"tmux display-message {pane_opt} -p '#{{pane_in_mode}}'",
        shell=True, capture_output=True, text=True
    )
    return result.stdout.strip() == "1"


def cancel_copy_mode(pane_opt: str) -> None:
    """コピーモードを解除する"""
    subprocess.run(
        f"tmux send-keys {pane_opt} -X cancel",
        shell=True, capture_output=True
    )
    time.sleep(0.3)  # 解除が反映されるまで短く待機


def send_compact(pane_opt: str, compact_cmd: str) -> None:
    """/compact コマンドを tmux send-keys で送信"""
    bash_cmd = (
        f"tmux send-keys {pane_opt} -l {shlex.quote(compact_cmd)} && "
        f"sleep 0.1 && "
        f"tmux send-keys {pane_opt} Enter"
    )
    subprocess.run(["bash", "-c", bash_cmd], capture_output=True)


def extract_session_id(handover_path: str) -> str:
    """ハンドオーバーパスからセッションIDを抽出する"""
    basename = os.path.basename(handover_path)
    match = re.match(r"^(.+?)_handover\.md$", basename)
    return match.group(1) if match else "unknown"


def write_debug_log(session_id: str, entries: list) -> None:
    """デバッグ情報をログファイルに書き出す"""
    log_dir = os.path.join(os.getcwd(), ".claude", "temp")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, f"{session_id}_compact_debug.log")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"--- {time.strftime('%Y-%m-%dT%H:%M:%S%z')} ---\n")
        for entry in entries:
            f.write(f"{entry}\n")
        f.write("\n")


def main():
    instruction = sys.argv[1] if len(sys.argv) > 1 else ""
    handover_path = sys.argv[2] if len(sys.argv) > 2 else ""
    session_id = extract_session_id(handover_path) if handover_path else "unknown"
    tmux_pane = os.environ.get("TMUX_PANE", "")

    if not os.environ.get("TMUX"):
        print("Error: tmux 環境ではありません", file=sys.stderr)
        sys.exit(1)

    compact_cmd = f"/compact {instruction}" if instruction else "/compact"
    pane_opt = get_pane_opt(tmux_pane)

    # コピーモード検知・解除
    copy_mode = is_copy_mode(pane_opt)
    if copy_mode:
        cancel_copy_mode(pane_opt)

    # /compact 送信
    time.sleep(COMPACT_DELAY)
    send_compact(pane_opt, compact_cmd)

    # デバッグログ記録
    write_debug_log(session_id, [
        f"TMUX_PANE: {tmux_pane!r}",
        f"copy_mode_detected: {copy_mode}",
        f"copy_mode_cancelled: {copy_mode}",
        f"compact_cmd_length: {len(compact_cmd)}",
        "send_compact: done",
    ])

    print("/compact コマンドを送信しました")


if __name__ == "__main__":
    main()
