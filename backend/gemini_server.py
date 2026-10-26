#!/usr/bin/env python3
"""Khusela AI proxy using the Google Gemini API.
The API key stays on this server. It is never put in the web page.
Setup:  pip install flask
        export GEMINI_API_KEY="your-key"        (Windows: set GEMINI_API_KEY=your-key)
        python gemini_server.py
Then in the page set  CFG.askUrl = "https://your-domain/api/ask"
"""
import os, json, time, urllib.request, urllib.error
try:
    from dotenv import load_dotenv   # reads backend/.env when running locally
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
except ImportError:
    pass
from flask import Flask, request, jsonify

MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")  # check the current model name in Google AI Studio
KEY = os.environ.get("GEMINI_API_KEY", "")
ALLOWED_ORIGIN = os.environ.get("ALLOWED_ORIGIN", "*")       # set to your site, e.g. https://khusela.example
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
HITS = {}                                                    # simple per-IP limit: 10 questions / 10 min

app = Flask(__name__)

def system_prompt(d):
    return (f"You are Khusela, a calm support guide for survivors of gender-based violence and people helping them in "
            f"{d.get('country','Southern Africa')}. Rules: plain, kind, no blame, under 170 words. Put safety first. "
            f"If danger is immediate, tell them to call {d.get('emergency','the emergency number')} and use Quick exit if unsafe. "
            f"Helplines: {d.get('helplines','')}. For sexual assault mention medical care within 72 hours. "
            f"Do not advise confronting the abuser. Give general information, not legal verdicts. "
            f"Refuse to help find, track or harm anyone. Reply in {d.get('lang','English')}.")

def limited(ip):
    now = time.time()
    HITS[ip] = [t for t in HITS.get(ip, []) if now - t < 600]
    if len(HITS[ip]) >= 10:
        return True
    HITS[ip].append(now)
    return False

@app.after_request
def cors(r):
    r.headers["Access-Control-Allow-Origin"] = ALLOWED_ORIGIN
    r.headers["Access-Control-Allow-Headers"] = "content-type,x-agent-token"
    r.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,PATCH,OPTIONS"
    return r

@app.route("/api/ask", methods=["POST", "OPTIONS"])
def ask():
    if request.method == "OPTIONS":
        return "", 204
    d = request.get_json(silent=True) or {}
    q = str(d.get("q", ""))[:800].strip()
    if not q or not KEY:
        return jsonify(text="The helper is not available. See Get help."), 200
    if limited(request.remote_addr):
        return jsonify(text="Too many questions. Please wait a few minutes."), 429
    body = {"systemInstruction": {"parts": [{"text": system_prompt(d)}]},
            "contents": [{"role": "user", "parts": [{"text": q}]}],
            "generationConfig": {"maxOutputTokens": 600, "temperature": 0.4}}
    req = urllib.request.Request(URL, json.dumps(body).encode(),
                                 {"content-type": "application/json", "x-goog-api-key": KEY})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            j = json.load(r)
        text = j["candidates"][0]["content"]["parts"][0]["text"]
    except (urllib.error.URLError, KeyError, IndexError, ValueError):
        text = (f"I could not answer that. If you are in danger call {d.get('emergency','the emergency number')}. "
                f"Helplines: {d.get('helplines','')}.")
    return jsonify(text=text)       # nothing is logged or stored

if __name__ == "__main__":
    app.run(port=3000)
