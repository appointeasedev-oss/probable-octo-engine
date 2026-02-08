import os
import random
import requests
import re
import json
import shutil
import subprocess
import difflib
import time
from pathlib import Path
from datetime import datetime

# ---------------- CONFIG ----------------
ARAS_FOLDER = "ARAS"
LOG_DIR = os.path.join(ARAS_FOLDER, "logs")
TEST_LOG_DIR = os.path.join(ARAS_FOLDER, "tests")
BACKUP_DIR = os.path.join(ARAS_FOLDER, "backups")
DATA_DIR = os.path.join(ARAS_FOLDER, "data")
PROJECT_PLAN_FILE = os.path.join(ARAS_FOLDER, "project_plan.json")
METRICS_FILE = os.path.join(ARAS_FOLDER, "metrics.json")
COUNTER_FILE = os.path.join(ARAS_FOLDER, "counter.txt")
BRAIN_FILE = "brain.py"
MAX_PREV_IMPROVEMENTS = 5

OPENROUTER_KEYS = [os.getenv(f"OPENROUTER_KEY_{i}") for i in range(1,6)]

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

# ---------------- HELPERS ----------------
def rotate_keys():
    keys = [k for k in OPENROUTER_KEYS if k]
    random.shuffle(keys)
    return keys

def call_model(model_name, prompt):
    for key in rotate_keys():
        headers = {"Authorization": f"Bearer {key}"}
        data = {"model": model_name, "messages": [{"role": "user", "content": prompt}]}
        try:
            resp = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=60
            )
            if resp.status_code == 200:
                return resp.json()
        except:
            continue
    return None

def call_multi_model(prompt):
    for model in MODELS:
        response = call_model(model, prompt)
        if response:
            return response
    raise RuntimeError("All models and keys failed")

def ensure_folders():
    for folder in [ARAS_FOLDER, LOG_DIR, TEST_LOG_DIR, BACKUP_DIR, DATA_DIR]:
        os.makedirs(folder, exist_ok=True)
    if not os.path.exists(COUNTER_FILE):
        with open(COUNTER_FILE, "w") as f:
            f.write("0")
    if not os.path.exists(PROJECT_PLAN_FILE):
        write_file(PROJECT_PLAN_FILE, json.dumps({"modules": {}, "next_tasks": []}, indent=2))
    if not os.path.exists(METRICS_FILE):
        write_file(METRICS_FILE, json.dumps({}, indent=2))

def read_counter():
    with open(COUNTER_FILE, "r") as f:
        return int(f.read().strip())

def increment_counter():
    count = read_counter() + 1
    with open(COUNTER_FILE, "w") as f:
        f.write(str(count))
    return count

