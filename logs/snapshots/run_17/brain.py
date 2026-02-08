# Brain metadata: last_run=2026-02-08T16:08:33.534492
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List

ARAS_DIR = Path("ARAS")
RESPONSES_PATH = ARAS_DIR / "responses.json"
VERIFY_CASES_PATH = ARAS_DIR / "verify_cases.json"
SKILLS_PATH = ARAS_DIR / "skills" / "notes.json"
LOG_DIR = Path("logs")
SNAPSHOT_DIR = LOG_DIR / "snapshots"
STATE_PATH = LOG_DIR / "brain_state.json"
RUN_LOG_PATH = LOG_DIR / "run_logs.json"
COUNTER_FILE = Path("counter.txt")
DOCS_DIR = Path("docs")
DOCS_DATA_PATH = DOCS_DIR / "data.json"

BRAIN_METADATA_PREFIX = "# Brain metadata:"


@dataclass
class Improvement:
    identifier: str
    kind: str
    payload: Dict[str, str]


IMPROVEMENT_QUEUE: List[Improvement] = [
    Improvement(
        identifier="add_greeting_variant",
        kind="response_variant",
        payload={
            "category": "greeting",
            "text": "Hello! I'm here to help you today. 😊",
        },
    ),
    Improvement(
        identifier="add_unknown_variant",
        kind="response_variant",
        payload={
            "category": "unknown",
            "text": "I'm still learning that topic. Want to try another question?",
        },
    ),
    Improvement(
        identifier="add_verify_case",
        kind="verify_case",
        payload={
            "input": "bye",
            "expected_contains": "Goodbye",
        },
    ),
    Improvement(
        identifier="add_skill_note",
        kind="skill_note",
        payload={
            "title": "Conversation memory",
            "body": "Track basic session memory like last topic discussed.",
        },
    ),
    Improvement(
        identifier="add_module_stub",
        kind="new_file",
        payload={
            "relative_path": "ARAS/modules/skills_stub.py",
            "content": (
                "\"\"\"ARAS skill module placeholder.\"\"\"\n\n"
                "def describe() -> str:\n"
                "    return \"Skill module placeholder for future ARAS extensions.\"\n"
            ),
        },
    ),
]


def load_json(path: Path, default):
    if path.exists():
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    return default


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)


def ensure_state() -> Dict[str, int]:
    if not STATE_PATH.exists():
        state = {"next_index": 0, "runs": 0}
        save_json(STATE_PATH, state)
        return state
    return load_json(STATE_PATH, {"next_index": 0, "runs": 0})


def read_counter() -> int:
    if not COUNTER_FILE.exists():
        COUNTER_FILE.write_text("0", encoding="utf-8")
    return int(COUNTER_FILE.read_text(encoding="utf-8").strip())


def increment_counter() -> int:
    count = read_counter() + 1
    COUNTER_FILE.write_text(str(count), encoding="utf-8")
    return count


def snapshot_sources(counter: int) -> Path:
    snapshot_path = SNAPSHOT_DIR / f"run_{counter}"
    if snapshot_path.exists():
        shutil.rmtree(snapshot_path)
    snapshot_path.mkdir(parents=True, exist_ok=True)
    shutil.copy2(Path(__file__), snapshot_path / "brain.py")
    shutil.copytree(ARAS_DIR, snapshot_path / "ARAS")
    return snapshot_path


def update_brain_metadata() -> None:
    brain_path = Path(__file__)
    lines = brain_path.read_text(encoding="utf-8").splitlines()
    timestamp = datetime.utcnow().isoformat()
    updated_lines = []
    replaced = False
    for line in lines:
        if line.startswith(BRAIN_METADATA_PREFIX):
            updated_lines.append(f"{BRAIN_METADATA_PREFIX} last_run={timestamp}")
            replaced = True
        else:
            updated_lines.append(line)
    if not replaced:
        updated_lines.insert(0, f"{BRAIN_METADATA_PREFIX} last_run={timestamp}")
    brain_path.write_text("\n".join(updated_lines) + "\n", encoding="utf-8")


