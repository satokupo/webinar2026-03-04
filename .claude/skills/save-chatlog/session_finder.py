"""JSONL セッション管理モジュール

プロジェクトの JSONL ファイルの検索・パース・セッション管理を担当する。
"""

import glob
import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple


def get_all_jsonl_files() -> List[Tuple[str, float]]:
    """全JSONLファイルを更新日時降順（最新が先）で返す。"""
    projects_dir = os.path.expanduser('~/.claude/projects/')
    jsonl_files = glob.glob(os.path.join(projects_dir, "*", "*.jsonl"))
    if not jsonl_files:
        raise FileNotFoundError(f"No .jsonl files found in {projects_dir}")

    files_with_mtime = [(f, os.path.getmtime(f)) for f in jsonl_files]
    files_with_mtime.sort(key=lambda x: x[1], reverse=True)
    return files_with_mtime


def parse_jsonl(jsonl_path: str) -> Dict:
    """JSONLファイルを解析する。

    Args:
        jsonl_path: JSONLファイルの絶対パス

    Returns:
        {
            'session_id': str,
            'start_time': datetime,
            'conversations': [(role, content), ...],
            'plan_files': [str, ...]
        }
    """
    conversations = []
    # session_idはファイル名から取得（JSONL内には複数のIDが混在する可能性があるため）
    session_id = os.path.basename(jsonl_path).replace('.jsonl', '')
    start_time = None
    plan_files = []

    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data = json.loads(line)

                # file-history-snapshotからタイムスタンプを取得
                if data.get('type') == 'file-history-snapshot' and start_time is None:
                    snapshot = data.get('snapshot', {})
                    ts = snapshot.get('timestamp')
                    if ts:
                        start_time = datetime.fromisoformat(ts.replace('Z', '+00:00'))

                # 会話内容を抽出
                if data.get('type') == 'user' and 'message' in data:
                    content = data['message'].get('content', '')
                    if isinstance(content, str) and content.strip():
                        conversations.append(('User', content))
                elif data.get('type') == 'assistant' and 'message' in data:
                    content = data['message'].get('content', '')
                    if isinstance(content, list):
                        text_parts = [c.get('text', '') for c in content if c.get('type') == 'text']
                        content = '\n'.join(text_parts)
                        # プランファイルの検出（Write と Read の両方）
                        for item in data['message'].get('content', []):
                            if item.get('type') == 'tool_use' and item.get('name') in ('Write', 'Read'):
                                file_path = item.get('input', {}).get('file_path', '')
                                if '.claude/plans/' in file_path:
                                    plan_files.append(file_path)
                    if isinstance(content, str) and content.strip():
                        conversations.append(('Assistant', content))
            except json.JSONDecodeError:
                pass

    # start_timeが取得できなかった場合はファイルの作成日時を使用
    if start_time is None:
        file_stat = os.stat(jsonl_path)
        start_time = datetime.fromtimestamp(file_stat.st_ctime)

    # ローカル時間に変換（UTCの場合）
    if start_time.tzinfo is not None:
        start_time = start_time.astimezone().replace(tzinfo=None)

    return {
        'session_id': session_id or 'unknown',
        'start_time': start_time,
        'conversations': conversations,
        'plan_files': list(set(plan_files))  # 重複除去
    }


def find_jsonl_path(offset: int = 0) -> str:
    """N個前のセッションのJSONLファイルパスを返す。"""
    files_with_mtime = get_all_jsonl_files()

    if offset >= len(files_with_mtime):
        raise IndexError(f"offset {offset} is out of range (max: {len(files_with_mtime) - 1})")

    return files_with_mtime[offset][0]


def find_jsonl_path_by_grep(grep_pattern: str) -> str:
    """grepパターンでJSONLファイルを特定してパスを返す。"""
    projects_dir = os.path.expanduser('~/.claude/projects/')
    jsonl_files = glob.glob(os.path.join(projects_dir, "*", "*.jsonl"))

    matched_files = []
    for jsonl_path in jsonl_files:
        try:
            with open(jsonl_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if grep_pattern in content:
                    matched_files.append((jsonl_path, os.path.getmtime(jsonl_path)))
        except Exception:
            pass

    if not matched_files:
        raise FileNotFoundError(f"No session found matching: {grep_pattern[:50]}...")

    matched_files.sort(key=lambda x: x[1], reverse=True)
    return matched_files[0][0]


def find_jsonl_path_by_session_id(session_id: str) -> str:
    """セッションIDからJSONLパスを返す。

    ~/.claude/projects/ 配下を横断検索し、session_id に一致する
    JSONL ファイルを直接特定する。UUID の一意性により
    プロジェクトディレクトリの特定は不要。

    Args:
        session_id: セッションID（UUID形式）

    Returns:
        JSONLファイルパス
    """
    projects_dir = os.path.expanduser('~/.claude/projects/')
    matches = glob.glob(f"{projects_dir}*/{session_id}.jsonl")
    if not matches:
        raise FileNotFoundError(f"Session not found: {session_id}")
    if len(matches) > 1:
        # ディレクトリコピー等で重複がある場合は mtime 最新を返す
        matches.sort(key=os.path.getmtime, reverse=True)
    return matches[0]


def find_jsonl_paths_range(offset: int, merge_until: int) -> List[str]:
    """offsetからmerge_untilまでの範囲のJSONLファイルパスを返す。"""
    files_with_mtime = get_all_jsonl_files()

    if merge_until >= len(files_with_mtime):
        raise IndexError(f"merge_until {merge_until} is out of range (max: {len(files_with_mtime) - 1})")

    selected = files_with_mtime[offset:merge_until + 1]
    selected.sort(key=lambda x: x[1])
    return [f[0] for f in selected]


def get_saved_session_ids(cwd: str) -> Set[str]:
    """_chatlog/ 内の保存済みsession_idを収集する。

    Args:
        cwd: 作業ディレクトリの絶対パス

    Returns:
        session_idのセット
    """
    chatlog_dir = os.path.join(cwd, '_chatlog')
    if not os.path.isdir(chatlog_dir):
        return set()

    saved_ids = set()
    # 再帰的にマークダウンファイルを検索
    for root, dirs, files in os.walk(chatlog_dir):
        for f in files:
            if f.endswith('.md'):
                filepath = os.path.join(root, f)
                try:
                    with open(filepath, 'r', encoding='utf-8') as file:
                        content = file.read(2000)  # 先頭のみ読む
                        # session_id: 形式（単一セッション）
                        match = re.search(r'^session_id:\s*([a-f0-9-]{36})', content, re.MULTILINE)
                        if match:
                            saved_ids.add(match.group(1))
                        # session_ids: 形式（マージされたセッション）
                        ids_match = re.findall(r'^\s+-\s*([a-f0-9-]{36})', content, re.MULTILINE)
                        for sid in ids_match:
                            saved_ids.add(sid)
                except Exception:
                    pass

    return saved_ids
