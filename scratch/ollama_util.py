"""Throwaway helpers for Task 01 measurements (stdlib only)."""
import json, time, urllib.request

BASE = "http://localhost:11434"

def post(path, payload, timeout=900):
    req = urllib.request.Request(BASE + path, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        body = json.loads(r.read().decode())
    return body, time.time() - t0

def get(path):
    with urllib.request.urlopen(BASE + path, timeout=60) as r:
        return json.loads(r.read().decode())
