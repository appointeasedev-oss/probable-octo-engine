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
# Max time to run main.py or tests
RUN_TIMEOUT = 15
# Sleep between retries
RETRY_DELAY = 2
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

    # Apply unified diff manually
    patch_lines = difflib.unified_diff(old, diff_text.splitlines(keepends=True))
    new = list(difflib.restore(list(patch_lines), 1))

    if new != old:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w") as f:
            f.writelines(new)
        return True
    return False

def run_main():
    try:
        subprocess.check_output(
            ["python", os.path.join(ARAS_ROOT, "main.py")],
            stderr=subprocess.STDOUT, timeout=RUN_TIMEOUT
        )
        return True, ""
    except subprocess.CalledProcessError as e:
        return False, e.output.decode()
    except Exception as e:
        return False, str(e)

def run_tests():
    if not os.path.exists(os.path.join(ARAS_ROOT, "tests")):
        return True, ""
    try:
        subprocess.check_output(
            ["pytest", ARAS_ROOT],
            stderr=subprocess.STDOUT, timeout=RUN_TIMEOUT
        )
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

def parse_previous_logs():
    done = set()
    if not os.path.exists(LOG_DIR):
        return done
    for log in os.listdir(LOG_DIR):
        with open(os.path.join(LOG_DIR, log)) as f:
            for m in re.findall(r"- Improvements done: (.+)", f.read()):
                done.add(m.strip())
    return done

def write_log(counter, text):
    with open(os.path.join(LOG_DIR, f"log_{counter}.txt"), "w") as f:
        f.write(text)

# ---------- Brain ----------
def main():
    ensure_env()
    counter = read_counter() + 1
    snap = snapshot(counter)
    workspace = read_workspace()
    memory = parse_previous_logs()

    base_prompt = f"""
You are ARAS, an autonomous coding agent.

LONG-TERM GOALS:
- Always improve ARAS folder
- Modularize and refactor code
- Ensure main.py runs
- Add or improve tests if present
- Accumulate improvements without repeating past work

RULES:
- Return ONLY valid JSON
- Plan before executing
- Use diff if possible, fallback to full file overwrite if necessary
- At least one file must be changed
- main.py must run successfully

Workspace:
{json.dumps(workspace, indent=2)}

Previous improvements (do not repeat):
{memory}

JSON FORMAT:
{{
  "plan": ["step1", "step2"],
  "diffs": [
    {{
      "path": "relative/path.py",
      "diff": "unified diff or full content"
    }}
  ],
  "summary": "**Summary:**\\n- Improvements done: ...\\n- Next improvements to consider: ..."
}}
"""

    last_error = ""
    while True:  # Loop until success
        prompt = base_prompt + (f"\nERROR TO FIX:\n{last_error}" if last_error else "")
        response = call_openrouter(prompt)
        ai_text = response["choices"][0]["message"]["content"]
        try:
            data = extract_json(ai_text)
            changes_applied = False

            # Apply diffs or full file writes
            for d in data.get("diffs", []):
                applied = apply_diff(d["path"], d["diff"])
                changes_applied = changes_applied or applied

            if not changes_applied:
                last_error = "No file changes applied. Retrying..."
                time.sleep(RETRY_DELAY)
                rollback(snap)
                continue

            # Run main.py
            ok, err = run_main()
            if not ok:
                last_error = f"main.py failed: {err}"
                time.sleep(RETRY_DELAY)
                rollback(snap)
                continue

            # Run tests
            ok, err = run_tests()
            if not ok:
                last_error = f"Tests failed: {err}"
                time.sleep(RETRY_DELAY)
                rollback(snap)
                continue

            # Success
            write_counter(counter)
            write_log(counter, data.get("summary", "**Summary:** No summary provided"))
            print(f"ARAS run {counter} complete. Improvements applied successfully.")
            return

        except Exception as e:
            last_error = str(e)
            time.sleep(RETRY_DELAY)
            rollback(snap)

if __name__ == "__main__":
    main()
