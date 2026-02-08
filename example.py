```python
# ARAS - A Really Awesome System 🤖
import random
import datetime
import re
import string
import os
from typing import Optional, List, Dict

# Helper functions for better modularity and testability
def is_greeting(text: str) -> bool:
    greetings = ["hi", "hello", "hey", "greetings", "howdy"]
    return re.search(r'\b(' + '|'.join(greetings) + r')\b', text) is not None

def is_farewell(text: str) -> bool:
    farewells = ["bye", "exit", "quit", "goodbye", "see you"]
    return re.search(r'\b(' + '|'.join(farewells) + r')\b', text) is not None

def extract_name(text: str) -> Optional[str]:
    match = re.search(r'my name is (\w+)', text, re.IGNORECASE)
    return match.group(1).title() if match else None

def contains_any(text: str, phrases: List[str]) -> bool:
    return any(q.lower() in text for q in phrases)

def contains_all(text: str, phrases: List[str]) -> bool:
    return all(q.lower() in text for q in phrases)

# Predefined responses
responses = {
    "greeting": [
        "Hello there! 😊",
        "Hi! How can I help you today? 😊",
        "Hey! What's up? 😊"
    ],
    "name_introduction": [
        "My name is ARAS.",
        "I'm ARAS, nice to meet you!",
        "You can call me ARAS."
    ],
    "unknown": [
        "I'm still learning. Try something else!",
        "I'm not sure about that. Can you ask something else?",
        "Hmm, I don't know about that yet."
    ]
}

# Load the AI model
def load_model() -> Optional:
    try:
        from transformers import pipeline
        model = pipeline("conversational", model="microsoft/DialoGPT-medium")
        return model
    except ImportError:
        print("Warning: transformers library not found. AI features will be disabled.")
        return None

def get_time_response() -> str:
    current_time = datetime.datetime.now().strftime("%H:%M")
    return f"ARAS: The current time is {current_time}."

def get_name_response(name: str) -> str:
    return f"ARAS: You are {name}." if name else "ARAS: I don't know your name yet."

def aras():
    print("👋 Hello! I am ARAS (A Really Awesome System).")
    name = ""
    model = load_model()

    if model:
        conversation: List[Dict[str, str]] = []
        print("ARAS: AI mode enabled! I can now have more natural conversations.")
    else:
        conversation = None

    while True:
        user_input = input("You: ").strip()
        if not user_input:
            print("ARAS: Please type something.")
            continue

        user_text = user_input.lower()

        # AI-powered conversation (if model available)
        if model and conversation is not None:
            conversation.append({"role": "user", "content": user_input})
            response = model(conversation, max_length=100, pad_token_id=1)
            bot_response = response[0]['generated_text']
            print(f"ARAS: {bot_response}")
            conversation.append({"role": "assistant", "content": bot_response})
            continue

        # Greeting detection
        if is_greeting(user_text):
            print(f"ARAS: {random.choice(responses['greeting'])}")

        # Name introduction
        elif contains_any(user_text, ["your name", "who are you", "what's your name"]):
            print(f"ARAS: {random.choice(responses['name_introduction'])}")

        # Name extraction
        elif (extracted_name := extract_name(user_input)) is not None:
            name = extracted_name
            print(f"ARAS: Nice to meet you, {name}!")

        # Identity questions
        elif contains_any(user_text, ["who am i", "what's my name", "do you know my name"]):
            print(get_name_response(name))

        # Farewell
        elif is_farewell(user_text):
            print("ARAS: Goodbye! Have a great day 🚀")
            break

        # Time query
        elif "time" in user_text:
            print(get_time_response())

        # Default response
        else:
            print(f"ARAS: {random.choice(responses['unknown'])}")

# Start ARAS
if __name__ == "__main__":
    aras()
```