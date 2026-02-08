import os
import random
import requests
import re

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
    """Extract previous improvements from all logs to avoid repeats"""
    improvements_done = set()
    if not os.path.exists(LOG_DIR):
        return improvements_done
    logs = sorted(os.listdir(LOG_DIR))
    for log_file in logs:
        path = os.path.join(LOG_DIR, log_file)
        with open(path, "r") as f:
            text = f.read()
            # Extract improvements done from previous logs
            matches = re.findall(r"- Improvements done: (.+)", text)
            for m in matches:
                improvements_done.add(m.strip())
    return improvements_done

def write_log(counter, summary):
    log_file = os.path.join(LOG_DIR, f"log_{counter}.txt")
    with open(log_file, "w") as f:
        f.write(summary)

def extract_summary(ai_response):
    """
    Extract only the summary section from the AI response.
    Assumes AI includes '**Summary:**' section.
    """
    text = ai_response['choices'][0]['message']['content']
    summary_index = text.find("**Summary:**")
    if summary_index != -1:
        return text[summary_index:]
    # fallback: return last 20 lines
    return "\n".join(text.splitlines()[-20:])

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

Return the full improved Python code, and include a clear summary section starting with '**Summary:**' listing:
- Improvements done
- Next improvements to consider
"""

    try:
        response = call_openrouter(prompt)
        # Extract improved code and summary
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

        # Save summary in separate log file
        write_log(counter, summary)

        print(f"Run {counter} complete. example.py updated. Log saved as log_{counter}.txt")
    except Exception as e:
        print(f"Brain run failed: {e}")

if __name__ == "__main__":
    main()
