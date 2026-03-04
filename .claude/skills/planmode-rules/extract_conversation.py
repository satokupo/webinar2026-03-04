#!/usr/bin/env python3
"""
プラン検証用 会話抽出スクリプト

セッションIDからJSONLファイルを読み込み、構造化された会話ログを生成する。

使用方法:
    python3 extract_conversation.py --session-id <UUID> --cwd <出力先ディレクトリ>
"""

import argparse
import glob
import json
import os
import sys
from typing import Any, Dict, List


def _find_jsonl_path_by_session_id(session_id: str) -> str:
    """セッションIDからJSONLパスを返す（ファイル名で全プロジェクトを検索）"""
    projects_dir = os.path.expanduser("~/.claude/projects/")
    matches = glob.glob(os.path.join(projects_dir, "*", f"{session_id}.jsonl"))
    if not matches:
        raise FileNotFoundError(f"Session not found: {session_id}")
    if len(matches) > 1:
        # ディレクトリコピー等で重複がある場合は mtime 最新を返す
        # （session_finder.py の find_jsonl_path_by_session_id と同じ挙動）
        matches.sort(key=os.path.getmtime, reverse=True)
    return matches[0]


def _summarize_tool_use(name: str, input_data: Dict[str, Any]) -> str:
    """tool_useブロックから1行サマリーを生成"""
    if name == "Read":
        return f"[Tool: Read {input_data.get('file_path', '')}]"
    elif name == "Write":
        return f"[Tool: Write {input_data.get('file_path', '')}]"
    elif name == "Edit":
        return f"[Tool: Edit {input_data.get('file_path', '')}]"
    elif name == "Grep":
        pattern = input_data.get("pattern", "")
        path = input_data.get("path", "")
        if path:
            return f'[Tool: Grep "{pattern}" in {path}]'
        return f'[Tool: Grep "{pattern}"]'
    elif name == "Glob":
        return f"[Tool: Glob {input_data.get('pattern', '')}]"
    elif name == "Bash":
        command = input_data.get("command", "")
        truncated = command[:50]
        if len(command) > 50:
            truncated += "..."
        return f"[Tool: Bash {truncated}]"
    elif name == "Task":
        return f"[Tool: Task \"{input_data.get('description', '')}\"]"
    elif name == "Skill":
        return f"[Tool: Skill {input_data.get('skill', '')}]"
    else:
        return f"[Tool: {name}]"


def _extract_user_text(content: Any) -> str:
    """ユーザーメッセージからテキストを抽出"""
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        texts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                texts.append(block.get("text", ""))
            elif isinstance(block, str):
                texts.append(block)
        return "\n".join(texts).strip()
    return ""


def _extract_assistant_content(content: Any) -> str:
    """アシスタントメッセージからテキストとtool callサマリーを抽出"""
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "text":
                text = block.get("text", "").strip()
                if text:
                    parts.append(text)
            elif block.get("type") == "tool_use":
                name = block.get("name", "")
                input_data = block.get("input", {})
                parts.append(_summarize_tool_use(name, input_data))
        return "\n".join(parts)
    return ""


def parse_and_extract(jsonl_path: str) -> Dict:
    """JSONLファイルを解析し、ターン構造の会話データを返す

    Returns: {
        'turns': [{'user': str, 'assistant': str}, ...],
    }
    """
    turns: List[Dict[str, str]] = []
    current_user = None
    current_assistant_parts: List[str] = []

    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue

            msg_type = data.get("type")

            if msg_type == "user" and "message" in data:
                # 前のターンを確定
                if current_user is not None:
                    assistant_text = "\n".join(current_assistant_parts).strip()
                    turns.append({"user": current_user, "assistant": assistant_text})
                    current_assistant_parts = []

                content = data["message"].get("content", "")
                user_text = _extract_user_text(content)
                if user_text:
                    current_user = user_text
                else:
                    current_user = None

            elif msg_type == "assistant" and "message" in data:
                content = data["message"].get("content", "")
                assistant_text = _extract_assistant_content(content)
                if assistant_text:
                    current_assistant_parts.append(assistant_text)

    # 最後のターンを確定
    if current_user is not None:
        assistant_text = "\n".join(current_assistant_parts).strip()
        turns.append({"user": current_user, "assistant": assistant_text})

    return {
        "turns": turns,
    }


def generate_conversation_md(turns: List[Dict[str, str]]) -> str:
    """構造化会話ログ（conversation.md）を生成"""
    parts = []
    for i, turn in enumerate(turns, 1):
        parts.append(f"## ターン {i}")
        parts.append("### User")
        parts.append(turn["user"])
        parts.append("")
        if turn["assistant"]:
            parts.append("### Assistant")
            parts.append(turn["assistant"])
            parts.append("")
    return "\n".join(parts)


def extract(session_id: str, cwd: str) -> None:
    """メイン処理: セッションIDから会話を抽出し、一時ファイルに出力"""
    jsonl_path = _find_jsonl_path_by_session_id(session_id)
    result = parse_and_extract(jsonl_path)

    output_dir = os.path.join(cwd, ".claude", "temp")
    os.makedirs(output_dir, exist_ok=True)

    conversation_path = os.path.join(output_dir, f"{session_id}_conversation.md")
    conversation_md = generate_conversation_md(result["turns"])
    with open(conversation_path, "w", encoding="utf-8") as f:
        f.write(conversation_md)
    print(f"Generated: {conversation_path}")

    print(f"Turns: {len(result['turns'])}")


def main():
    parser = argparse.ArgumentParser(description="プラン検証用 会話抽出スクリプト")
    parser.add_argument("--session-id", type=str, help="セッションID（UUID）")
    parser.add_argument("--cwd", type=str, help="出力先ディレクトリ")

    args = parser.parse_args()

    if not args.session_id or not args.cwd:
        parser.error("--session-id と --cwd は必須です")

    try:
        extract(args.session_id, args.cwd)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
