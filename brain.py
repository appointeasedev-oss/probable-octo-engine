import os
import random
import requests
import re
import json
import subprocess

ARAS_ROOT = "ARAS"
LOG_DIR = "logs"
COUNTER_FILE = "counter.txt"

OPENROUTER_KEYS = [
    os.getenv("OPENROUTER_KEY_1"),
    os.getenv("OPENROUTER_KEY_2"),
    os.getenv("OPENROUTER_KEY_3"),
    os.getenv("OPENROUTER_KEY_4"),
    os.getenv("OPENROUTER_KEY_5"),
]

MODEL_NAME = "arcee-ai/trinity-large-preview:free"

# -------- Helpers --------
def rotate_keys():
    keys = [k for k in OPENROUTER_KEYS if k]
    random.shuffle(keys)
    return keys

def call_openrouter(prompt):
    keys = rotate_keys()
    for key in keys:
        try:
            resp = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}"},
                json={
                    "model": MODEL_NAME,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=60,
            )
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
    raise RuntimeError("All OpenRouter keys failed")

def ensure_files():
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(ARAS_ROOT, exist_ok=True)

    main_py = os.path.join(ARAS_ROOT, "main.py")
    if not os.path.exists(main_py):
        with open(main_py, "w") as f:
            f.write("print('ARAS main running')\n")

    if not os.path.exists(COUNTER_FILE):
        with open(COUNTER_FILE, "w") as f:
            f.write("0")

def read_counter():
    with open(COUNTER_FILE) as f:
        return int(f.read().strip())

def increment_counter():
    c = read_counter() + 1
    with open(COUNTER_FILE, "w") as f:
        f.write(str(c))
    return c

def read_workspace():
    workspace = {}
    for root, _, files in os.walk(ARAS_ROOT):
        for file in files:
            path = os.path.join(root, file)
            rel = os.path.relpath(path, ARAS_ROOT)
            with open(path, "r", errors="ignore") as f:
                workspace[rel] = f.read()
    return workspace

def apply_operations(operations):
    did_change = False

    for op in operations:
        action = op["action"]
        target = os.path.abspath(os.path.join(ARAS_ROOT, op["path"]))

        if not target.startswith(os.path.abspath(ARAS_ROOT)):
            continue

        if action == "create_dir":
            os.makedirs(target, exist_ok=True)
            did_change = True

        elif action == "write_file":
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "w", encoding="utf-8") as f:
                f.write(op["content"])
            did_change = True

    return did_change

def parse_previous_logs():
    improvements = set()
    if not os.path.exists(LOG_DIR):
        return improvements
    for log in os.listdir(LOG_DIR):
        with open(os.path.join(LOG_DIR, log)) as f:
            text = f.read()
            matches = re.findall(r"- Improvements done: (.+)", text)
            for m in matches:
                improvements.add(m.strip())
    return improvements

def write_log(counter, text):
    with open(os.path.join(LOG_DIR, f"log_{counter}.txt"), "w") as f:
        f.write(text)

def run_aras_main():
    try:
        subprocess.check_output(
            ["python", os.path.join(ARAS_ROOT, "main.py")],
            stderr=subprocess.STDOUT,
            timeout=10,
        )
        return "ARAS/main.py executed successfully."
    except subprocess.CalledProcessError as e:
        return f"Runtime error:\n{e.output.decode()}"
    except Exception as e:
        return f"Execution failed: {e}"

# -------- Brain Logic --------
def main():
    ensure_files()
    counter = increment_counter()

    workspace = read_workspace()
    previous_improvements = parse_previous_logs()

    prompt = f"""
You are ARAS, an autonomous coding agent.

RULES (MANDATORY):
- You MUST perform at least one filesystem operation.
- You MUST modify, create, or extend files inside ARAS/.
- You MUST NOT return empty operations.
- You MUST keep ARAS/main.py runnable.

Current workspace:
{json.dumps(workspace, indent=2)}

Previous improvements (do not repeat):
{previous_improvements}

Respond ONLY in valid JSON:

{{
  "operations": [
    {{
      "action": "create_dir" | "write_file",
      "path": "relative/path/from/ARAS",
      "content": "required for write_file"
    }}
  ],
  "summary": "**Summary:**\\n- Improvements done: ...\\n- Next improvements to consider: ..."
}}
"""

    response = call_openrouter(prompt)
    result = json.loads(response["choices"][0]["message"]["content"])

    changed = apply_operations(result["operations"])

    if not changed:
        raise RuntimeError("AI returned no effective operations. Aborting run.")

    runtime_report = run_aras_main()
    summary = result["summary"] + "\n\n**Runtime Check:**\n" + runtime_report

    write_log(counter, summary)
    print(f"ARAS run {counter} complete.")

if __name__ == "__main__":
    main()
