#!/usr/bin/env python3
"""
Codexレビュー実行スクリプト（Phase 5 オプション）

codex exec を使って非対話的にCodexをレビュアーとして呼び出し、
プランの技術的健全性をレビューする。

使用方法:
    # 初回レビュー
    python3 codex_reviewer.py review --plan <プランファイルパス> --cwd <作業ディレクトリ>

    # 追加質問
    python3 codex_reviewer.py followup --codex-session <スレッドID> --question "質問" --cwd <作業ディレクトリ>
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


EXEC_TIMEOUT = 600  # 10分


def _check_codex_installed() -> None:
    """codex コマンドの存在を確認"""
    if shutil.which("codex") is None:
        print(
            json.dumps(
                {"error": "codex コマンドが見つかりません。Codex CLIをインストールしてください。"},
                ensure_ascii=False,
                indent=2,
            )
        )
        sys.exit(1)


def _ensure_temp_dir(cwd: str) -> Path:
    """一時ファイルディレクトリを確保"""
    temp_dir = Path(cwd) / ".claude" / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir


def _parse_jsonl_output(raw_output: str) -> dict:
    """codex exec の JSONL 出力を解析し、スレッドIDとレビュー本文を抽出

    Codex CLI --json の JSONL イベントフォーマット:
    - thread.started: スレッドIDを含む
    - item.completed + item.type == "agent_message": レビュー本文を含む
    - turn.completed: usage情報を含む
    - error / turn.failed: エラー情報

    Returns:
        {
            "thread_id": str | None,
            "review_text": str,
            "errors": list[str],
            "usage": dict | None,
        }
    """
    thread_id: str | None = None
    text_parts: list[str] = []
    errors: list[str] = []
    usage: dict | None = None

    for line in raw_output.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        event_type = event.get("type", "")

        # スレッドID抽出
        if event_type == "thread.started":
            thread_id = event.get("thread_id")

        # レビュー本文抽出（agent_message の完了イベント）
        if event_type == "item.completed":
            item = event.get("item", {})
            if item.get("type") == "agent_message":
                text = item.get("text", "")
                if text:
                    text_parts.append(text)

        # エラーイベント
        if event_type == "error":
            error_msg = event.get("message", "不明なエラー")
            errors.append(f"error: {error_msg}")

        if event_type == "turn.failed":
            error_info = event.get("error", {})
            if isinstance(error_info, dict):
                error_msg = error_info.get("message", "ターン失敗")
            else:
                error_msg = str(error_info)
            errors.append(f"turn.failed: {error_msg}")

        # usage情報抽出（複数ターンの場合は加算）
        if event_type == "turn.completed":
            usage_data = event.get("usage")
            if usage_data:
                if usage is None:
                    usage = {
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "cached_input_tokens": 0,
                    }
                usage["input_tokens"] += usage_data.get("input_tokens", 0)
                usage["output_tokens"] += usage_data.get("output_tokens", 0)
                usage["cached_input_tokens"] += usage_data.get("cached_input_tokens", 0)

    # スレッドIDが JSONL イベントから取得できなかった場合、正規表現で最終手段
    if thread_id is None:
        match = re.search(r'"thread_id"\s*:\s*"([^"]+)"', raw_output)
        if match:
            thread_id = match.group(1)

    return {
        "thread_id": thread_id,
        "review_text": "\n\n".join(text_parts) if text_parts else "",
        "errors": errors,
        "usage": usage,
    }


def review(plan_path: str, cwd: str, session_id: str) -> None:
    """初回レビュー実行"""
    _check_codex_installed()

    plan_file = Path(plan_path)
    if not plan_file.exists():
        print(
            json.dumps(
                {"error": f"プランファイルが見つかりません: {plan_path}"},
                ensure_ascii=False,
                indent=2,
            )
        )
        sys.exit(1)

    temp_dir = _ensure_temp_dir(cwd)

    # 定型プロンプト構築（外部テンプレートファイルから読み込み）
    template_path = Path(__file__).parent / "subagent-prompts" / "codex-review.md"
    prompt_text = template_path.read_text(encoding="utf-8").format(plan_file_path=plan_path)

    # codex exec 実行（stdinでプロンプトを渡す）
    cmd = [
        "codex", "--search", "exec",
        "-s", "read-only",
        "-C", cwd,
        "--json",
        "-",
    ]

    try:
        result = subprocess.run(
            cmd,
            input=prompt_text,
            capture_output=True,
            text=True,
            timeout=EXEC_TIMEOUT,
            encoding="utf-8",
        )
    except subprocess.TimeoutExpired as e:
        # タイムアウト時、部分出力があれば保存
        partial_output = ""
        if e.stdout:
            partial_output = e.stdout if isinstance(e.stdout, str) else e.stdout.decode("utf-8", errors="replace")

        if partial_output:
            partial_file = temp_dir / f"{session_id}_codex-review-timeout.md"
            partial_file.write_text(
                f"# Codexレビュー（タイムアウト - 部分出力）\n\n{partial_output}",
                encoding="utf-8",
            )
            print(
                json.dumps(
                    {
                        "error": f"タイムアウト（{EXEC_TIMEOUT}秒）。部分出力を保存しました。",
                        "partial_file": str(partial_file),
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            print(
                json.dumps(
                    {"error": f"タイムアウト（{EXEC_TIMEOUT}秒）。出力はありませんでした。"},
                    ensure_ascii=False,
                    indent=2,
                )
            )
        sys.exit(1)

    raw_output = result.stdout

    # JSONL解析
    parsed = _parse_jsonl_output(raw_output)
    thread_id = parsed["thread_id"]
    review_text = parsed["review_text"]
    parse_errors = parsed["errors"]

    # JSONL解析失敗時の2段階フォールバック
    if not review_text:
        # Raw出力を保存
        fallback_file = temp_dir / f"{session_id}_codex-review-raw.md"
        fallback_file.write_text(
            f"# Codexレビュー（JSONL解析失敗 - Raw出力）\n\n```\n{raw_output}\n```\n",
            encoding="utf-8",
        )

        stderr_text = result.stderr.strip() if result.stderr else ""

        if thread_id:
            # 準正常系: テキスト抽出失敗だが thread_id は取得済み
            message = (
                "JSONLからレビュー本文を抽出できませんでしたが、スレッドIDは取得済みです。"
                "Raw出力を確認してください。followupは使用可能です。"
            )
            if parse_errors:
                message += f"\nCodexエラー: {'; '.join(parse_errors)}"
            if stderr_text:
                message += f"\nstderr: {stderr_text}"

            print(
                json.dumps(
                    {
                        "status": "fallback",
                        "message": message,
                        "codex_thread_id": thread_id,
                        "raw_file": str(fallback_file),
                        "usage": parsed.get("usage"),
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            # exit 0: followup が使える状態を維持
        else:
            # エラー: thread_id もテキストも取れない
            message = (
                "JSONL解析に失敗し、スレッドIDも取得できませんでした。"
                "Raw出力から手動でthread_idを確認し、codex exec resumeで直接対話してください。"
            )
            if parse_errors:
                message += f"\nCodexエラー: {'; '.join(parse_errors)}"
            if stderr_text:
                message += f"\nstderr: {stderr_text}"

            print(
                json.dumps(
                    {
                        "error": message,
                        "raw_file": str(fallback_file),
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            sys.exit(1)
        return

    # レビュー結果ファイル保存
    review_file = temp_dir / f"{session_id}_codex-review.md"
    review_file.write_text(
        f"# Codexレビュー結果\n\n{review_text}\n",
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "status": "ok",
                "codex_thread_id": thread_id,
                "review_file": str(review_file),
                "usage": parsed["usage"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def followup(codex_session: str, question: str, cwd: str, session_id: str) -> None:
    """追加質問実行（followup）"""
    _check_codex_installed()

    temp_dir = _ensure_temp_dir(cwd)

    # codex exec resume 実行
    cmd = [
        "codex", "--search", "exec", "resume", codex_session,
        "--json",
        question,
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=EXEC_TIMEOUT,
            encoding="utf-8",
        )
    except subprocess.TimeoutExpired:
        print(
            json.dumps(
                {"error": f"タイムアウト（{EXEC_TIMEOUT}秒）"},
                ensure_ascii=False,
                indent=2,
            )
        )
        sys.exit(1)

    raw_output = result.stdout

    # JSONL解析
    parsed = _parse_jsonl_output(raw_output)
    answer_text = parsed["review_text"]

    if not answer_text:
        print(
            json.dumps(
                {
                    "error": "追加質問の回答を取得できませんでした。",
                    "codex_thread_id": codex_session,
                    "raw_output": raw_output[:2000],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        sys.exit(1)

    # 既存レビューファイルに追記
    review_file = temp_dir / f"{session_id}_codex-review.md"

    if review_file.exists():
        existing_content = review_file.read_text(encoding="utf-8")

        # 追加質問の番号を算出
        followup_count = existing_content.count("## 追加質問") + 1

        updated_content = (
            f"{existing_content}\n\n"
            f"## 追加質問 {followup_count}\n\n"
            f"**質問**: {question}\n\n"
            f"**回答**:\n\n{answer_text}\n"
        )
        review_file.write_text(updated_content, encoding="utf-8")
    else:
        # レビューファイルが見つからない場合は新規作成
        review_file.write_text(
            f"# Codexレビュー（追加質問）\n\n"
            f"## 追加質問 1\n\n"
            f"**質問**: {question}\n\n"
            f"**回答**:\n\n{answer_text}\n",
            encoding="utf-8",
        )

    print(
        json.dumps(
            {
                "status": "ok",
                "codex_thread_id": codex_session,
                "review_file": str(review_file),
                "usage": parsed["usage"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Codexレビュー実行スクリプト（Phase 5 オプション）"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # review サブコマンド
    review_parser = subparsers.add_parser("review", help="初回レビュー実行")
    review_parser.add_argument("--plan", required=True, help="プランファイルパス")
    review_parser.add_argument("--cwd", required=True, help="プロジェクトディレクトリ")
    review_parser.add_argument("--session-id", required=True, help="セッションID")

    # followup サブコマンド
    followup_parser = subparsers.add_parser("followup", help="追加質問")
    followup_parser.add_argument(
        "--codex-session", required=True, help="CodexスレッドID"
    )
    followup_parser.add_argument("--question", required=True, help="質問テキスト")
    followup_parser.add_argument("--cwd", required=True, help="プロジェクトディレクトリ")
    followup_parser.add_argument("--session-id", required=True, help="セッションID")

    args = parser.parse_args()

    if args.command == "review":
        review(args.plan, args.cwd, args.session_id)
    elif args.command == "followup":
        followup(args.codex_session, args.question, args.cwd, args.session_id)


if __name__ == "__main__":
    main()
