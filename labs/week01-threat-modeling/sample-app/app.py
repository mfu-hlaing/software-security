"""
Tiny sample web app for Week 1 threat modeling.
You will NOT exploit this in Week 1 — you will draw a data-flow diagram
and apply STRIDE to its components (web client, app, SQLite DB, /upload).
"""
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import sqlite3, os, uuid

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
DB = "notes.db"
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def init_db():
    con = sqlite3.connect(DB)
    con.execute("CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY, owner TEXT, body TEXT)")
    con.commit(); con.close()

@app.route("/notes", methods=["GET", "POST"])
def notes():
    con = sqlite3.connect(DB)
    if request.method == "POST":
        owner = request.json.get("owner", "anon")
        body = request.json.get("body", "")
        con.execute("INSERT INTO notes (owner, body) VALUES (?, ?)", (owner, body))
        con.commit()
    rows = con.execute("SELECT id, owner, body FROM notes").fetchall()
    con.close()
    return jsonify(rows)

@app.route("/upload", methods=["POST"])
def upload():
    f = request.files.get("file")
    if f is None or not f.filename:
        return {"error": "a named file is required"}, 400
    raw = f.filename
    if any(c in raw for c in ("/", "\\", "\x00")):
        return {"error": "path components are not allowed"}, 400
    safe = secure_filename(raw)
    extension = safe.rsplit(".", 1)[-1].lower() if "." in safe else ""
    if extension not in {"txt", "png", "jpg", "jpeg", "pdf"}:
        return {"error": "unsupported file type"}, 400
    # Only server-generated identifiers and fixed allowlisted suffixes form paths.
    name = uuid.uuid4().hex + "." + extension
    with open(os.path.join(UPLOAD_DIR, name), "xb") as output:
        f.save(output)
    return {"saved": name}

@app.route("/files/<name>")
def files(name):
    response = send_from_directory(UPLOAD_DIR, name, as_attachment=True)
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
