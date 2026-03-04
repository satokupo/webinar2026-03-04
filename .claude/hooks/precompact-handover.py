#!/usr/bin/env python3
"""
PreCompact Hook: コンパクション前にハンドオーバーファイルを生成する

stdin から hook 入力 JSON を受け取り、transcript JSONL をパースして
{cwd}/.claude/temp/{session_id}_autocompact.md に保存する。

フェイルオープン: エラー時はハンドオーバーなしで通常再開。
"""

import json
import os
import shutil
import subprocess
import sys
import time
from collections import deque
from datetime import datetime

PARSE_TIMEOUT_SECONDS = 15
SONNET_TIMEOUT_SECONDS = 45


def _find_claude_cli():
    """claude CLI のパスを検索する。"""
    known_path = os.path.expanduser("~/.local/bin/claude")
    if os.path.isfile(known_path) and os.access(known_path, os.X_OK):
        return known_path
    found = shutil.which("claude")
    return found  # None if not found


def _trim_text(text, max_chars):
    """テキストを末尾優先でトリムする。"""
    if len(text) <= max_chars:
        return text
    return "...(省略)...\n" + text[-max_chars:]


def parse_transcript(transcript_path):
    """transcript JSONL をパースしてハンドオーバー情報を抽出する。

    Returns:
        dict: {
            'initial_task': str,
            'recent_turns': [(user_msg, assistant_msg), ...],
            'modified_files': [(path, operation), ...],
            'plan_files': [path, ...],
        }
    """
    initial_task = ""
    # リングバッファ: 直近10ターン分を保持
    recent_turns = deque(maxlen=10)
    modified_files = []
    modified_files_seen = set()
    plan_files = []
    plan_files_seen = set()

    current_user_msg = None
    start_time = time.monotonic()

    with open(transcript_path, "r", encoding="utf-8") as f:
        for line in f:
            # タイムアウトガード
            if time.monotonic() - start_time > PARSE_TIMEOUT_SECONDS:
                print(
                    f"Warning: タイムアウト({PARSE_TIMEOUT_SECONDS}秒)に達しました。"
                    "現時点までの結果を使用します。",
                    file=sys.stderr,
                )
                break

            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue

            # user メッセージ
            if data.get("type") == "user" and "message" in data:
                content = data["message"].get("content", "")
                if isinstance(content, str) and content.strip():
                    # 最初の user メッセージをタスク概要として記録
                    if not initial_task:
                        initial_task = content.strip()
                    current_user_msg = content.strip()

            # assistant メッセージ
            elif data.get("type") == "assistant" and "message" in data:
                content = data["message"].get("content", "")

                # content が list の場合: text 部分を結合
                if isinstance(content, list):
                    text_parts = []
                    for item in content:
                        if item.get("type") == "text":
                            text_parts.append(item.get("text", ""))

                        # tool_use から変更ファイル・プランファイルを抽出
                        if item.get("type") == "tool_use":
                            tool_name = item.get("name", "")
                            file_path = item.get("input", {}).get("file_path", "")

                            # 変更されたファイル
                            if tool_name in ("Write", "Edit") and file_path:
                                key = (file_path, tool_name)
                                if key not in modified_files_seen:
                                    modified_files_seen.add(key)
                                    modified_files.append(key)

                            # プランファイル
                            if (
                                tool_name in ("Write", "Read")
                                and file_path
                                and ".claude/plans/" in file_path
                            ):
                                if file_path not in plan_files_seen:
                                    plan_files_seen.add(file_path)
                                    plan_files.append(file_path)

                    content = "\n".join(text_parts)

                if isinstance(content, str) and content.strip():
                    assistant_msg = content.strip()
                    if current_user_msg:
                        recent_turns.append((current_user_msg, assistant_msg))
                        current_user_msg = None

    return {
        "initial_task": initial_task,
        "recent_turns": list(recent_turns),
        "modified_files": modified_files,
        "plan_files": plan_files,
    }


def find_planmode_logs(temp_dir):
    """Phase4の一時ファイル（会話ログ）を検出する。

    Returns:
        list[tuple[str, str]]: [(ファイルパス, 種別), ...]
        種別は 'user_statements' または 'conversation'
    """
    found = []
    if not os.path.isdir(temp_dir):
        return found
    for name in os.listdir(temp_dir):
        if name.startswith("user_statements-") and name.endswith(".md"):
            found.append((os.path.join(temp_dir, name), "user_statements"))
        elif name.startswith("conversation-") and name.endswith(".md"):
            found.append((os.path.join(temp_dir, name), "conversation"))
    return found