def read_file(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def backup_file(path):
    if os.path.exists(path):
        name = os.path.basename(path)
        timestamp = int(time.time())
        backup_path = os.path.join(BACKUP_DIR, f"{name}_{timestamp}")
        shutil.copy2(path, backup_path)

def parse_previous_logs(file_path):
    improvements = []
    if not os.path.exists(LOG_DIR):
        return improvements
    logs = sorted(os.listdir(LOG_DIR), reverse=True)
    for log_file in logs:
        path = os.path.join(LOG_DIR, log_file)
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
            matches = re.findall(rf"- File: {re.escape(file_path)}; Improvements done: (.+)", text)
            for m in matches:
                improvements.append(m.strip())
                if len(improvements) >= MAX_PREV_IMPROVEMENTS:
                    return improvements
    return improvements

def write_log(counter, file_path, summary):
    log_file = os.path.join(LOG_DIR, f"log_{counter}.txt")
    with open(log_file, "w", encoding="utf-8") as f:
        f.write(f"[{datetime.now()}] - File: {file_path}; {summary}\n")

def get_all_files(folder):
    files = []
    for root, _, filenames in os.walk(folder):
        for f in filenames:
            files.append(os.path.join(root, f))
    return files

# ---------------- PROJECT METRICS ----------------
def update_metrics(file_path, success=True):
    metrics = {}
    if os.path.exists(METRICS_FILE):
        with open(METRICS_FILE, "r", encoding="utf-8") as f:
            metrics = json.load(f)
    file_metrics = metrics.get(file_path, {"improvements":0,"failures":0})
    if success:
        file_metrics["improvements"] +=1
    else:
        file_metrics["failures"] +=1
    metrics[file_path] = file_metrics
    write_file(METRICS_FILE, json.dumps(metrics, indent=2))

# ---------------- ARAS CONVERSATION TEST ----------------
def test_aras_conversation():
    test_file = os.path.join(TEST_LOG_DIR, "conversation.json")
    conversation = []
    if os.path.exists(test_file):
        with open(test_file, "r", encoding="utf-8") as f:
            conversation = json.load(f)
    test_message = f"Test message at run {read_counter()}"
    try:
        response = call_multi_model(f"Simulate ARAS AI conversation. User: {test_message}")
        reply = response['choices'][0]['message']['content']
        conversation.append({"user": test_message, "aras": reply})
        write_file(test_file, json.dumps(conversation, indent=2))
    except:
        reply = "No reply (failed)"
    print(f"ARAS conversation test done. Last reply: {reply}")

# ---------------- BRAIN SELF-IMPROVEMENT ----------------
def improve_brain_safely():
    brain_code = read_file(BRAIN_FILE)
    prev_improvements = parse_previous_logs(BRAIN_FILE)
    prompt = f"""
You are an autonomous AI agent. Your core purpose, keys, and models must never change.
Improve your own code to better achieve your main goal: make ARAS AI the best AI possible.
Only improve if safe.
Current code:
{brain_code}
Last {MAX_PREV_IMPROVEMENTS} improvements:
{prev_improvements}
Return improved code and summary starting with '**Summary:**' if possible.
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
            summary = "**Summary:** No improvement."
        temp_file = BRAIN_FILE.replace(".py","_temp.py")
        write_file(temp_file, new_code)
        try:
            subprocess.check_output(["python","-m","py_compile",temp_file])
            shutil.copy(temp_file,BRAIN_FILE)
            counter = increment_counter()
            write_log(counter,BRAIN_FILE,summary)
            print("Brain self-improvement applied successfully.")
        except subprocess.CalledProcessError:
            print("No safe brain improvement this run, skipping.")
        finally:
            os.remove(temp_file)
    except:
        print("Brain self-improvement skipped due to failure.")

# ---------------- ARAS FILE IMPROVEMENT ----------------
def improve_aras_files():
    counter = increment_counter()
    all_files = get_all_files(ARAS_FOLDER)
    if not all_files:
        main_file = os.path.join(ARAS_FOLDER,"main.py")
        write_file(main_file,"# ARAS AI main entry point\n")
        all_files = [main_file]
    for file_path in all_files:
        backup_file(file_path)
        current_code = read_file(file_path)
        prev_improvements = parse_previous_logs(file_path)
        all_files_paths = get_all_files(ARAS_FOLDER)
        prompt = f"""
You are an autonomous AI agent improving/building ARAS AI project.
Project files: {all_files_paths}
Current file: {file_path}
Current code:
{current_code}
Last {MAX_PREV_IMPROVEMENTS} improvements for this file:
{prev_improvements}

Task:
- Improve this file as part of ARAS AI system.
- Can create new files/subfolders and update existing files.
- Apply one meaningful improvement per run.
- Generate unit tests and update integration tests.
- Update project metrics.
- Return full updated code and summary starting with '**Summary:**'.
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
            write_file(file_path,new_code)
            write_log(counter,file_path,summary)
            update_metrics(file_path,success=True)
            print(f"ARAS updated: {file_path}")
        except Exception as e:
            print(f"Failed to improve {file_path}: {e}")
            update_metrics(file_path,success=False)

# ---------------- MAIN ----------------
def main():
    ensure_folders()
    improve_aras_files()
    improve_brain_safely()
    test_aras_conversation()
    print(f"Run {read_counter()} complete.")

if __name__=="__main__":
    main()
