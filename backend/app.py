"""Khusela backend: AI proxy (Gemini), case/status/application API, USSD. Run: gunicorn app:app"""
import os, re, json, sqlite3, time
from flask import request, jsonify
from gemini_server import app, limited
import ussd_server as u

DBP = os.environ.get("DB_PATH", "khusela.db")
AT = os.environ.get("AGENT_TOKEN", "")
ID = {"cases": re.compile(r"^KH-[A-Z0-9]{4,8}$"), "applications": re.compile(r"^APP-[A-Z0-9]{4,8}$"), "status": re.compile(r"^KH-[A-Z0-9]{4,8}$")}

def db():
    c = sqlite3.connect(DBP)
    c.execute("create table if not exists docs(col text, id text, j text, primary key(col,id))")
    return c

def agent():
    return bool(AT) and request.headers.get("x-agent-token", "") == AT

@app.get("/health")
def health():
    return "ok"

@app.route("/api/doc/<col>/<id>", methods=["GET", "PUT", "PATCH"])
def doc(col, id):
    if col not in ID or not ID[col].match(id):
        return "", 404
    c = db()
    row = c.execute("select j from docs where col=? and id=?", (col, id)).fetchone()
    if request.method == "GET":
        if col != "status" and not agent():
            return "", 401          # survivors can only read status, never case text
        return (jsonify(json.loads(row[0])) if row else ("", 404))
    d = request.get_json(silent=True) or {}
    if len(json.dumps(d)) > 8000:
        return "", 413
    if request.method == "PUT":
        if col == "status" and not agent():
            return "", 401
        if col != "status" and not agent():      # public create-only
            if row or limited(request.remote_addr):
                return "", 403
            d["status"] = "Received" if col == "cases" else "Applied"
            d["log"] = [{"t": int(time.time() * 1000), "by": "System", "m": "Report received"}] if col == "cases" else []
    else:
        if not agent() or not row:
            return "", 401
        d = {**json.loads(row[0]), **d}
    c.execute("insert or replace into docs values(?,?,?)", (col, id, json.dumps(d)))
    c.commit()
    return jsonify(d)

@app.get("/api/col/<col>")
def col(col):
    if col not in ("cases", "applications") or not agent():
        return "", 401
    rows = [json.loads(r[0]) for r in db().execute("select j from docs where col=?", (col,))]
    return jsonify(sorted(rows, key=lambda x: -x.get("t", 0))[:100])

def ussd_case(phone, lang, msg):
    r = u.ref()
    d = {"ref": r, "channel": "ussd", "lang": lang, "summary": msg, "urgency": "High", "status": "Received",
         "contact": phone.lstrip("+"), "country": "Unknown", "t": int(time.time() * 1000),
         "log": [{"t": int(time.time() * 1000), "by": "System", "m": "Report received by USSD"}]}
    c = db(); c.execute("insert or replace into docs values(?,?,?)", ("cases", r, json.dumps(d))); c.commit()
    return r
u.save_case = ussd_case

@app.post("/ussd")
def ussd():
    return u.handle(request.form.get("text", ""), request.form.get("phoneNumber", "")), 200, {"Content-Type": "text/plain"}
