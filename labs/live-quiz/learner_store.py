"""Personal practice identity, separate from teacher accounts and graded records."""
import base64
import hashlib
import hmac
import os
from pathlib import Path
import re
import secrets
import sqlite3
import time
from contextlib import contextmanager


@contextmanager
def connection():
    path = os.environ.get('LEARNER_DB_PATH', str(Path(os.environ.get('DB_PATH', '/data/live-quiz.db')).with_name('learners.db')))
    conn = sqlite3.connect(path, timeout=5)
    conn.row_factory = sqlite3.Row
    conn.executescript('''
      CREATE TABLE IF NOT EXISTS learners (
        id TEXT PRIMARY KEY, student_id TEXT NOT NULL UNIQUE, name TEXT NOT NULL,
        password_hash TEXT NOT NULL, slot INTEGER NOT NULL UNIQUE,
        vpn_ip TEXT NOT NULL UNIQUE, active INTEGER NOT NULL DEFAULT 1);
      CREATE TABLE IF NOT EXISTS learner_limits (
        bucket TEXT PRIMARY KEY, started INTEGER NOT NULL, count INTEGER NOT NULL);
      CREATE TABLE IF NOT EXISTS learner_progress (
        learner_id TEXT NOT NULL, week INTEGER NOT NULL, checkpoint TEXT NOT NULL,
        value INTEGER NOT NULL, PRIMARY KEY(learner_id,week,checkpoint));
    ''')
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def password_hash(password, salt=None):
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 400000)
    return base64.b64encode(salt + digest).decode()


def password_ok(password, stored):
    if not isinstance(password, str) or not 12 <= len(password) <= 128:
        return False
    try:
        raw = base64.b64decode(stored, validate=True)
        return len(raw) == 48 and hmac.compare_digest(password_hash(password, raw[:16]), stored)
    except (ValueError, TypeError):
        return False


def get(learner_id):
    with connection() as conn:
        row = conn.execute('SELECT * FROM learners WHERE id=? AND active=1', (learner_id,)).fetchone()
        return dict(row) if row else None


def authenticate(student_id, password):
    with connection() as conn:
        row = conn.execute('SELECT * FROM learners WHERE student_id=? AND active=1', (student_id,)).fetchone()
    # Do equivalent password work for valid-length credentials on unknown accounts.
    dummy = base64.b64encode(b'\0' * 48).decode()
    ok = password_ok(password, row['password_hash'] if row else dummy)
    return dict(row) if row and ok else None


def admit(bucket, limit, period):
    now = int(time.time())
    with connection() as conn:
        conn.execute('BEGIN IMMEDIATE')
        row = conn.execute('SELECT * FROM learner_limits WHERE bucket=?', (bucket,)).fetchone()
        if row and now - row['started'] < period:
            if row['count'] >= limit:
                return False
            conn.execute('UPDATE learner_limits SET count=count+1 WHERE bucket=?', (bucket,))
        else:
            conn.execute('INSERT OR REPLACE INTO learner_limits VALUES (?, ?, 1)', (bucket, now))
        conn.execute('DELETE FROM learner_limits WHERE started < ?', (now - 86400,))
    return True


def enroll(student_id, name, slot, vpn_ip, password):
    import ipaddress
    if not re.fullmatch(r'[0-9]{6,16}', student_id):
        raise ValueError('A real numeric student ID of 6–16 digits is required.')
    if not isinstance(name, str) or not 1 <= len(name) <= 100 or not 1 <= slot <= 5:
        raise ValueError('Invalid name or slot.')
    if ipaddress.ip_address(vpn_ip).version != 4 or not 12 <= len(password) <= 128:
        raise ValueError('IPv4 and a password of 12–128 characters are required.')
    learner_id = secrets.token_hex(16)
    with connection() as conn:
        conn.execute('INSERT INTO learners VALUES (?, ?, ?, ?, ?, ?, 1)',
                     (learner_id, student_id, name, password_hash(password), slot, vpn_ip))
    return learner_id


def progress(learner_id, week=None, checkpoint=None, value=None):
    with connection() as conn:
        if checkpoint is not None:
            if type(week) is not int or not 1 <= week <= 19 or checkpoint not in ('explain','practice','defend') or type(value) is not bool:
                raise ValueError('invalid progress')
            conn.execute('INSERT OR REPLACE INTO learner_progress VALUES (?,?,?,?)',
                         (learner_id,week,checkpoint,int(value)))
        rows=conn.execute('SELECT week,checkpoint,value FROM learner_progress WHERE learner_id=?',(learner_id,)).fetchall()
        return [{'week':r['week'],'checkpoint':r['checkpoint'],'value':bool(r['value'])} for r in rows]
