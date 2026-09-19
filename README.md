# Prepify AI — AI Based ML Coding and Interview Platform

A unified web platform for learning AI/ML concepts, practicing coding problems,
taking quizzes, chatting with an AI assistant (Gemini), and running AI-driven
mock voice interviews (Vapi) — built with Flask + SQLite.

> Based on the Major Project Phase II report — Dept. of AIML, MVJCE (2025–26).

## Features
- 🔐 User registration/login (session-based)
- 📊 Dashboard with quiz & coding progress
- 📘 AI/ML learning module (structured notes)
- 💻 Coding practice platform with an in-browser judge
- 📝 Quiz module with instant grading
- 🤖 AI chatbot powered by Google Gemini
- 🎙️ AI voice interview page (Vapi Web SDK)

## Project Structure
```
prepify-ai/
├── app.py                # Main Flask app (routes, auth, judge, chatbot)
├── init_db.py             # One-time DB setup script
├── requirements.txt
├── .env.example            # Copy to .env and fill in your keys
├── data/
│   ├── problems.json       # Coding practice problems
│   └── quizzes.json        # Quiz questions
├── templates/              # Jinja2 HTML templates
└── static/
    ├── css/style.css
    └── js/chat.js
```

## Setup (VS Code)

1. **Open the folder** in VS Code.

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   Then open `.env` and add your `GEMINI_API_KEY` (get one at
   https://aistudio.google.com/app/apikey). The `VAPI_*` keys are optional —
   the interview page will still load without them, just without live voice AI.

5. **Initialize the database**
   ```bash
   python init_db.py
   ```

6. **Run the app**
   ```bash
   python app.py
   ```
   Visit **http://127.0.0.1:5000** and register a new account.

## Pushing to GitHub

```bash
cd prepify-ai
git init
git add .
git commit -m "Initial commit: Prepify AI platform"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

`.env` and `database.db` are already excluded via `.gitignore`, so your API
keys and local data won't be pushed.

## Notes
- The coding judge runs submitted code with Python's `exec()` in a
  restricted namespace — this is for learning/demo purposes only and is
  **not a hardened sandbox**; don't expose it on the public internet as-is.
- Team: Amrutha Sindu M, P J Rakshitha, Pavani N R, Rekhashree N
- Guide: Ms. Suruthi S, Dept. of AIML, MVJCE

## Future Scope
Multilingual chatbot support, resume analysis, company-specific mock
interviews, facial/body-language analysis, gamified learning, and mobile
app — see the full project report for details.