def generate_handover_md(session_id, trigger, cwd, info, planmode_logs):
    """ハンドオーバー Markdown を生成する。"""
    created_at = datetime.now().isoformat()

    lines = [
        "---",
        f"session_id: {session_id}",
        f"created_at: {created_at}",
        f"trigger: {trigger}",
        f"cwd: {cwd}",
        "---",
        "",
        "# Handover Context",
        "",
    ]

    # Initial Task
    if info["initial_task"]:
        lines.append("## Initial Task")
        lines.append(info["initial_task"])
        lines.append("")

    # Recent Conversation
    if info["recent_turns"]:
        lines.append("## Recent Conversation")
        for user_msg, assistant_msg in info["recent_turns"]:
            lines.append("### User")
            lines.append(user_msg)
            lines.append("### Assistant")
            lines.append(assistant_msg)
            lines.append("")

    # Files Modified
    if info["modified_files"]:
        lines.append("## Files Modified")
        for file_path, operation in info["modified_files"]:
            lines.append(f"- {file_path} ({operation})")
        lines.append("")

    # Active Plan
    if info["plan_files"]:
        lines.append("## Active Plan")
        for plan_path in info["plan_files"]:
            lines.append(plan_path)
        lines.append("")

    # Phase4 会話ログ（存在する場合のみ）
    if planmode_logs:
        lines.append("## プランモード会話ログ（参照可能）")
        lines.append("")
        lines.append("以下のファイルにプランモードの詳細な会話ログが残っています。")
        lines.append("プランモード作業の継続で、ハンドオーバーの情報では文脈が不足する場合に参照できます。")
        lines.append("")
        for path, kind in planmode_logs:
            rel_path = os.path.relpath(path, cwd)
            if kind == "user_statements":
                lines.append(f"- ユーザー発言抜粋: {rel_path}（軽量・まず確認）")
            elif kind == "conversation":
                lines.append(f"- 全会話ログ: {rel_path}（詳細な経緯が必要な場合）")
        lines.append("")
        lines.append("読み込みの判断:")
        lines.append("- プランモード作業の継続であり、議論経緯の詳細が必要と判断した場合は読み込んでよい")
        lines.append("- 判断に迷う場合はユーザーに「プランモードの会話ログが残っていますが、読みますか？」と確認する")
        lines.append("- プランモード以外の作業の復帰では、このセクションは無視してよい")
        lines.append("")

    return "\n".join(lines)


def build_sonnet_prompt(session_id, trigger, cwd, info, planmode_logs):
    """Sonnet に渡すプロンプトを構築する。"""
    parts = []

    parts.append(
        "あなたはコンテキスト引き継ぎの専門家です。\n"
        "以下の会話データを分析し、新しいセッションのAIがこのファイルだけで作業を再開できる"
        "引き継ぎドキュメントを生成してください。\n"
    )

    # セクション構造の指示
    parts.append(
        "## 出力フォーマット\n\n"
        "以下のセクション構造で Markdown を出力してください。\n"
        "フロントマターは不要です（呼び出し元で付与します）。\n\n"
        "### ユーザーの要望とニュアンス\n"
        "- ユーザーが達成したいことを要約\n"
        "- ユーザーの言い回し・トーン・暗黙の期待を含めて記述\n"
        "- 「何を重視しているか」「何を避けたいか」を明記\n\n"
        "### 現在の作業段階\n"
        "- どのスキル/フローのどのフェーズにいるか\n"
        "- 次に実行すべきステップ\n\n"
        "### プラン情報（プランがある場合のみ）\n"
        "- プランファイルのフルパス\n"
        "- プランの概要（1-2文）\n\n"
        "### 重要な決定事項と経緯\n"
        "- 何をしようとしていたか（目的）\n"
        "- どういう選択肢が検討されたか\n"
        "- なぜこの結論になったか（理由・過程）\n"
        "- 棄却した選択肢とその理由も含める\n\n"
        "### 次にやるべきこと\n"
        "1. 具体的なアクションを順番に列挙\n"
        "2. 必要なスキル名・コマンド名を明記\n\n"
        "### コンパクション後の指示\n"
        "- 「引き継ぎファイルの内容に基づいて状態を復元し、"
        "コンパクション前の作業をそのまま続行すること」\n"
    )

    # 記述の心得
    parts.append(
        "## 記述の心得\n\n"
        "- **最重要**: ユーザーのニュアンス（好み・懸念・トーン）は必ず残す\n"
        "- 新セッションのAIがこのファイルだけ読んで作業を再開できる詳細さで書く\n"
        "- 情報量の多さを気にしない。必要な情報は漏れなく書くこと\n"
    )

    # 会話データ
    parts.append("---\n\n## 会話データ\n")

    if info["initial_task"]:
        parts.append(f"### ユーザーの最初の依頼\n\n{info['initial_task']}\n")

    if info["recent_turns"]:
        parts.append("### 直近の会話\n")
        for user_msg, assistant_msg in info["recent_turns"]:
            trimmed_user = _trim_text(user_msg, 2000)
            trimmed_assistant = _trim_text(assistant_msg, 3000)
            parts.append(f"**User**: {trimmed_user}\n")
            parts.append(f"**Assistant**: {trimmed_assistant}\n")

    if info["modified_files"]:
        parts.append("### 変更ファイル一覧\n")
        for file_path, operation in info["modified_files"]:
            parts.append(f"- {file_path} ({operation})")
        parts.append("")

    if info["plan_files"]:
        parts.append("### プランファイル\n")
        for plan_path in info["plan_files"]:
            parts.append(f"- {plan_path}")
        parts.append("")

    if planmode_logs:
        parts.append("### プランモード会話ログ（参照可能ファイル）\n")
        for path, kind in planmode_logs:
            rel_path = os.path.relpath(path, cwd)
            if kind == "user_statements":
                parts.append(f"- ユーザー発言抜粋: {rel_path}")
            elif kind == "conversation":
                parts.append(f"- 全会話ログ: {rel_path}")
        parts.append("")

    return "\n".join(parts)


