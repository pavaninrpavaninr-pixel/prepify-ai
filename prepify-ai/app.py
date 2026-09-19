"""
Prepify AI - AI Based ML Coding and Interview Platform
Main Flask application: auth, dashboard, coding judge, quiz module,
AI/ML learning module, and Gemini-powered chatbot.
"""
import os
import io
import json
import sqlite3
import contextlib
from datetime import datetime

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, jsonify, flash
)
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")
PROBLEMS_PATH = os.path.join(BASE_DIR, "data", "problems.json")
QUIZZES_PATH = os.path.join(BASE_DIR, "data", "quizzes.json")

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key-change-me")

# Optional Gemini AI setup for the chatbot
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
gemini_model = None
if GEMINI_API_KEY:
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel("gemini-3.6-flash")
    except Exception as e:  # pragma: no cover
        print(f"[Prepify] Gemini AI not initialized: {e}")


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS quiz_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            module_id TEXT NOT NULL,
            score INTEGER NOT NULL,
            total INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS coding_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            problem_id INTEGER NOT NULL,
            result TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            role TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------
def login_required(view):
    def wrapped(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    wrapped.__name__ = view.__name__
    return wrapped


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not username or not password:
            flash("Username and password are required.")
            return redirect(url_for("register"))

        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, generate_password_hash(password)),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            flash("Username already taken.")
            return redirect(url_for("register"))
        finally:
            conn.close()

        flash("Account created. Please log in.")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["username"] = username
            return redirect(url_for("home"))

        flash("Invalid username or password.")
        return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# Core pages
# ---------------------------------------------------------------------------
@app.route("/")
def home():
    if "username" not in session:
        return redirect(url_for("login"))
    return render_template("index.html", username=session["username"])


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", username=session["username"])


@app.route("/aiml")
@login_required
def aiml():
    return render_template("aiml.html")


@app.route("/vapi")
@login_required
def vapi():
    vapi_public_key = os.getenv("VAPI_PUBLIC_KEY", "")
    vapi_assistant_id = os.getenv("VAPI_ASSISTANT_ID", "")
    return render_template(
        "vapi.html",
        vapi_public_key=vapi_public_key,
        vapi_assistant_id=vapi_assistant_id,
    )


# ---------------------------------------------------------------------------
# Coding practice platform
# ---------------------------------------------------------------------------
@app.route("/coding")
@login_required
def coding():
    problems = load_json(PROBLEMS_PATH)
    return render_template("coding.html", problems=problems)


@app.route("/problem/<int:pid>")
@login_required
def problem_page(pid):
    problems = load_json(PROBLEMS_PATH)
    problem = next((p for p in problems if p["id"] == pid), None)
    if not problem:
        return "Problem not found", 404
    return render_template("problem.html", problem=problem)


def _run_user_code(code, function_name, test_input):
    """Executes user code in a restricted namespace and calls function_name."""
    safe_globals = {"__builtins__": __builtins__}
    local_ns = {}
    stdout_capture = io.StringIO()
    try:
        with contextlib.redirect_stdout(stdout_capture):
            exec(code, safe_globals, local_ns)
            fn = local_ns.get(function_name) or safe_globals.get(function_name)
            if fn is None:
                return {"ok": False, "error": f"Function '{function_name}' not defined."}
            result = fn(*test_input) if isinstance(test_input, list) else fn(test_input)
        return {"ok": True, "result": result, "stdout": stdout_capture.getvalue()}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.route("/submit", methods=["POST"])
@login_required
def submit_code():
    data = request.get_json(force=True)
    user_code = data.get("code", "")
    problem_id = int(data.get("problem_id"))

    problems = load_json(PROBLEMS_PATH)
    problem = next((p for p in problems if p["id"] == problem_id), None)
    if not problem:
        return jsonify({"result": "Problem not found"}), 404

    outcome = _run_user_code(user_code, problem["function_name"], problem["test_input"])

    if not outcome["ok"]:
        verdict = {"status": "Error", "detail": outcome["error"]}
    elif outcome["result"] == problem["expected_output"]:
        verdict = {"status": "Correct Solution", "output": outcome["result"]}
    else:
        verdict = {
            "status": "Wrong Output",
            "expected": problem["expected_output"],
            "actual": outcome["result"],
        }

    conn = get_db()
    conn.execute(
        "INSERT INTO coding_submissions (username, problem_id, result) VALUES (?, ?, ?)",
        (session["username"], problem_id, verdict["status"]),
    )
    conn.commit()
    conn.close()

    return jsonify(verdict)


