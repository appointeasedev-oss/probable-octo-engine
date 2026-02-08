import os
import json
import random
import requests
import subprocess
import shutil
import difflib
import re
import time

# ================= CONFIG =================
ARAS_ROOT = "ARAS"
LOG_DIR = "logs"
SNAPSHOT_DIR = "snapshots"
COUNTER_FILE = "counter.txt"
MODEL_NAME = "arcee-ai/trinity-large-preview:free"

MAX_RETRIES = 4
# =========================================

OPENROUTER_KEYS = [
    os.getenv("OPENROUTER_KEY_1"),
    os.getenv("OPENROUTER_KEY_2"),
    os.getenv("OPENROUTER_KEY_3"),
    os.getenv("OPENROUTER_KEY_4"),
    os.getenv("OPENROUTER_KEY_5"),
]

# ---------- Utilities ----------
def rotate_keys():
    keys = [k for k in OPENROUTER_KEYS if k]
    random.shuffle(keys)
    return keys

def call_openrouter(prompt):
    for key in rotate_keys():
        try:
            r = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}"},
                json={"model": MODEL_NAME, "messages": [{"role": "user", "content": prompt}]},
                timeout=60,
            )
            if r.status_code == 200:
                return r.json()
        except:
            pass
    raise RuntimeError("All OpenRouter keys failed")

def ensure_env():
    os.makedirs(ARAS_ROOT, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)

    main_py = os.path.join(ARAS_ROOT, "main.py")
    if not os.path.exists(main_py):
        with open(main_py, "w") as f:
            f.write("print('ARAS running')\n")

    if not os.path.exists(COUNTER_FILE):
        with open(COUNTER_FILE, "w") as f:
            f.write("0")

def read_counter():
    with open(COUNTER_FILE) as f:
        return int(f.read().strip())

def write_counter(v):
    with open(COUNTER_FILE, "w") as f:
        f.write(str(v))

def snapshot(counter):
    path = os.path.join(SNAPSHOT_DIR, f"run_{counter}")
    if os.path.exists(path):
        shutil.rmtree(path)
    shutil.copytree(ARAS_ROOT, path)
    return path

def rollback(snapshot_path):
    shutil.rmtree(ARAS_ROOT)
    shutil.copytree(snapshot_path, ARAS_ROOT)

def read_workspace():
    data = {}
    for root, _, files in os.walk(ARAS_ROOT):
        for file in files:
            p = os.path.join(root, file)
            rel = os.path.relpath(p, ARAS_ROOT)
            with open(p, "r", errors="ignore") as f:
                data[rel] = f.read()
    return data

def apply_diff(path, diff_text):
    file_path = os.path.join(ARAS_ROOT, path)
    old = []
    if os.path.exists(file_path):
        with open(file_path) as f:
            old = f.readlines()

    diff = list(difflib.unified_diff(old, diff_text.splitlines(keepends=True)))
    new = []
    for line in diff:
        if line.startswith("+") and not line.startswith("+++"):
            new.append(line[1:])
        elif line.startswith(" ") or line.startswith("@"):
            continue
        elif line.startswith("-"):
            continue

    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w") as f:
        f.writelines(new)

def run_main():
    try:
        subprocess.check_output(["python", os.path.join(ARAS_ROOT, "main.py")],
                                stderr=subprocess.STDOUT, timeout=10)
        return True, ""
    except subprocess.CalledProcessError as e:
        return False, e.output.decode()

def run_tests():
    try:
        subprocess.check_output(["pytest"], stderr=subprocess.STDOUT, timeout=20)
        return True, ""
    except Exception as e:
        return False, str(e)

def extract_json(text):
    try:
        return json.loads(text)
    except:
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            return json.loads(m.group())
    raise ValueError("Invalid JSON")

def write_log(counter, text):
    with open(os.path.join(LOG_DIR, f"log_{counter}.txt"), "w") as f:
        f.write(text)

# ---------- Brain ----------
def main():
    ensure_env()
    counter = read_counter() + 1
    snap = snapshot(counter)

    workspace = read_workspace()

    base_prompt = f"""
You are ARAS, a real autonomous coding agent.

LONG-TERM GOALS:
- Improve structure and reliability
- Increase test coverage
- Reduce runtime errors
- Improve maintainability

RULES:
- You MUST plan first.
- You MUST apply at least one diff.
- You MUST keep code runnable.
- Use DIFFS only.
- Output ONLY valid JSON.

Workspace:
{json.dumps(workspace, indent=2)}

JSON FORMAT:
{{
  "plan": ["step1", "step2"],
  "diffs": [
    {{
      "path": "relative/path.py",
      "diff": "unified diff text"
    }}
  ],
  "summary": "**Summary:**\\n- Improvements done: ...\\n- Next improvements to consider: ..."
}}
"""

    error = ""
    for attempt in range(MAX_RETRIES):
        prompt = base_prompt + (f"\nERROR TO FIX:\n{error}" if error else "")
        response = call_openrouter(prompt)
        data = extract_json(response["choices"][0]["message"]["content"])

        try:
            for d in data["diffs"]:
                apply_diff(d["path"], d["diff"])

            ok, err = run_main()
            if not ok:
                raise RuntimeError(err)

            if os.path.exists("tests"):
                ok, err = run_tests()
                if not ok:
                    raise RuntimeError(err)

            write_counter(counter)
            write_log(counter, data["summary"])
            print(f"ARAS run {counter} complete.")
            return

        except Exception as e:
            rollback(snap)
            error = str(e)

    raise RuntimeError("ARAS failed after max retries")

if __name__ == "__main__":
    main()
