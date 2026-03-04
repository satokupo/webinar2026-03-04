#!/usr/bin/env python3
"""
current-session-id: マーカー生成スクリプト

ユニークなマーカー文字列を生成して stdout に出力する。
このマーカーは Claude の tool_result として JSONL に記録され、
find.py でのセッション特定に使用される。
"""

import uuid

marker = f"__CSID_MARKER_{uuid.uuid4()}__"
print(marker)
