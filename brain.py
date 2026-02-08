import os
import json
import random
import requests
import subprocess
import re
import time

# ================= CONFIG =================
ARAS_ROOT = "ARAS"
LOG_DIR = "logs"
COUNTER_FILE = "counter.txt"
MODEL_NAME = "arcee-ai/trinity-large-preview:free"
MAX_RETRIES = 3

OPENROUTER_KEYS = [
    os.getenv("OPENROUTER_KEY_1"),
    os.getenv("OPENROUTER_KEY_2"),
    os.getenv("OPENROUTER_KEY_3"),
    os.getenv("OPENROUTER_KEY_4"),
    os.getenv("OPENROUTER_KEY_5"),
]
# =========================================


# ---------- Utilities ----------
def rotate_keys():
    keys = [k for k in OPENROUTER_KEYS if k]
    random.shuffle(keys)
    return keys


def call_openrouter(prompt):
    for key in rotate_keys():
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


def ensure_environment():
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


def write_counter(value):
    with open(COUNTER_FILE, "w") as f:
        f.write(str(value))


def read_workspace():
    data = {}
    for root, _, files in os.walk(ARAS_ROOT):
        for file in files:
            path = os.path.join(root, file)
            rel = os.path.relpath(path, ARAS_ROOT)
            with open(path, "r", errors="ignore") as f:
                data[rel] = f.read()
    return data


def parse_previous_logs():
    done = set()
    if not os.path.exists(LOG_DIR):
        return done
    for log in os.listdir(LOG_DIR):
        with open(os.path.join(LOG_DIR, log)) as f:
            for m in re.findall(r"- Improvements done: (.+)", f.read()):
                done.add(m.strip())
    return done


def extract_json(text):
    try:
        return json.loads(text)
    except:
        pass

    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        return json.loads(match.group())

    raise ValueError("Invalid JSON")


def apply_operations(ops):
    changed = False
    for op in ops:
        path = os.path.abspath(os.path.join(ARAS_ROOT, op["path"]))
        if not path.startswith(os.path.abspath(ARAS_ROOT)):
            continue

        if op["action"] == "create_dir":
            os.makedirs(path, exist_ok=True)
            changed = True

        elif op["action"] == "write_file":
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(op["content"])
            changed = True

    return changed


def run_aras_main():
    try:
        subprocess.check_output(
            ["python", os.path.join(ARAS_ROOT, "main.py")],
            stderr=subprocess.STDOUT,
            timeout=10,
        )
        return True, "Execution OK"
    except subprocess.CalledProcessError as e:
        return False, e.output.decode()
    except Exception as e:
        return False, str(e)


def write_log(counter, text):
    with open(os.path.join(LOG_DIR, f"log_{counter}.txt"), "w") as f:
        f.write(text)


# ---------- Brain ----------
def main():
    ensure_environment()
    counter = read_counter() + 1

    workspace = read_workspace()
    memory = parse_previous_logs()

    base_prompt = f"""
You are ARAS, a real autonomous coding agent.

STRICT RULES:
- You MUST change at least one file inside ARAS/.
- You MAY create folders/files.
- You MUST keep ARAS/main.py runnable.
- You MUST return ONLY valid JSON.
- No explanations. No markdown.

Workspace:
{json.dumps(workspace, indent=2)}

Previous improvements (do not repeat):
{memory}

JSON FORMAT:
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

    last_error = ""
    for attempt in range(1, MAX_RETRIES + 1):
        prompt = base_prompt
        if last_error:
            prompt += f"\nERROR TO FIX:\n{last_error}"

        response = call_openrouter(prompt)
        ai_text = response["choices"][0]["message"]["content"]

        try:
            result = extract_json(ai_text)
            changed = apply_operations(result["operations"])

            if not changed:
                last_error = "No filesystem changes were made."
                continue

            ok, runtime = run_aras_main()
            if not ok:
                last_error = runtime
                continue

            write_counter(counter)
            write_log(counter, result["summary"] + "\n\nRuntime OK")
            print(f"ARAS run {counter} complete.")
            return

        except Exception as e:
            last_error = str(e)

    raise RuntimeError("ARAS failed after maximum retries")


if __name__ == "__main__":
    main()
