import os
import random
import requests

EXAMPLE_FILE = "example.py"
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

def parse_previous_logs():
    """Extract all previous improvements to avoid repeats"""
    improvements_done = set()
    if not os.path.exists(LOG_DIR):
        return improvements_done
    logs = sorted(os.listdir(LOG_DIR))
    for log_file in logs:
        with open(os.path.join(LOG_DIR, log_file), "r") as f:
            for line in f:
                if line.startswith("Improvement:"):
                    improvements_done.add(line.strip())
    return improvements_done

def write_log(counter, content):
    log_file = os.path.join(LOG_DIR, f"log_{counter}.txt")
    with open(log_file, "w") as f:
        f.write(content)

# -------- Brain Logic --------
def main():
    ensure_files()
    counter = increment_counter()
    current_code = read_example()
    previous_improvements = parse_previous_logs()

    prompt = f"""
You are an AI assistant improving Python code.
Current code:
{current_code}

Previous improvements (do not repeat):
{previous_improvements}

Return full improved Python code, and at the end include a summary:
- Improvements done
- Next improvements to consider
"""

    try:
        response = call_openrouter(prompt)
        new_code = response['choices'][0]['message']['content']

        write_example(new_code)
        write_log(counter, new_code)

        print(f"Run {counter} complete. example.py updated.")
    except Exception as e:
        print(f"Brain run failed: {e}")

if __name__ == "__main__":
    main()
