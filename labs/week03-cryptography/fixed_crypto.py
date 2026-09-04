"""
Week 3 — remediated crypto (wk03 branch). Companion to solution_skeleton.py with the
rehash-on-login migration (Task 6). All four misuses closed.
"""
import os, secrets
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from Crypto.Cipher import AES

ph = PasswordHasher()

def store_password(pw: str) -> str:                 # CWE-916/327 -> argon2id, auto-salted
    return ph.hash(pw)

def verify_password(stored: str, pw: str) -> bool:
    try:
        return ph.verify(stored, pw)
    except VerifyMismatchError:
        return False

def needs_rehash(stored: str) -> bool:              # Task 6: upgrade legacy records on login
    return ph.check_needs_rehash(stored)

def encrypt_gcm(data: bytes) -> tuple[bytes, bytes, bytes]:   # CWE-327 -> AES-GCM (AEAD)
    key = bytes.fromhex(os.environ["ENC_KEY_HEX"])           # CWE-798 -> key from env
    nonce = os.urandom(12)
    ct, tag = AES.new(key, AES.MODE_GCM, nonce=nonce).encrypt_and_digest(data)
    return nonce, ct, tag

def reset_token() -> str:                            # CWE-330 -> CSPRNG
    return secrets.token_urlsafe(16)
