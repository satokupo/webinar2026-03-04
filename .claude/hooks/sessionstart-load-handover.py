#!/usr/bin/env python3
"""
SessionStart Hook: コンパクション後のセッション再開時にハンドオーバーファイルを読み込む

stdin から hook 入力 JSON を受け取り、
{cwd}/.claude/temp/{session_id}_handover.md（スキル生成）および
{cwd}/.claude/temp/{session_id}_autocompact.md（フック生成）を探索し、
見つかったものを additionalContext として stdout に出力する。

両方存在すれば結合（handover を先頭に配置）。
どちらもない場合はフェイルオープン（ハンドオーバーなしで通常再開）。
削除は save-chatlog に委譲する。
"""

import json
import os
import subprocess
import sys


def main():
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error: stdin JSON の読み込みに失敗: {e}", file=sys.stderr)
        sys.exit(0)  # フェイルオープン

    session_id = hook_input.get("session_id", "")
    cwd = hook_input.get("cwd", "")

    if not session_id or not cwd:
        print("Error: 必須フィールド (session_id, cwd) が不足", file=sys.stderr)
        sys.exit(0)  # フェイルオープン

    # 引き継ぎファイルを探索（handover: スキル生成、autocompact: フック生成）
    temp_dir = os.path.join(cwd, ".claude", "temp")
    handover_path = os.path.join(temp_dir, f"{session_id}_handover.md")
    autocompact_path = os.path.join(temp_dir, f"{session_id}_autocompact.md")

    parts = []

    # handover（スキル生成）を優先で探索
    if os.path.exists(handover_path):
        try:
            with open(handover_path, "r", encoding="utf-8") as f:
                parts.append(f.read())
            print(f"Handover file loaded: {handover_path}", file=sys.stderr)
        except OSError as e:
            print(f"Error: handover ファイルの読み込みに失敗: {e}", file=sys.stderr)

    # autocompact（フック生成）も探索
    if os.path.exists(autocompact_path):
        try:
            with open(autocompact_path, "r", encoding="utf-8") as f:
                parts.append(f.read())
            print(f"Autocompact file loaded: {autocompact_path}", file=sys.stderr)
        except OSError as e:
            print(f"Error: autocompact ファイルの読み込みに失敗: {e}", file=sys.stderr)

    if not parts:
        print(
            f"引き継ぎファイルが見つかりませんでした: {handover_path}, {autocompact_path}",
            file=sys.stderr,
        )
        sys.exit(0)  # フェイルオープン

    # 両方存在すれば結合（handover を先頭に配置）
    content = "\n\n---\n\n".join(parts)

    # handover.md（スキル生成）が存在し、tmux 環境であれば自動続行プロセスを起動
    if os.path.exists(handover_path) and os.environ.get("TMUX"):
        script_path = os.path.join(os.path.dirname(__file__), "send-continue.py")
        if os.path.exists(script_path):
            subprocess.Popen(
                ["python3", script_path],
                start_new_session=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

    # additionalContext として stdout に出力
    output = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": content,
        }
    }
    json.dump(output, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
