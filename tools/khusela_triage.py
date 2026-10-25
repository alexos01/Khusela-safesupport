#!/usr/bin/env python3
"""Khusela case triage: turns the Agent desk export into a priority queue
and an anonymous prevention report. Usage: python khusela_triage.py khusela-cases.json"""
import json, sys, csv, time
from collections import Counter

RANK = {"Critical": 0, "High": 1, "Medium": 2, "Standard": 3}
SLA_MIN = {"Critical": 5, "High": 15, "Medium": 30, "Standard": 60}  # time to first agent action

def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def minutes_old(case):
    return (time.time() * 1000 - case["t"]) / 60000

def queue(cases):
    rows = []
    for c in cases:
        if c.get("status") == "Closed":
            continue
        age = minutes_old(c)
        breach = c["status"] == "Received" and age > SLA_MIN[c["urgency"]]
        rows.append({"ref": c["ref"], "urgency": c["urgency"], "country": c["country"],
                     "status": c["status"], "minutes_waiting": round(age),
                     "sla_breached": breach})
    return sorted(rows, key=lambda r: (not r["sla_breached"], RANK[r["urgency"]], -r["minutes_waiting"]))

def anonymous_stats(cases):
    """No names, contacts, text or locations leave this function."""
    return {"total": len(cases),
            "by_country": Counter(c["country"] for c in cases),
            "by_urgency": Counter(c["urgency"] for c in cases),
            "by_status": Counter(c["status"] for c in cases),
            "closed_rate": round(sum(c["status"] == "Closed" for c in cases) / max(len(cases), 1), 2)}

if __name__ == "__main__":
    cases = load(sys.argv[1])
    q = queue(cases)
    with open("priority_queue.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(q[0].keys()) if q else ["ref"])
        w.writeheader(); w.writerows(q)
    with open("prevention_report.json", "w", encoding="utf-8") as f:
        json.dump(anonymous_stats(cases), f, indent=1)
    print(f"{len(q)} open cases, {sum(r['sla_breached'] for r in q)} past their response target.")
