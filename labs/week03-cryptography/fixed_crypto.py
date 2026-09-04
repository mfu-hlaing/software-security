"""Week 3 defenses, prepared with disclosed Codex assistance."""
import hashlib
import hmac
import os
import re
import secrets
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from Crypto.Cipher import AES

ph = PasswordHasher()

def store_password(pw: str) -> str:
    return ph.hash(pw)

def verify_password(stored: str, pw: str) -> bool:
    try:
        return ph.verify(stored, pw)
    except (InvalidHashError, VerificationError):
        return False

def verify_and_upgrade(stored: str, pw: str) -> tuple[bool, str]:
    """Caller must persist the returned hash atomically after successful login.

    Legacy MD5 support is migration-only, never used for new password records.
    """
    if re.fullmatch(r'[0-9a-fA-F]{32}', stored):
        matched = hmac.compare_digest(stored.lower(), hashlib.md5(pw.encode()).hexdigest())
        return (True, store_password(pw)) if matched else (False, stored)
    if not verify_password(stored, pw):
        return False, stored
    return True, store_password(pw) if ph.check_needs_rehash(stored) else stored

def encryption_key() -> bytes:
    key = bytes.fromhex(os.environ['ENC_KEY_HEX'])
    if len(key) not in (16, 24, 32):
        raise ValueError('ENC_KEY_HEX must encode 16, 24, or 32 bytes')
    return key

def encrypt_gcm(data: bytes) -> tuple[bytes, bytes, bytes]:
    nonce = os.urandom(12)
    ct, tag = AES.new(encryption_key(), AES.MODE_GCM, nonce=nonce).encrypt_and_digest(data)
    return nonce, ct, tag

def decrypt_gcm(nonce: bytes, ciphertext: bytes, tag: bytes) -> bytes:
    return AES.new(encryption_key(), AES.MODE_GCM, nonce=nonce).decrypt_and_verify(ciphertext, tag)

def reset_token() -> str:
    return secrets.token_urlsafe(16)

if __name__ == '__main__':
    stored = store_password('lab-example')
    print('argon2id verified:', stored.startswith('$argon2id$') and verify_password(stored, 'lab-example'))
    record = encrypt_gcm(b'lab message')
    print('GCM round trip:', decrypt_gcm(*record) == b'lab message')
    print('CSPRNG token length:', len(reset_token()))
