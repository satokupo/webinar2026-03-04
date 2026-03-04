"""エラー/課題の機械的検出モジュール

セッションの会話内容からエラーパターンを自動検出し、
検出結果を stderr に出力する。

検出対象はセッション中に発生した他のスキル・フロー・ツールのエラーであり、
save-chatlog 自体のエラーではない。
"""

import os
import re
import sys
from datetime import datetime
from typing import List, Tuple


# 検出パターン定義
_ERROR_PATTERNS = [
    {
        'type': 'traceback',
        'pattern': re.compile(r'Traceback \(most recent call last\):', re.IGNORECASE),
    },
    {
        'type': 'exit_code',
        'pattern': re.compile(r'Exit code[:\s]+[1-9]\d*', re.IGNORECASE),
    },
    {
        'type': 'permission_denied',
        'pattern': re.compile(r'Permission to use .+ has been denied', re.IGNORECASE),
    },
    {
        'type': 'permission_denied',
        'pattern': re.compile(r'(?:permission|access)\s+denied', re.IGNORECASE),
    },
    {
        'type': 'error',
        'pattern': re.compile(r'^.*(?:Error|ERROR):\s+.+', re.MULTILINE),
    },
]

# 除外パターン（save-chatlog 自体の処理に関するもの）
_EXCLUDE_PATTERNS = [
    re.compile(r'chatlog_utils\.py'),
    re.compile(r'session_finder\.py'),
    re.compile(r'plan_manager\.py'),
    re.compile(r'error_collector\.py'),
]


def _extract_context(text: str, match_start: int, match_end: int, context_lines: int = 2) -> str:
    """マッチ位置の前後からコンテキスト行を抽出する。"""
    lines = text.split('\n')
    char_count = 0
    match_line_idx = 0

    for i, line in enumerate(lines):
        char_count += len(line) + 1  # +1 for \n
        if char_count > match_start:
            match_line_idx = i
            break

    start_idx = max(0, match_line_idx - context_lines)
    end_idx = min(len(lines), match_line_idx + context_lines + 1)
    return '\n'.join(lines[start_idx:end_idx])


def _is_excluded(match_text: str) -> bool:
    """除外パターンに該当するかチェックする。"""
    for pattern in _EXCLUDE_PATTERNS:
        if pattern.search(match_text):
            return True
    return False


def collect_errors(conversations: List[Tuple[str, str]], session_id: str,
                   start_time: datetime, cwd: str, chatlog_path: str = '') -> list:
    """会話内容からエラーパターンを機械的に検出する。

    Args:
        conversations: [(role, content), ...] 形式の会話リスト（parse_jsonl の出力）
        session_id: セッションID
        start_time: セッション開始時刻（datetime）— ファイル名のタイムスタンプに使用
        cwd: プロジェクトルート — エラーログの保存先パス生成に使用

    Returns:
        検出されたエラーのリスト [{
            'type': 'error' | 'permission_denied' | 'traceback' | 'exit_code',
            'content': エラーメッセージの抜粋,
            'context': 前後の会話コンテキスト（数行）
        }, ...]
    """
    errors = []
    seen_contents = set()  # 重複検出用

    for role, content in conversations:
        # Assistant の発言のみを対象とする（User 発言は偽陽性対策で除外）
        if role != 'Assistant':
            continue

        for pattern_def in _ERROR_PATTERNS:
            for match in pattern_def['pattern'].finditer(content):
                match_text = match.group(0)

                # save-chatlog 自体のエラーは除外
                context_text = _extract_context(content, match.start(), match.end())
                if _is_excluded(context_text):
                    continue

                # 重複を除去（同じエラーメッセージが複数回出現する場合）
                content_key = match_text[:200]  # 先頭200文字で重複判定
                if content_key in seen_contents:
                    continue
                seen_contents.add(content_key)

                errors.append({
                    'type': pattern_def['type'],
                    'content': match_text[:500],  # 長すぎるメッセージは切り詰め
                    'context': context_text[:1000],
                })

    # エラーログ出力先パス生成（常に実行）
    timestamp = start_time.strftime('%Y%m%d-%H%M%S')
    error_log_dir = os.path.join(cwd, '.claude', 'context', 'issues')
    error_log_path = os.path.join(error_log_dir, f'{timestamp}_error-log.md')
    os.makedirs(error_log_dir, exist_ok=True)
    os.makedirs(os.path.join(error_log_dir, 'archive'), exist_ok=True)

    # 常に stderr に基本情報を出力
    print(f"\n=== Error Collection Results ===", file=sys.stderr)
    print(f"Detected {len(errors)} error(s)/issue(s) in session {session_id}", file=sys.stderr)
    if errors:
        print(f"Error log path: {error_log_path}", file=sys.stderr)
    print(f"Chatlog path: {chatlog_path}", file=sys.stderr)
    print(f"", file=sys.stderr)

    if errors:
        for i, err in enumerate(errors, 1):
            print(f"--- [{i}] type={err['type']} ---", file=sys.stderr)
            print(f"{err['content']}", file=sys.stderr)
            print(f"[context]", file=sys.stderr)
            print(f"{err['context']}", file=sys.stderr)
            print(f"", file=sys.stderr)

    print(f"=== End Error Collection ===", file=sys.stderr)

    return errors
