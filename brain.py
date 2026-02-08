import os
import random
import requests
from datetime import datetime

EXAMPLE_FILE = "example.py"
LOG_DIR = "logs"
COUNTER_FILE = "counter.txt"

OPENROUTER_KEYS = [
    os.getenv("OPENROUTER_KEY_1"),
    os.getenv("OPENROUTER_KEY_2"),
    os.getenv("OPENROUTER_KEY_3"),
    os.getenv("OPENROUTER_KEY_4"),
    os.getenv("OPENROUTER_KEY_5"),
]

def rotate_keys():
    keys = [k for k in OPENROUTER_KEYS if k]
    random.shuffle(keys)
    return keys

def call_openrouter(prompt):
    keys = rotate_keys()
    for key in keys:
        headers = {"Authorization": f"Bearer {key}"}
        data = {
            "model": "qwen/qwen-3-coder:free",
            "messages": [{"role": "user", "content": prompt}],
        }
        try:
            resp = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30
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

def read_example():
    with open(EXAMPLE_FILE, "r") as f:
        return f.read()

def write_example(content):
    with open(EXAMPLE_FILE, "w") as f:
        f.write(content)

def last_log_content():
    logs = sorted(os.listdir(LOG_DIR))
    if not logs:
        return ""
    last_file = os.path.join(LOG_DIR, logs[-1])
    with open(last_file, "r") as f:
        return f.read()

def write_log(counter, improvement_text):
    log_file = os.path.join(LOG_DIR, f"log_{counter}.txt")
    with open(log_file, "w") as f:
        f.write(improvement_text)

def main():
    ensure_files()
    counter = increment_counter()
    current_code = read_example()
    previous_log = last_log_content()

    prompt = f"""
You are an AI code assistant.
Analyze this Python code and improve it intelligently.
Use previous log notes to continue improvement without repeating the same changes.
Return full improved Python code and a summary of:
1. Improvements done
2. Next improvements to consider

Previous log (if any):
{previous_log}

Current code:
{current_code}
"""

    try:
        response = call_openrouter(prompt)
        new_code = response['choices'][0]['message']['content']

        # Split the response dynamically: last line can contain next steps
        # For simplicity, we log the entire response as dynamic thoughts
        write_example(new_code)
        write_log(counter, response['choices'][0]['message']['content'])

        print(f"Run {counter} complete. example.py updated.")
    except Exception as e:
        print(f"Brain run failed: {e}")

if __name__ == "__main__":
    main()
