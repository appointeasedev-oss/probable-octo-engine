# ARAS - A Really Awesome System 🤖
import argparse
import datetime
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

RESPONSES_PATH = Path("ARAS/responses.json")
VERIFY_CASES_PATH = Path("ARAS/verify_cases.json")

DEFAULT_RESPONSES = {
    "greeting": [
        "Hello there! 😊",
        "Hi! How can I help you today? 😊",
        "Hey! What's up? 😊",
    ],
    "name_introduction": [
        "My name is ARAS.",
        "I'm ARAS, nice to meet you!",
        "You can call me ARAS.",
    ],
    "unknown": [
        "I'm still learning. Try something else!",
        "I'm not sure about that yet. Can you ask something else?",
        "Hmm, I don't know about that yet.",
    ],
    "farewell": [
        "Goodbye! Have a great day 🚀",
    ],
}

DEFAULT_VERIFY_CASES = [
    {
        "input": "hi",
        "expected_contains": "Hello",
    },
    {
        "input": "what's your name",
        "expected_contains": "ARAS",
    },
    {
        "input": "time",
        "expected_contains": "current time",
    },
]

SELF_HARM_PHRASES = [
    "suicide",
    "kill myself",
    "end my life",
    "self harm",
    "self-harm",
    "hurt myself",
]


def load_json_file(path: Path, default: Dict) -> Dict:
    if path.exists():
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(default, handle, indent=2)
    return default


def load_responses() -> Dict[str, List[str]]:
    return load_json_file(RESPONSES_PATH, DEFAULT_RESPONSES)


def load_verify_cases() -> List[Dict[str, str]]:
    cases = load_json_file(VERIFY_CASES_PATH, {"cases": DEFAULT_VERIFY_CASES})
    return cases.get("cases", DEFAULT_VERIFY_CASES)


def normalize_text(text: str) -> str:
    return text.strip().lower()


def is_self_harm_related(text: str) -> bool:
    return any(phrase in text for phrase in SELF_HARM_PHRASES)


def get_self_harm_response() -> str:
    return (
        "I'm really sorry you're feeling this way. You deserve support, and "
        "I can't help with self-harm, but I can listen. If you feel at risk, "
        "please reach out to someone you trust or a local support line in your country."
    )


def extract_name(text: str) -> Optional[str]:
    match = re.search(r"my name is (\w+)", text, re.IGNORECASE)
    return match.group(1).title() if match else None


def get_time_response() -> str:
    current_time = datetime.datetime.now().strftime("%H:%M")
    return f"The current time is {current_time}."


def generate_response(user_text: str, state: Dict[str, str], responses: Dict[str, List[str]]) -> Tuple[str, Dict[str, str]]:
    if is_self_harm_related(user_text):
        return get_self_harm_response(), state

    if any(word in user_text for word in ["hi", "hello", "hey", "greetings", "howdy"]):
        return responses["greeting"][0], state

    if any(phrase in user_text for phrase in ["your name", "who are you", "what's your name"]):
        return responses["name_introduction"][0], state

    if (extracted_name := extract_name(user_text)) is not None:
        state["name"] = extracted_name
        return f"Nice to meet you, {extracted_name}!", state

    if any(phrase in user_text for phrase in ["who am i", "what's my name", "do you know my name"]):
        if state.get("name"):
            return f"You are {state['name']}.", state
        return "I don't know your name yet.", state

    if any(phrase in user_text for phrase in ["bye", "exit", "quit", "goodbye"]):
        return responses["farewell"][0], state

    if "time" in user_text:
        return get_time_response(), state

    return responses["unknown"][0], state


def run_chat() -> None:
    print("👋 Hello! I am ARAS (A Really Awesome System).")
    state = {"name": ""}
    responses = load_responses()

    while True:
        user_input = input("You: ").strip()
        if not user_input:
            print("ARAS: Please type something.")
            continue

        user_text = normalize_text(user_input)
        response, state = generate_response(user_text, state, responses)
        print(f"ARAS: {response}")
        if response == responses["farewell"][0]:
            break


def run_verify() -> int:
    responses = load_responses()
    cases = load_verify_cases()
    state = {"name": ""}
    failures = []

    for case in cases:
        response, state = generate_response(normalize_text(case["input"]), state, responses)
        expected = case["expected_contains"].lower()
        if expected not in response.lower():
            failures.append((case["input"], response, case["expected_contains"]))

    if failures:
        print("Verification failed:")
        for user_input, response, expected in failures:
            print(f"- Input: {user_input!r} | Response: {response!r} | Expected: {expected!r}")
        return 1

    print("Verification passed.")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the ARAS assistant.")
    parser.add_argument("--verify", action="store_true", help="Run verification checks and exit.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.verify:
        return run_verify()
    run_chat()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
