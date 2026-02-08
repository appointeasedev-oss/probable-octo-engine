import os
import random
import requests
import time
from datetime import datetime

# ---------------- CONFIG ----------------
BRAIN_FILE = "brain.py"
EXAMPLE_FILE = "example.py"

LOG_DIR = "logs"
OLD_BRAIN_DIR = "old_brain"
BRAIN_HISTORY_DIR = "brain_history"
BRAIN_ERROR_DIR = "brain_errors"
EXAMPLE_ERROR_DIR = "example_errors"

COUNTER_FILE = "counter.txt"
MODEL_NAME = "arcee-ai/trinity-large-preview:free"

OPENROUTER_KEYS = [
    os.getenv("OPENROUTER_KEY_1"),
    os.getenv("OPENROUTER_KEY_2"),
    os.getenv("OPENROUTER_KEY_3"),
    os.getenv("OPENROUTER_KEY_4"),
    os.getenv("OPENROUTER_KEY_5"),
]

# ---------------- FILE SYSTEM ----------------
def ensure_dirs():
    for d in [
        LOG_DIR,
        OLD_BRAIN_DIR,
        BRAIN_HISTORY_DIR,
        BRAIN_ERROR_DIR,
        EXAMPLE_ERROR_DIR,
    ]:
        os.makedirs(d, exist_ok=True)
        keep = os.path.join(d, ".gitkeep")
        if not os.path.exists(keep):
            open(keep, "w").write("")

    if not os.path.exists(COUNTER_FILE):
        open(COUNTER_FILE, "w").write("0")

    if not os.path.exists(EXAMPLE_FILE):
        open(EXAMPLE_FILE, "w").write("# example.py\n")

# ---------------- COUNTER ----------------
def increment_counter():
    val = int(open(COUNTER_FILE).read().strip()) + 1
    open(COUNTER_FILE, "w").write(str(val))
    return val

# ---------------- AI CORE ----------------
def rotate_keys():
    keys = [k for k in OPENROUTER_KEYS if k]
    random.shuffle(keys)
    return keys

def call_ai(prompt):
    for key in rotate_keys():
        try:
            r = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}"},
                json={
                    "model": MODEL_NAME,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=60,
            )
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"]
        except Exception:
            continue
    raise RuntimeError("All OpenRouter keys failed")

# ---------------- VERIFY ----------------
def verify_code(code):
    prompt = f"""
Check ONLY for Python syntax or runtime-breaking errors.
Ignore style and optimization.

Answer strictly:
YES
or
NO: <short reason>

Code:
{code}
"""
    return call_ai(prompt)

# ---------------- IMPROVE ----------------
def improve_code(code, previous_error):
    prompt = f"""
Improve this Python code with engineering intent.

STRICT RULES:
- Do NOT change AI model or provider references
- ALWAYS attempt improvement (even small)
- Fix previous error if present
- Output FULL CODE
- Append a **Summary** section exactly as shown below

Previous error:
{previous_error}

Code:
{code}

FORMAT:
<code>

**Summary:**
**Improvements done:**
- ...

**Next improvements to consider:**
- ...
"""
    return call_ai(prompt)

# ---------------- CORE UPDATE LOGIC ----------------
def improve_file(path, error_dir, allow_retry):
    original = open(path).read()
    last_error = ""
    improved_summary = ""

    for attempt in range(2 if allow_retry else 1):
        new_content = improve_code(original, last_error)
        verify = verify_code(new_content)

        if verify.strip().startswith("YES"):
            open(path, "w").write(new_content)
            improved_summary = new_content.split("**Summary:**", 1)[-1]
            return True, improved_summary

        last_error = verify
        ts = int(time.time())
        open(os.path.join(error_dir, f"error_{ts}.txt"), "w").write(verify)

    return False, last_error

# ---------------- MAIN ----------------
def main():
    ensure_dirs()
    run = increment_counter()
    timestamp = int(time.time())
    now = datetime.utcnow().isoformat()

    log_lines = []
    log_lines.append(f"Run #{run} — {now}")

    # ---------- BACKUP BRAIN ----------
    old_path = os.path.join(OLD_BRAIN_DIR, f"brain_{timestamp}.py")
    open(old_path, "w").write(f"# Backup {now}\n\n" + open(BRAIN_FILE).read())

    # ---------- BRAIN UPDATE ----------
    success, brain_info = improve_file(BRAIN_FILE, BRAIN_ERROR_DIR, allow_retry=True)

    if success:
        hist = os.path.join(BRAIN_HISTORY_DIR, f"brain_{timestamp}.py")
        open(hist, "w").write(open(BRAIN_FILE).read())
        log_lines.append("SUCCESS: brain.py updated")
        log_lines.append("")
        log_lines.append("**Summary:**")
        log_lines.append(brain_info.strip())
    else:
        open(BRAIN_FILE, "w").write(open(old_path).read())
        log_lines.append("FAIL: brain.py update failed")
        log_lines.append("")
        log_lines.append("**Summary:**")
        log_lines.append(brain_info)

    # ---------- EXAMPLE UPDATE ----------
    ex_success, ex_info = improve_file(EXAMPLE_FILE, EXAMPLE_ERROR_DIR, allow_retry=True)

    if ex_success:
        log_lines.append("")
        log_lines.append("SUCCESS: example.py updated")
        log_lines.append("")
        log_lines.append("**Summary:**")
        log_lines.append(ex_info.strip())
    else:
        log_lines.append("")
        log_lines.append("FAIL: example.py update failed")
        log_lines.append("")
        log_lines.append("**Summary:**")
        log_lines.append(ex_info)

    # ---------- WRITE LOG ----------
    open(os.path.join(LOG_DIR, f"log_{run}.txt"), "w").write("\n".join(log_lines))
    print("Run complete.")

if __name__ == "__main__":
    main()
