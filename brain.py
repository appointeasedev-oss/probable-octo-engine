import os
import random
import requests
import time
from datetime import datetime

# ================= CONFIG =================
BRAIN_FILE = "brain.py"
EXAMPLE_FILE = "example.py"

BRAIN_COUNTER_FILE = "brain_counter.txt"

BRAIN_LOG_DIR = "brain_logs"
BRAIN_OLD_DIR = "brain_old"
BRAIN_HISTORY_DIR = "brain_history"
BRAIN_ERROR_DIR = "brain_errors"

EXAMPLE_ERROR_DIR = "example_errors"

MODEL_NAME = "arcee-ai/trinity-large-preview:free"

OPENROUTER_KEYS = [
    os.getenv("OPENROUTER_KEY_1"),
    os.getenv("OPENROUTER_KEY_2"),
    os.getenv("OPENROUTER_KEY_3"),
    os.getenv("OPENROUTER_KEY_4"),
    os.getenv("OPENROUTER_KEY_5"),
]

# ================= FILESYSTEM =================
def ensure_dirs():
    for d in [
        BRAIN_LOG_DIR,
        BRAIN_OLD_DIR,
        BRAIN_HISTORY_DIR,
        BRAIN_ERROR_DIR,
        EXAMPLE_ERROR_DIR,
    ]:
        os.makedirs(d, exist_ok=True)
        keep = os.path.join(d, ".gitkeep")
        if not os.path.exists(keep):
            open(keep, "w").write("")

    if not os.path.exists(BRAIN_COUNTER_FILE):
        open(BRAIN_COUNTER_FILE, "w").write("0")

    if not os.path.exists(EXAMPLE_FILE):
        open(EXAMPLE_FILE, "w").write("# example.py\n")

# ================= COUNTER =================
def increment_brain_counter():
    val = int(open(BRAIN_COUNTER_FILE).read().strip()) + 1
    open(BRAIN_COUNTER_FILE, "w").write(str(val))
    return val

# ================= AI CORE =================
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

# ================= VERIFY =================
def verify_code(code):
    prompt = f"""
Check ONLY for Python syntax or runtime-breaking errors.
Ignore style.

Answer:
YES
or
NO: <reason>

Code:
{code}
"""
    return call_ai(prompt)

# ================= IMPROVE =================
def improve_code(code, last_error):
    prompt = f"""
You are improving a self-modifying Python system.

STRICT RULES:
- Do NOT change AI model/provider references
- ALWAYS make at least one real improvement
- Fix previous error if present
- Return in TWO blocks ONLY:

<CODE>
<python code only>
</CODE>

<SUMMARY>
**Improvements done:**
- ...

**Next improvements to consider:**
- ...
</SUMMARY>

Previous error:
{last_error}

Code:
{code}
"""
    return call_ai(prompt)

def split_response(text):
    code = text.split("<CODE>")[1].split("</CODE>")[0].strip()
    summary = text.split("<SUMMARY>")[1].split("</SUMMARY>")[0].strip()
    return code, summary

# ================= CORE LOGIC =================
def improve_file(path, error_dir):
    original = open(path).read()
    last_error = ""

    for attempt in range(2):
        response = improve_code(original, last_error)
        new_code, summary = split_response(response)
        verify = verify_code(new_code)

        if verify.strip().startswith("YES"):
            open(path, "w").write(new_code)
            return True, summary

        last_error = verify
        ts = int(time.time())
        open(os.path.join(error_dir, f"error_{ts}.txt"), "w").write(verify)

    return False, last_error

# ================= MAIN =================
def main():
    ensure_dirs()
    run = increment_brain_counter()
    ts = int(time.time())
    now = datetime.utcnow().isoformat()

    log = []
    log.append(f"Brain Run #{run} — {now}")

    # ----- BACKUP BRAIN (FORCED UNIQUE) -----
    old_path = os.path.join(BRAIN_OLD_DIR, f"brain_{ts}.py")
    open(old_path, "w").write(f"# Backup at {now}\n\n" + open(BRAIN_FILE).read())

    # ----- IMPROVE BRAIN -----
    success, info = improve_file(BRAIN_FILE, BRAIN_ERROR_DIR)

    if success:
        hist = os.path.join(BRAIN_HISTORY_DIR, f"brain_{ts}.py")
        open(hist, "w").write(open(BRAIN_FILE).read())
        log.append("SUCCESS: brain.py updated")
        log.append("")
        log.append("**Summary:**")
        log.append(info)
    else:
        open(BRAIN_FILE, "w").write(open(old_path).read())
        log.append("FAIL: brain.py update failed")
        log.append("")
        log.append("**Summary:**")
        log.append(info)

    # ----- IMPROVE EXAMPLE -----
    ex_success, ex_info = improve_file(EXAMPLE_FILE, EXAMPLE_ERROR_DIR)

    if ex_success:
        log.append("")
        log.append("SUCCESS: example.py updated")
        log.append("")
        log.append("**Summary:**")
        log.append(ex_info)
    else:
        log.append("")
        log.append("FAIL: example.py update failed")
        log.append("")
        log.append("**Summary:**")
        log.append(ex_info)

    open(os.path.join(BRAIN_LOG_DIR, f"log_{run}.txt"), "w").write("\n".join(log))
    print("Brain run complete.")

if __name__ == "__main__":
    main()
