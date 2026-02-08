import os
import random
import requests
import re

EXAMPLE_FILE = "example.py"
LOG_DIR = "logs"
COUNTER_FILE = "counter.txt"

# -------- Config --------
# Environment keys
OPENROUTER_KEYS = [
    os.getenv("OPENROUTER_KEY_1"),
    os.getenv("OPENROUTER_KEY_2"),
    os.getenv("OPENROUTER_KEY_3"),
    os.getenv("OPENROUTER_KEY_4"),
    os.getenv("OPENROUTER_KEY_5"),
]

# List of models to try, in order
MODELS = [
    "openrouter/pony-alpha",
    "stepfun/step-3.5-flash:free",
    "liquid/lfm-2.5-1.2b-thinking:free",
    "openai/gpt-oss-120b:free",
    "z-ai/glm-4.5-air:free",
    "qwen/qwen3-coder:free",
    "tngtech/deepseek-r1t2-chimera:free",
    "deepseek/deepseek-r1-0528:free",
    "google/gemma-3n-e4b-it:free",
    "tngtech/deepseek-r1t-chimera:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "nousresearch/hermes-3-llama-3.1-405b:free",
    "nvidia/nemotron-nano-12b-v2-vl:free"
]

# -------- Helpers --------
def rotate_keys():
    keys = [k for k in OPENROUTER_KEYS if k]
    random.shuffle(keys)
    return keys

def call_model(model_name, prompt):
    """Try all keys for a single model"""
    keys = rotate_keys()
    for key in keys:
        headers = {"Authorization": f"Bearer {key}"}
        data = {
            "model": model_name,
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
                print(f"Model '{model_name}' failed with key ({resp.status_code}), trying next key...")
        except Exception as e:
            print(f"Exception with model '{model_name}': {e}, trying next key...")
    return None  # All keys failed for this model

def call_multi_model(prompt):
    """Try all models in sequence until one succeeds"""
    for model in MODELS:
        print(f"Trying model: {model}")
        response = call_model(model, prompt)
        if response:
            return response
        print(f"Model '{model}' failed, moving to next model...")
    raise RuntimeError("All models and keys failed")

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
        response = call_multi_model(prompt)
        ai_text = response['choices'][0]['message']['content']

        summary_start = ai_text.find("**Summary:**")
        if summary_start != -1:
            new_code = ai_text[:summary_start].strip()
            summary = ai_text[summary_start:].strip()
        else:
            new_code = ai_text
            summary = "**Summary:** No summary provided."

        write_example(new_code)
        write_log(counter, summary)

        print(f"Run {counter} complete. example.py updated. Log saved as log_{counter}.txt")
    except Exception as e:
        print(f"Brain run failed: {e}")

if __name__ == "__main__":
    main()
