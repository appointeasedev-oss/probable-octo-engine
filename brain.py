import os
import random
import requests
import re
import json

ARAS_ROOT = "ARAS"
LOG_DIR = "logs"
COUNTER_FILE = "counter.txt"

# Load OpenRouter keys from env
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
        headers = {"Authorization": f"Bearer {key}"}
        data = {
            "model": MODEL_NAME,
            "messages": [{"role": "user", "content": prompt}],
        }
        try:
            resp = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=60
            )
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
    raise RuntimeError("All OpenRouter keys failed")

def ensure_files():
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(ARAS_ROOT, exist_ok=True)

    main_file = os.path.join(ARAS_ROOT, "main.py")
    if not os.path.exists(main_file):
        with open(main_file, "w") as f:
            f.write("# ARAS main entry\n")

    if not os.path.exists(COUNTER_FILE):
        with open(COUNTER_FILE, "w") as f:
            f.write("0")

def read_counter():
    with open(COUNTER_FILE, "r") as f:
        return int(f.read().strip())

def increment_counter():
    count = read_counter() + 1
    with open(COUNTER_FILE, "w") as f:
        f.write(str(count))
    return count

def read_workspace():
    workspace = {}
    for root, dirs, files in os.walk(ARAS_ROOT):
        for file in files:
            path = os.path.join(root, file)
            rel = os.path.relpath(path, ARAS_ROOT)
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                workspace[rel] = f.read()
    return workspace

def apply_operations(ops):
    for op in ops:
        action = op["action"]
        path = os.path.normpath(os.path.join(ARAS_ROOT, op["path"]))

        if not path.startswith(os.path.abspath(ARAS_ROOT)):
            continue

        if action == "create_dir":
            os.makedirs(path, exist_ok=True)

        elif action == "write_file":
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(op["content"])

def parse_previous_logs():
    improvements_done = set()
    if not os.path.exists(LOG_DIR):
        return improvements_done
    for log in os.listdir(LOG_DIR):
        with open(os.path.join(LOG_DIR, log), "r") as f:
            text = f.read()
            matches = re.findall(r"- Improvements done: (.+)", text)
            for m in matches:
                improvements_done.add(m.strip())
    return improvements_done

def write_log(counter, summary):
    with open(os.path.join(LOG_DIR, f"log_{counter}.txt"), "w") as f:
        f.write(summary)

# -------- Brain Logic --------
def main():
    ensure_files()
    counter = increment_counter()

    workspace = read_workspace()
    previous_improvements = parse_previous_logs()

    prompt = f"""
You are Sparrow, an autonomous coding agent Your pourpous is to improve ARAS AI make it advance.

You control ONLY the ARAS directory.
You may:
- Create files
- Edit files
- Create subfolders

Current ARAS workspace (JSON):
{json.dumps(workspace, indent=2)}

Previous improvements (do not repeat):
{previous_improvements}

Respond ONLY in valid JSON with this structure:

{{
  "operations": [
    {{
      "action": "create_dir" | "write_file",
      "path": "relative/path/from/ARAS",
      "content": "file content if write_file"
    }}
  ],
  "summary": "**Summary:**\\n- Improvements done: ...\\n- Next improvements to consider: ..."
}}
"""

    response = call_openrouter(prompt)
    ai_text = response["choices"][0]["message"]["content"]

    result = json.loads(ai_text)
    apply_operations(result["operations"])
    write_log(counter, result["summary"])

    print(f"ARAS run {counter} complete.")

if __name__ == "__main__":
    main()
