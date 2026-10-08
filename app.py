"""Student Management System - Flask + SQLite REST API."""
import re
import sqlite3
from pathlib import Path
from flask import Flask, jsonify, request, g

BASE = Path(__file__).parent
app = Flask(__name__, static_folder="static", static_url_path="")
app.config["DATABASE"] = str(BASE / "students.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS students (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    name     TEXT    NOT NULL,
    roll_no  TEXT    NOT NULL UNIQUE,
    class    TEXT    NOT NULL,
    marks    REAL    NOT NULL CHECK (marks BETWEEN 0 AND 100),
    contact  TEXT    NOT NULL
);
"""


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_):
    db = g.pop("db", None)
    if db:
        db.close()


def init_db():
    with sqlite3.connect(app.config["DATABASE"]) as db:
        db.executescript(SCHEMA)


def validate(data):
    """Return (clean_dict, errors_dict)."""
    errors, clean = {}, {}
    name = str(data.get("name", "")).strip()
    roll = str(data.get("roll_no", "")).strip()
    cls = str(data.get("class", "")).strip()
    contact = str(data.get("contact", "")).strip()

    if len(name) < 2 or not re.fullmatch(r"[A-Za-z .'-]+", name):
        errors["name"] = "Enter a name using letters only (at least 2)."
    if not re.fullmatch(r"[A-Za-z0-9-]{1,20}", roll):
        errors["roll_no"] = "Roll number must be 1-20 letters, digits or hyphens."
    if not cls:
        errors["class"] = "Class is required."
    if not re.fullmatch(r"[6-9]\d{9}", contact):
        errors["contact"] = "Enter a valid 10-digit mobile number."
    try:
        marks = float(data.get("marks"))
        if not 0 <= marks <= 100:
            raise ValueError
    except (TypeError, ValueError):
        errors["marks"] = "Marks must be a number from 0 to 100."
        marks = None

    clean.update(name=name, roll_no=roll.upper(), cls=cls, marks=marks, contact=contact)
    return clean, errors


def row(r):
    return {k: r[k] for k in r.keys()}


@app.get("/")
def index():
    return app.send_static_file("index.html")


@app.get("/api/students")
def list_students():
    q = request.args.get("q", "").strip()
    sql, args = "SELECT * FROM students", []
    if q:
        sql += " WHERE name LIKE ? OR roll_no LIKE ?"
        args = [f"%{q}%", f"%{q}%"]
    sql += " ORDER BY id DESC"
    return jsonify([row(r) for r in get_db().execute(sql, args)])


@app.get("/api/students/<int:sid>")
def get_student(sid):
    r = get_db().execute("SELECT * FROM students WHERE id=?", (sid,)).fetchone()
    if not r:
        return jsonify(error="Student not found."), 404
    return jsonify(row(r))


@app.post("/api/students")
def add_student():
    clean, errors = validate(request.get_json(silent=True) or {})
    if errors:
        return jsonify(error="Validation failed.", fields=errors), 400
    db = get_db()
    try:
        cur = db.execute(
            "INSERT INTO students (name, roll_no, class, marks, contact) VALUES (?,?,?,?,?)",
            (clean["name"], clean["roll_no"], clean["cls"], clean["marks"], clean["contact"]),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify(error="Validation failed.",
                       fields={"roll_no": "This roll number already exists."}), 409
    return get_student(cur.lastrowid).get_json(), 201


@app.put("/api/students/<int:sid>")
def update_student(sid):
    db = get_db()
    if not db.execute("SELECT 1 FROM students WHERE id=?", (sid,)).fetchone():
        return jsonify(error="Student not found."), 404
    clean, errors = validate(request.get_json(silent=True) or {})
    if errors:
        return jsonify(error="Validation failed.", fields=errors), 400
    try:
        db.execute(
            "UPDATE students SET name=?, roll_no=?, class=?, marks=?, contact=? WHERE id=?",
            (clean["name"], clean["roll_no"], clean["cls"], clean["marks"], clean["contact"], sid),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify(error="Validation failed.",
                       fields={"roll_no": "This roll number already exists."}), 409
    return get_student(sid)


@app.delete("/api/students/<int:sid>")
def delete_student(sid):
    db = get_db()
    cur = db.execute("DELETE FROM students WHERE id=?", (sid,))
    db.commit()
    if cur.rowcount == 0:
        return jsonify(error="Student not found."), 404
    return jsonify(message="Student deleted.")


init_db()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
