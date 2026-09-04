"""
Week 2 — remediated version (wk02 branch). Each planted flaw fixed and mapped to its CWE.
Secrets now come from the environment; run with them set (see CI secrets).
"""
import os, sqlite3, subprocess, re
from flask import Flask, request
from argon2 import PasswordHasher

app = Flask(__name__)
ph = PasswordHasher()

# CWE-798 fix: secrets from environment, never hardcoded/committed.
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")

@app.route("/user")
def user():
    name = request.args.get("name", "")
    con = sqlite3.connect("app.db")
    # CWE-89 fix: parameterized query — input is data, never SQL.
    return str(con.execute("SELECT * FROM users WHERE name = ?", (name,)).fetchall())

@app.route("/ping")
def ping():
    host = request.args.get("host", "127.0.0.1")
    # CWE-78 fix: no shell; argument list + validate host.
    if not re.fullmatch(r"[A-Za-z0-9._-]{1,253}", host):
        return "invalid host", 400
    return subprocess.check_output(["ping", "-c", "1", host])

def store_password(pw):
    # CWE-327 fix: argon2id (salted, tunable work factor).
    return ph.hash(pw)

if __name__ == "__main__":
    app.run(debug=False)  # CWE-489 fix: debug off
