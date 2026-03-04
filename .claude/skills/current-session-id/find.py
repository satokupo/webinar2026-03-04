#!/usr/bin/env python3
"""
current-session-id: セッション検索スクリプト

マーカー文字列で JSONL ファイルを検索し、セッションIDを特定する。
"""

import argparse
import glob
import os
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--marker", required=True)
    args = parser.parse_args()

    projects_dir = os.path.expanduser("~/.claude/projects/")
    if not os.path.isdir(projects_dir):
        print("Error: ~/.claude/projects/ not found", file=sys.stderr)
        sys.exit(1)

    # 全プロジェクト配下の JSONL を収集（1階層構造なので */ で十分）
    jsonl_files = glob.glob(os.path.join(projects_dir, "*", "*.jsonl"))
    if not jsonl_files:
        print("Error: No .jsonl files found", file=sys.stderr)
        sys.exit(1)

    # mtime 降順（新しい順）でソート → 早期打ち切り
    jsonl_files.sort(key=lambda f: os.path.getmtime(f), reverse=True)

    for filepath in jsonl_files:
        try:
            with open(filepath, encoding="utf-8") as f:
                content = f.read()
            if args.marker in content:
                session_id = os.path.splitext(os.path.basename(filepath))[0]
                print(session_id)
                return
        except (OSError, UnicodeDecodeError):
            continue

    print(f"Error: Session not found for marker: {args.marker}", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
