import os
import random
import requests
import re
import subprocess

# ----------------- Config -----------------
EXAMPLE_FILE = "ARAS/main.py"   # <-- Now editing ARAS/main.py
LOG_DIR = "logs"
COUNTER_FILE = "counter.txt"
MAX_FIX_ATTEMPTS = 2  # how many times to retry AI fix on runtime error

# Load OpenRouter keys from environment variables
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
            else:
                print(f"Key failed ({resp.status_code}), trying next key...")
        except Exception as e:
            print(f"Exception with key: {e}, trying next key...")
    raise RuntimeError("All OpenRouter keys failed")

def ensure_files():
    os.makedirs(LOG_DIR, exist_ok=True)
    if not os.path.exists(EXAMPLE_FILE):
        os.makedirs(os.path.dirname(EXAMPLE_FILE), exist_ok=True)
        with open(EXAMPLE_FILE, "w") as f:
            f.write("# ARAS main.py starter code\n")
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

def read_example():
    with open(EXAMPLE_FILE, "r") as f:
        return f.read()

def write_example(content):
    with open(EXAMPLE_FILE, "w") as f:
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

def write_log(counter, summary):
    log_file = os.path.join(LOG_DIR, f"log_{counter}.txt")
    with open(log_file, "w") as f:
        f.write(summary)

def extract_summary(ai_response):
    text = ai_response['choices'][0]['message']['content']
    summary_index = text.find("**Summary:**")
    if summary_index != -1:
        return text[summary_index:]
    return "\n".join(text.splitlines()[-20:])

# -------- Run ARAS/main.py and return result --------
def run_code():
    try:
        result = subprocess.run(
            ["python", EXAMPLE_FILE],
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)

# -------- Brain Logic --------
def main():
    ensure_files()
    counter = increment_counter()
    current_code = read_example()
    previous_improvements = parse_previous_logs()

    prompt = f"""
You are an AI assistant improving Python code. Improve it so that when the user runs it, it is an interactive chat program with the user.
Current code:
{current_code}

Previous improvements (do not repeat):
{previous_improvements}

Return the full improved Python code, and include a clear summary section starting with '**Summary:**' listing:
- Improvements done
- Next improvements to consider
"""

    try:
        response = call_openrouter(prompt)
        ai_text = response['choices'][0]['message']['content']

        # Split code and summary
        summary_start = ai_text.find("**Summary:**")
        if summary_start != -1:
            new_code = ai_text[:summary_start].strip()
            summary = ai_text[summary_start:].strip()
        else:
            new_code = ai_text
            summary = "**Summary:** No summary provided."

        # Save improved code
        write_example(new_code)
        write_log(counter, summary)
        print(f"Run {counter} complete. ARAS/main.py updated. Log saved as log_{counter}.txt")

        # ----- Post-run check with self-fix -----
        attempt = 0
        while attempt <= MAX_FIX_ATTEMPTS:
            returncode, stdout, stderr = run_code()
            if returncode == 0:
                print("✅ Improvement successful! ARAS/main.py runs without errors.")
                break
            else:
                attempt += 1
                print(f"❌ Runtime error detected on attempt {attempt}:\n{stderr}")

                if attempt > MAX_FIX_ATTEMPTS:
                    error_log_file = os.path.join(LOG_DIR, f"error_run_{counter}.txt")
                    with open(error_log_file, "w") as f:
                        f.write(stderr)
                    print(f"❌ Maximum fix attempts reached. Check {error_log_file} for details.")
                    break

                # Ask AI to fix runtime error
                fix_prompt = f"""
The following Python code failed to run due to errors:
{new_code}

Error message:
{stderr}

Please fix the code so it runs correctly as a chat program and return the full corrected code with '**Summary:**' of fixes.
"""
                print("Attempting AI fix...")
                response = call_openrouter(fix_prompt)
                ai_text = response['choices'][0]['message']['content']
                summary_start = ai_text.find("**Summary:**")
                if summary_start != -1:
                    new_code = ai_text[:summary_start].strip()
                    summary_fix = ai_text[summary_start:].strip()
                else:
                    new_code = ai_text
                    summary_fix = "**Summary:** AI fix applied, no summary."

                # Save fixed code and updated summary log
                write_example(new_code)
                write_log(counter, summary + "\n\n" + summary_fix)
                print("AI fix applied, retrying run...")

    except Exception as e:
        print(f"Brain run failed: {e}")

if __name__ == "__main__":
    main()
