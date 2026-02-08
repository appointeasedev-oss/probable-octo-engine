import os
import json
import shutil
import subprocess
import time
from pathlib import Path
from datetime import datetime
import random
import difflib

# ---------------- CONFIG ----------------
ARAS_FOLDER = "ARAS"
LOG_DIR = os.path.join(ARAS_FOLDER, "logs")
TEST_LOG_DIR = os.path.join(ARAS_FOLDER, "tests")
BACKUP_DIR = os.path.join(ARAS_FOLDER, "backups")
DATA_DIR = os.path.join(ARAS_FOLDER, "data")
PROJECT_PLAN_FILE = os.path.join(ARAS_FOLDER, "project_plan.json")
METRICS_FILE = os.path.join(ARAS_FOLDER, "metrics.json")
COUNTER_FILE = os.path.join(ARAS_FOLDER, "counter.txt")
ARAS_MAIN_FILE = os.path.join(ARAS_FOLDER, "main.py")
MAX_PREV_IMPROVEMENTS = 5

# ---------------- HELPERS ----------------
def ensure_folders():
    for folder in [ARAS_FOLDER, LOG_DIR, TEST_LOG_DIR, BACKUP_DIR, DATA_DIR]:
        os.makedirs(folder, exist_ok=True)
    for file, default in [
        (COUNTER_FILE, "0"),
        (PROJECT_PLAN_FILE, json.dumps({"modules": {}, "next_tasks": []}, indent=2)),
        (METRICS_FILE, json.dumps({}, indent=2)),
        (ARAS_MAIN_FILE, "# ARAS main entry point\nprint('ARAS started')\n")
    ]:
        if not os.path.exists(file):
            with open(file, "w", encoding="utf-8") as f:
                f.write(default)

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
        timestamp = int(time.time())
        shutil.copy2(path, os.path.join(BACKUP_DIR, f"{os.path.basename(path)}_{timestamp}"))

def read_counter():
    with open(COUNTER_FILE, "r", encoding="utf-8") as f:
        val = f.read().strip()
        return int(val) if val.isdigit() else 0

def increment_counter():
    count = read_counter() + 1
    write_file(COUNTER_FILE, str(count))
    return count

def write_log(file_path, summary):
    counter = read_counter()
    log_file = os.path.join(LOG_DIR, f"log_{counter}.txt")
    with open(log_file, "w", encoding="utf-8") as f:
        f.write(f"[{datetime.now()}] - File: {file_path}\n{summary}\n")

def update_metrics(file_path, success=True):
    metrics = {}
    if os.path.exists(METRICS_FILE):
        try:
            content = read_file(METRICS_FILE).strip()
            if content:
                metrics = json.loads(content)
        except:
            metrics = {}
    file_metrics = metrics.get(file_path, {"improvements":0,"failures":0})
    if success:
        file_metrics["improvements"] += 1
    else:
        file_metrics["failures"] += 1
    metrics[file_path] = file_metrics
    write_file(METRICS_FILE, json.dumps(metrics, indent=2))

# ---------------- ARAS SELF-IMPROVEMENT ----------------
def analyze_code_dependencies(file_path):
    """Find imports and potential related files."""
    code = read_file(file_path)
    deps = []
    for line in code.splitlines():
        line = line.strip()
        if line.startswith("import "):
            deps.append(line.split()[1] + ".py")
        elif line.startswith("from "):
            parts = line.split()
            if len(parts) > 1:
                deps.append(parts[1].replace(".","/") + ".py")
    return deps

def plan_improvement(file_path):
    """Decide what to improve in file and optionally related files."""
    improvements = []
    deps = analyze_code_dependencies(file_path)
    improvements.append(f"Refactor {os.path.basename(file_path)} for clarity and structure")
    for dep in deps:
        dep_path = os.path.join(ARAS_FOLDER, dep)
        if os.path.exists(dep_path):
            improvements.append(f"Check related file {dep}")
    return improvements

def edit_file(file_path, improvement_summary):
    """Make simple safe improvements: add comments, structure, logging"""
    code = read_file(file_path)
    new_code = "# Auto-improved by ARAS Brain\n" + code
    new_code += f"\n# Improvement log: {improvement_summary}\n"
    write_file(file_path, new_code)
    write_log(file_path, improvement_summary)
    update_metrics(file_path, success=True)

def improve_aras():
    """Main ARAS improvement cycle"""
    all_files = [ARAS_MAIN_FILE]
    # Optionally find other .py files in ARAS
    for root, _, files in os.walk(ARAS_FOLDER):
        for f in files:
            if f.endswith(".py") and os.path.join(root,f) not in all_files:
                all_files.append(os.path.join(root,f))
    # Improve one file per run
    for file_path in all_files:
        backup_file(file_path)
        improvements = plan_improvement(file_path)
        if improvements:
            edit_file(file_path, "; ".join(improvements))
            break

# ---------------- ARAS CONVERSATION SIMULATION ----------------
def simulate_aras_conversation():
    test_file = os.path.join(TEST_LOG_DIR, "conversation.json")
    conversation = []
    if os.path.exists(test_file):
        try:
            conversation = json.load(open(test_file,"r",encoding="utf-8"))
        except:
            conversation = []
    counter = read_counter()
    user_msg = f"Hello ARAS, test run {counter}"
    # simulate ARAS reply (basic echo)
    reply = f"ARAS received: {user_msg}"
    conversation.append({"user": user_msg, "aras": reply})
    write_file(test_file, json.dumps(conversation, indent=2))
    print(f"ARAS conversation simulated. Last reply: {reply}")

# ---------------- MAIN BRAIN ----------------
def main():
    ensure_folders()
    increment_counter()
    improve_aras()
    simulate_aras_conversation()
    print(f"Brain run complete. Counter: {read_counter()}")

if __name__ == "__main__":
    main()
