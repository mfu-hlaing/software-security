"""
Week 2 — remediated version (wk02 branch). Each planted flaw fixed and mapped to its CWE.
Secrets now come from the environment; run with them set (see CI secrets).
"""
import os, sqlite3, subprocess
from ipaddress import ip_address
from flask import Flask, request
from argon2 import PasswordHasher

app = Flask(__name__)
ph = PasswordHasher()

# CWE-798 fix: secrets from environment, never hardcoded/committed.
AWS_SECRET_ACCESS_KEY = os.environ["AWS_SECRET_ACCESS_KEY"]
DB_PASSWORD = os.environ["DB_PASSWORD"]

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
    try:
        address = ip_address(host)
    except ValueError:
        return "invalid IP address", 400
    if not address.is_loopback:
        return "only loopback lab destinations are allowed", 400
    try:
        return subprocess.check_output(["ping", "-c", "1", str(address)], timeout=3)
    except (subprocess.SubprocessError, OSError):
        return "ping failed", 502

def store_password(pw):
    # CWE-327 fix: argon2id (salted, tunable work factor).
    return ph.hash(pw)

if __name__ == "__main__":
    app.run(debug=False)  # CWE-489 fix: debug off
