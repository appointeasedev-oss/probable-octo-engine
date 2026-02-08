import os
import random
import requests
import re
import subprocess
import time
import shutil

# ---------- Config ----------
EXAMPLE_FILE = "example.py"
LOG_DIR = "logs"
TEST_DIR = "test"
OLD_BRAIN_DIR = "old_brain"
BRAIN_HISTORY_DIR = "brain_history"
COUNTER_FILE = "counter.txt"
BRAIN_FILE = "brain.py"

OPENROUTER_KEYS = [
    os.getenv("OPENROUTER_KEY_1"),
    os.getenv("OPENROUTER_KEY_2"),
    os.getenv("OPENROUTER_KEY_3"),
    os.getenv("OPENROUTER_KEY_4"),
    os.getenv("OPENROUTER_KEY_5"),
]

MODEL_NAME = "arcee-ai/trinity-large-preview:free"
VERIFIER_MODEL = "arcee-ai/trinity-large-preview:free"

# ---------- Helpers ----------
def rotate_keys():
    keys = [k for k in OPENROUTER_KEYS if k]
    random.shuffle(keys)
    return keys

def call_openrouter(prompt, model=MODEL_NAME):
    keys = rotate_keys()
    for key in keys:
        headers = {"Authorization": f"Bearer {key}"}
        data = {
            "model": model,
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
            else:
                print(f"Key failed ({resp.status_code}), trying next key...")
        except Exception as e:
            print(f"Exception with key: {e}, trying next key...")
    raise RuntimeError("All OpenRouter keys failed")

def ensure_dirs():
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(TEST_DIR, exist_ok=True)
    os.makedirs(OLD_BRAIN_DIR, exist_ok=True)
    os.makedirs(BRAIN_HISTORY_DIR, exist_ok=True)
    if not os.path.exists(EXAMPLE_FILE):
        with open(EXAMPLE_FILE, "w") as f:
            f.write("# example.py - basic calculator\n")
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

def read_file(path):
    with open(path, "r") as f:
        return f.read()

def write_file(path, content):
    with open(path, "w") as f:
        f.write(content)

def parse_previous_logs():
    improvements_done = set()
    if not os.path.exists(LOG_DIR):
        return improvements_done
    logs = sorted(os.listdir(LOG_DIR))
    for log_file in logs:
        path = os.path.join(LOG_DIR, log_file)
        with open(path, "r") as f:
            text = f.read()
            matches = re.findall(r"- Improvements done: (.+)", text)
            for m in matches:
                improvements_done.add(m.strip())
    return improvements_done

def write_log(counter, summary, folder=LOG_DIR):
    log_file = os.path.join(folder, f"log_{counter}.txt")
    with open(log_file, "w") as f:
        f.write(summary)

def run_test_file():
    test_file = os.path.join(TEST_DIR, f"test_run_{int(time.time())}.txt")
    with open(test_file, "w") as f:
        try:
            proc = subprocess.Popen(
                ["python", EXAMPLE_FILE],
                stdout=f,
                stderr=subprocess.STDOUT
            )
            time.sleep(5)
            proc.terminate()
        except Exception as e:
            f.write(f"\nTest run failed: {e}")
    print(f"Test run completed. Output saved in {test_file}")

def verify_code_with_ai(code):
    prompt = f"""
You are a strict code verifier AI.
Check this Python code for correctness and safety.
Rules:
- Do NOT change AI model/provider references.
- Do not provide general or vague answers.
- Only allow safe improvements.
- Respond only YES if code is fully correct and safe, otherwise NO and explain.

Code to verify:
{code}
"""
    response = call_openrouter(prompt, model=VERIFIER_MODEL)
    ai_text = response['choices'][0]['message']['content'].strip().upper()
    return "YES" in ai_text

def improve_file_with_ai(file_path, previous_improvements, retry_until_pass=True):
    code = read_file(file_path)
    while True:
        prompt = f"""
You are an AI assistant improving Python code with clear purpose to increase engineering quality.
Rules:
- Do NOT change AI model/provider references.
- Do not give vague/general changes.
- Only make safe improvements.

Current code:
{code}

Previous improvements (do not repeat):
{previous_improvements}

Return full improved code with summary starting '**Summary:**' listing:
- Improvements done
- Next improvements to consider
"""
        response = call_openrouter(prompt)
        ai_text = response['choices'][0]['message']['content']
        summary_start = ai_text.find("**Summary:**")
        if summary_start != -1:
            new_code = ai_text[:summary_start].strip()
            summary = ai_text[summary_start:].strip()
        else:
            new_code = ai_text
            summary = "**Summary:** No summary provided."

        if verify_code_with_ai(new_code):
            write_file(file_path, new_code)
            return summary
        else:
            if retry_until_pass:
                print(f"Verification failed for {file_path}, retrying...")
                code = new_code
            else:
                print(f"Verification failed for {file_path}, skipping update.")
                return None

# ---------- Brain Self-Update ----------
def self_update_brain():
    timestamp = int(time.time())
    old_brain_path = os.path.join(OLD_BRAIN_DIR, f"brain_{timestamp}.py")
    shutil.copyfile(BRAIN_FILE, old_brain_path)

    code = read_file(BRAIN_FILE)
    print("Attempting brain self-update...")

    prompt = f"""
You are an AI improving your own brain.py with strict purpose.
Rules:
- Improve engineering quality and maintainability.
- Do NOT change AI model/provider references.
- Do not provide vague/general improvements.
- Only safe improvements.
- Return full updated brain.py code and summary starting '**Summary:**'.

Current brain.py code:
{code}
"""
    response = call_openrouter(prompt)
    ai_text = response['choices'][0]['message']['content']
    summary_start = ai_text.find("**Summary:**")
    if summary_start != -1:
        new_code = ai_text[:summary_start].strip()
        summary = ai_text[summary_start:].strip()
    else:
        new_code = ai_text
        summary = "**Summary:** No summary provided."

    # Verify new brain
    if verify_code_with_ai(new_code):
        write_file(BRAIN_FILE, new_code)
        print("Brain self-update successful.")
        save_brain_history(new_code, summary)
    else:
        print("Brain verification failed. Sending once to AI to fix...")
        prompt_fix = f"""
The previous brain.py update failed verification. Fix the errors safely without changing AI model/provider.
Code:
{new_code}
"""
        response_fix = call_openrouter(prompt_fix)
        ai_text_fix = response_fix['choices'][0]['message']['content']
        summary_start_fix = ai_text_fix.find("**Summary:**")
        if summary_start_fix != -1:
            new_code_fix = ai_text_fix[:summary_start_fix].strip()
            summary_fix = ai_text_fix[summary_start_fix:].strip()
        else:
            new_code_fix = ai_text_fix
            summary_fix = "**Summary:** No summary provided."

        if verify_code_with_ai(new_code_fix):
            write_file(BRAIN_FILE, new_code_fix)
            print("Brain self-update successful after fix.")
            save_brain_history(new_code_fix, summary_fix)
        else:
            print("Brain self-update failed after fix. Restoring old brain...")
            shutil.copyfile(old_brain_path, BRAIN_FILE)
            print("Old brain restored.")

def save_brain_history(code, summary):
    timestamp = int(time.time())
    hist_file = os.path.join(BRAIN_HISTORY_DIR, f"brain_{timestamp}.py")
    write_file(hist_file, code)
    write_log(timestamp, summary, folder=BRAIN_HISTORY_DIR)
    print(f"Brain history saved at {hist_file}")

# ---------- Main Brain Logic ----------
def main():
    ensure_dirs()
    counter = increment_counter()

    # Step 1: Self-update brain.py
    self_update_brain()

    # Step 2: Improve example.py
    previous_improvements = parse_previous_logs()
    summary = improve_file_with_ai(EXAMPLE_FILE, previous_improvements, retry_until_pass=True)
    if summary:
        write_log(counter, summary)
        print(f"example.py improved. Log saved.")

    # Step 3: Test example.py
    run_test_file()

if __name__ == "__main__":
    main()
