import os
import random
import requests
import time
import shutil

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

# ---------------- UTILS ----------------
def ensure_dirs():
    for d in [
        LOG_DIR,
        OLD_BRAIN_DIR,
        BRAIN_HISTORY_DIR,
        BRAIN_ERROR_DIR,
        EXAMPLE_ERROR_DIR,
    ]:
        os.makedirs(d, exist_ok=True)

    if not os.path.exists(COUNTER_FILE):
        with open(COUNTER_FILE, "w") as f:
            f.write("0")

    if not os.path.exists(EXAMPLE_FILE):
        with open(EXAMPLE_FILE, "w") as f:
            f.write("# example.py\n")

def read_counter():
    return int(open(COUNTER_FILE).read().strip())

def increment_counter():
    c = read_counter() + 1
    open(COUNTER_FILE, "w").write(str(c))
    return c

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

def read_file(p):
    return open(p).read()

def write_file(p, c):
    open(p, "w").write(c)

def save_error(folder, text):
    ts = int(time.time())
    path = os.path.join(folder, f"error_{ts}.txt")
    write_file(path, text)
    return path

# ---------------- AI VERIFY (NOT TOO STRICT) ----------------
def ai_verify(code):
    prompt = f"""
You are a Python verifier.

Rules:
- ONLY check for syntax or runtime-breaking errors
- Ignore style, optimization, or architecture
- Answer strictly:
YES -> code can run
NO -> code has errors (explain shortly)

Code:
{code}
"""
    result = call_ai(prompt)
    return result.strip()

# ---------------- AI IMPROVE ----------------
def ai_improve(code, previous_error=""):
    prompt = f"""
You are improving Python code.

STRICT RULES:
- Do NOT change AI model or provider references
- Fix ONLY real issues or make safe improvements
- If previous error exists, FIX IT
- Output FULL CODE ONLY
- No explanations outside code

Previous error:
{previous_error}

Code:
{code}
"""
    return call_ai(prompt)

# ---------------- SELF UPDATE LOGIC ----------------
def improve_with_retry(file_path, error_dir, allow_retry):
    original = read_file(file_path)
    last_error = ""

    for attempt in range(2 if allow_retry else 1):
        improved = ai_improve(original, last_error)
        verify = ai_verify(improved)

        if verify.startswith("YES"):
            write_file(file_path, improved)
            return True, improved

        last_error = verify
        save_error(error_dir, verify)

    return False, original

# ---------------- MAIN ----------------
def main():
    ensure_dirs()
    counter = increment_counter()
    log_text = f"Run #{counter}\n"

    # -------- BACKUP OLD BRAIN --------
    ts = int(time.time())
    old_brain_path = os.path.join(OLD_BRAIN_DIR, f"brain_{ts}.py")
    shutil.copyfile(BRAIN_FILE, old_brain_path)

    # -------- BRAIN SELF UPDATE (ONE TIME ONLY) --------
    ok, _ = improve_with_retry(
        BRAIN_FILE,
        BRAIN_ERROR_DIR,
        allow_retry=True,  # retry ONCE
    )

    if ok:
        shutil.copyfile(
            BRAIN_FILE,
            os.path.join(BRAIN_HISTORY_DIR, f"brain_{ts}.py"),
        )
        log_text += "Brain updated successfully\n"
    else:
        shutil.copyfile(old_brain_path, BRAIN_FILE)
        log_text += "Brain update failed → rolled back\n"

    # -------- EXAMPLE UPDATE (CAN REPEAT EVERY RUN) --------
    ex_ok, _ = improve_with_retry(
        EXAMPLE_FILE,
        EXAMPLE_ERROR_DIR,
        allow_retry=True,
    )

    log_text += (
        "example.py updated\n" if ex_ok else "example.py verification failed\n"
    )

    # -------- LOG --------
    log_path = os.path.join(LOG_DIR, f"log_{counter}.txt")
    write_file(log_path, log_text)

    print("Run complete.")

if __name__ == "__main__":
    main()