# ---------------------------------------------------------------------------
# Quiz module
# ---------------------------------------------------------------------------
@app.route("/quiz")
@login_required
def quiz_page():
    return render_template("quiz.html")


@app.route("/api/quizzes")
@login_required
def api_quizzes():
    return jsonify(load_json(QUIZZES_PATH))


@app.route("/api/quiz/submit", methods=["POST"])
@login_required
def api_quiz_submit():
    data = request.get_json(force=True)
    module_id = data.get("module_id")
    answers = data.get("answers", {})

    quizzes = load_json(QUIZZES_PATH)
    module = next((q for q in quizzes if q["module_id"] == module_id), None)
    if not module:
        return jsonify({"error": "Quiz module not found"}), 404

    score = 0
    for q in module["questions"]:
        qid = str(q["id"])
        if qid in answers and answers[qid] == q["answer"]:
            score += 1
    total = len(module["questions"])

    conn = get_db()
    conn.execute(
        "INSERT INTO quiz_scores (username, module_id, score, total) VALUES (?, ?, ?, ?)",
        (session["username"], module_id, score, total),
    )
    conn.commit()
    conn.close()

    return jsonify({"score": score, "total": total})


# ---------------------------------------------------------------------------
# Progress / dashboard API
# ---------------------------------------------------------------------------
@app.route("/api/progress")
@login_required
def api_progress():
    conn = get_db()
    quiz_rows = conn.execute(
        "SELECT module_id, score, total, created_at FROM quiz_scores "
        "WHERE username = ? ORDER BY created_at DESC",
        (session["username"],),
    ).fetchall()
    coding_rows = conn.execute(
        "SELECT result, COUNT(*) as count FROM coding_submissions "
        "WHERE username = ? GROUP BY result",
        (session["username"],),
    ).fetchall()
    conn.close()

    quizzes = [dict(row) for row in quiz_rows]
    coding_summary = {row["result"]: row["count"] for row in coding_rows}

    # Aggregate a simple per-module percentage for the dashboard bars
    best_by_module = {}
    for q in quizzes:
        pct = round((q["score"] / q["total"]) * 100) if q["total"] else 0
        if q["module_id"] not in best_by_module or pct > best_by_module[q["module_id"]]:
            best_by_module[q["module_id"]] = pct

    return jsonify({
        "username": session["username"],
        "quizzes": quizzes,
        "module_progress": best_by_module,
        "coding_summary": coding_summary,
    })


# ---------------------------------------------------------------------------
# AI Chatbot (Gemini) - simple JSON API used by the floating chat widget
# ---------------------------------------------------------------------------
@app.route("/api/chat", methods=["POST"])
@login_required
def api_chat():
    data = request.get_json(force=True)
    user_message = data.get("message", "").strip()
    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    conn = get_db()
    conn.execute(
        "INSERT INTO chat_history (username, role, message) VALUES (?, 'user', ?)",
        (session["username"], user_message),
    )

    if gemini_model:
        try:
            response = gemini_model.generate_content(user_message)
            reply = response.text
        except Exception as e:
            reply = f"(AI error: {e}) Please check your GEMINI_API_KEY in .env"
    else:
        reply = (
            "Gemini API key not configured. Add GEMINI_API_KEY to your .env file "
            "to enable real AI responses."
        )

    conn.execute(
        "INSERT INTO chat_history (username, role, message) VALUES (?, 'assistant', ?)",
        (session["username"], reply),
    )
    conn.commit()
    conn.close()

    return jsonify({"reply": reply})


if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        init_db()
    else:
        init_db()  # safe: CREATE TABLE IF NOT EXISTS
    app.run(debug=True, port=5000)