def call_sonnet(prompt):
    """claude --print で Sonnet を呼び出す。失敗時は None を返す。"""
    claude_cli = _find_claude_cli()
    if not claude_cli:
        print("Warning: claude CLI が見つかりません。フォールバックします。", file=sys.stderr)
        return None

    cmd = [
        claude_cli,
        "--print",
        "--model", "sonnet",
        "--no-session-persistence",
        prompt,
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=SONNET_TIMEOUT_SECONDS,
            encoding="utf-8",
        )
    except subprocess.TimeoutExpired:
        print(
            f"Warning: Sonnet 呼び出しがタイムアウト({SONNET_TIMEOUT_SECONDS}秒)。フォールバックします。",
            file=sys.stderr,
        )
        return None
    except FileNotFoundError:
        print("Warning: claude CLI の実行に失敗。フォールバックします。", file=sys.stderr)
        return None

    if result.returncode != 0:
        print(
            f"Warning: claude --print が非ゼロ終了コード({result.returncode})。フォールバックします。",
            file=sys.stderr,
        )
        if result.stderr:
            print(f"  stderr: {result.stderr[:500]}", file=sys.stderr)
        return None

    output = result.stdout.strip()
    if not output:
        print("Warning: Sonnet の出力が空です。フォールバックします。", file=sys.stderr)
        return None

    # キーセクションの存在チェック
    if "ユーザーの要望とニュアンス" not in output and "次にやるべきこと" not in output:
        print(
            "Warning: Sonnet の出力にキーセクションが含まれていません。フォールバックします。",
            file=sys.stderr,
        )
        return None

    return output


def main():
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error: stdin JSON の読み込みに失敗: {e}", file=sys.stderr)
        sys.exit(0)  # フェイルオープン

    session_id = hook_input.get("session_id", "")
    transcript_path = hook_input.get("transcript_path", "")
    cwd = hook_input.get("cwd", "")
    trigger = hook_input.get("trigger", "unknown")

    if not session_id or not transcript_path or not cwd:
        print("Error: 必須フィールド (session_id, transcript_path, cwd) が不足", file=sys.stderr)
        sys.exit(0)  # フェイルオープン

    if not os.path.exists(transcript_path):
        print(f"Error: transcript が見つかりません: {transcript_path}", file=sys.stderr)
        sys.exit(0)  # フェイルオープン

    # スキル生成の handover.md が存在する場合、autocompact は不要
    temp_dir = os.path.join(cwd, ".claude", "temp")
    handover_path = os.path.join(temp_dir, f"{session_id}_handover.md")
    if os.path.exists(handover_path):
        print(
            f"Skip: スキル生成の handover.md が存在するため autocompact をスキップ: {handover_path}",
            file=sys.stderr,
        )
        sys.exit(0)

    # transcript パース
    info = parse_transcript(transcript_path)

    # 保存先ディレクトリ作成
    temp_dir = os.path.join(cwd, ".claude", "temp")
    os.makedirs(temp_dir, exist_ok=True)

    # Phase4ファイルの存在チェック
    planmode_logs = find_planmode_logs(temp_dir)

    # フォールバック用: 従来の機械パース結果を生成
    fallback_md = generate_handover_md(session_id, trigger, cwd, info, planmode_logs)

    # Sonnet 呼び出し試行
    created_at = datetime.now().isoformat()
    sonnet_output = None
    has_conversation_data = bool(info["initial_task"] or info["recent_turns"])

    if has_conversation_data:
        prompt = build_sonnet_prompt(session_id, trigger, cwd, info, planmode_logs)
        sonnet_output = call_sonnet(prompt)

    if sonnet_output:
        # Sonnet 成功: フロントマター付きで出力
        handover_md = (
            "---\n"
            f"session_id: {session_id}\n"
            f"created_at: {created_at}\n"
            f"trigger: {trigger}\n"
            f"cwd: {cwd}\n"
            "source: autocompact-sonnet\n"
            "---\n\n"
            f"{sonnet_output}\n"
        )
        print("Sonnet による高品質ハンドオーバーを生成しました。", file=sys.stderr)
    else:
        # フォールバック: 従来の機械パース結果を使用
        handover_md = fallback_md
        if has_conversation_data:
            print("Sonnet 呼び出し失敗。従来の機械パース結果を使用します。", file=sys.stderr)

    # ファイル保存（既存なら上書き）
    output_path = os.path.join(temp_dir, f"{session_id}_autocompact.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(handover_md)

    print(f"Autocompact file generated: {output_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