def apply_response_variant(payload: Dict[str, str]) -> str:
    data = load_json(RESPONSES_PATH, {})
    category = payload["category"]
    text = payload["text"]
    data.setdefault(category, [])
    if text not in data[category]:
        data[category].append(text)
        save_json(RESPONSES_PATH, data)
        return f"Added response variant to {category}."
    return f"Response variant already present in {category}."


def apply_verify_case(payload: Dict[str, str]) -> str:
    cases_data = load_json(VERIFY_CASES_PATH, {"cases": []})
    case = {"input": payload["input"], "expected_contains": payload["expected_contains"]}
    if case not in cases_data.get("cases", []):
        cases_data.setdefault("cases", []).append(case)
        save_json(VERIFY_CASES_PATH, cases_data)
        return "Added verification case."
    return "Verification case already present."


def apply_skill_note(payload: Dict[str, str]) -> str:
    notes = load_json(SKILLS_PATH, {"notes": []})
    note = {
        "title": payload["title"],
        "body": payload["body"],
        "timestamp": datetime.utcnow().isoformat(),
    }
    notes.setdefault("notes", []).append(note)
    save_json(SKILLS_PATH, notes)
    return "Added skill note."


def apply_new_file(payload: Dict[str, str]) -> str:
    relative_path = payload["relative_path"]
    content = payload["content"]
    target_path = Path(relative_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    if target_path.exists():
        return f"File already exists at {relative_path}."
    target_path.write_text(content, encoding="utf-8")
    return f"Created new file at {relative_path}."


def apply_improvement(improvement: Improvement) -> str:
    if improvement.kind == "response_variant":
        return apply_response_variant(improvement.payload)
    if improvement.kind == "verify_case":
        return apply_verify_case(improvement.payload)
    if improvement.kind == "skill_note":
        return apply_skill_note(improvement.payload)
    if improvement.kind == "new_file":
        return apply_new_file(improvement.payload)
    return "No improvement applied."


def run_verification() -> Dict[str, str]:
    result = subprocess.run(
        [sys.executable, "ARAS/main.py", "--verify"],
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "success": result.returncode == 0,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def append_run_log(entry: Dict[str, str]) -> None:
    logs = load_json(RUN_LOG_PATH, {"runs": []})
    logs.setdefault("runs", []).append(entry)
    save_json(RUN_LOG_PATH, logs)


def build_dashboard_data() -> None:
    logs = load_json(RUN_LOG_PATH, {"runs": []})
    data = {
        "generated_at": datetime.utcnow().isoformat(),
        "runs": logs.get("runs", []),
    }
    save_json(DOCS_DATA_PATH, data)


def run_brain() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    state = ensure_state()
    counter = increment_counter()
    snapshot_sources(counter)

    improvement = IMPROVEMENT_QUEUE[state["next_index"] % len(IMPROVEMENT_QUEUE)]
    improvement_summary = apply_improvement(improvement)

    update_brain_metadata()

    verification = run_verification()

    state["next_index"] = (state["next_index"] + 1) % len(IMPROVEMENT_QUEUE)
    state["runs"] += 1
    save_json(STATE_PATH, state)

    run_entry = {
        "run_id": counter,
        "timestamp": datetime.utcnow().isoformat(),
        "improvement_id": improvement.identifier,
        "summary": improvement_summary,
        "verification_success": verification["success"],
        "verification_stdout": verification["stdout"],
        "verification_stderr": verification["stderr"],
    }
    append_run_log(run_entry)
    build_dashboard_data()

    print(f"Run {counter} complete: {improvement_summary}")
    print("Verification:", "passed" if verification["success"] else "failed")


def main() -> None:
    if "--build-dashboard" in sys.argv:
        build_dashboard_data()
        print("Dashboard data rebuilt.")
        return
    run_brain()


if __name__ == "__main__":
    main()
