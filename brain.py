import os
import random
import requests
import re
import subprocess

# ----------------- Config -----------------
EXAMPLE_FILE = "ARAS/main.py"
LOG_DIR = "logs"
ERROR_DIR = "error_runs"
COUNTER_FILE = "counter.txt"

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
    os.makedirs(ERROR_DIR, exist_ok=True)
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

    # ---- Initial AI improvement prompt ----
    prompt = f"""
You are an AI assistant improving Python code. 
Your task: 
1. Improve this Python code into a working interactive chat program.
2. Return only valid Python code. Do NOT include explanations, Markdown, quotes, or any text outside the Python code.
3. At the very end of the file, include a '**Summary:**' section as a Python comment block, listing:
   - Improvements done
   - Next improvements to consider

Current code:
{current_code}

Previous improvements (do not repeat):
{previous_improvements}
"""

    try:
        response = call_openrouter(prompt)
        ai_text = response['choices'][0]['message']['content']

        # Split code and summary
        summary_start = ai_text.find("**Summary:**")
        if summary_start != -1:
            new_code = ai_text[:summary_start].rstrip()
            summary = ai_text[summary_start:].strip()
        else:
            new_code = ai_text
            summary = "# **Summary:** No summary provided."

        write_example(new_code)
        write_log(counter, summary)
        print(f"Run {counter} complete. ARAS/main.py updated. Log saved as log_{counter}.txt")

        # ---- Run + auto-fix loop ----
        while True:
            returncode, stdout, stderr = run_code()
            if returncode == 0:
                print("✅ ARAS/main.py runs without errors. Improvement successful!")
                break
            else:
                # Save runtime error
                error_log_file = os.path.join(ERROR_DIR, f"error_run_{counter}.txt")
                with open(error_log_file, "w") as f:
                    f.write(stderr)
                print(f"❌ Runtime error detected. Saved to {error_log_file}")

                # Ask AI to fix code
                fix_prompt = f"""
The following Python code failed to run:
{new_code}

Error message:
{stderr}

Your task: 
- Fix the code so it runs correctly as an interactive chat program.
- Return ONLY the fixed Python code (no Markdown, no explanations, no extra text).
- At the end, include a '**Summary:**' section as a Python comment block, listing:
  - Fixes applied
  - Next improvements to consider
"""
                print("Attempting AI auto-fix...")
                response = call_openrouter(fix_prompt)
                ai_text = response['choices'][0]['message']['content']

                summary_start = ai_text.find("**Summary:**")
                if summary_start != -1:
                    new_code = ai_text[:summary_start].rstrip()
                    summary_fix = ai_text[summary_start:].strip()
                else:
                    new_code = ai_text
                    summary_fix = "# **Summary:** AI fix applied, no summary."

                # Save fixed code and update log
                write_example(new_code)
                write_log(counter, summary + "\n\n" + summary_fix)
                print("AI fix applied, retrying run...")

    except Exception as e:
        print(f"Brain run failed: {e}")


if __name__ == "__main__":
    main()
