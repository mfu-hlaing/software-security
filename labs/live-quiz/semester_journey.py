"""Read-only semester learning content. No identities, grading or arbitrary execution."""
from __future__ import annotations
import copy
import json
import os
from pathlib import Path
from urllib.parse import urlsplit

WEEKS = tuple(json.loads(Path(__file__).with_name('semester_content.json').read_text()))

def week(number):
    return copy.deepcopy(next((w for w in WEEKS if w['number'] == number), None))

def lab_url(number, variant):
    # Operator-managed launch links. Missing links never invent a live target.
    if number not in (10, 14, 15) or variant not in ('vulnerable', 'defended'):
        return None
    raw = os.environ.get(f'SEMESTER_WEEK{number:02}_{variant.upper()}_URL', '').strip()
    if not raw or any(ord(c) < 33 or ord(c) == 127 for c in raw) or '\\' in raw:
        return None
    try:
        url = urlsplit(raw)
        if url.scheme != 'https' or not url.hostname or url.username or url.password:
            return None
        _ = url.port
    except ValueError:
        return None
    return raw
