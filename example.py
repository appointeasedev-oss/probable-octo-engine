# ARAS - A Really Awesome System 🤖
import random
import datetime
import re
from typing import Optional, List, Dict
import logging
from pathlib import Path
import json
import sqlite3
from transformers import pipeline, Conversation

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Helper functions for better modularity and testability
def is_greeting(text: str) -> bool:
    greetings = ["hi", "hello", "hey", "greetings", "howdy"]
    return re.search(r'\b(' + '|'.join(greetings) + r')\b', text, re.IGNORECASE) is not None

def is_farewell(text: str) -> bool:
    farewells = ["bye", "exit", "quit", "goodbye", "see you"]
    return re.search(r'\b(' + '|'.join(farewells) + r')\b', text, re.IGNORECASE) is not None

def extract_name(text: str) -> Optional[str]:
    match = re.search(r'my name is (\w+)', text, re.IGNORECASE)
    return match.group(1).title() if match else None

def contains_any(text: str, phrases: List[str]) -> bool:
    return any(q.lower() in text for q in phrases)

def is_self_harm_related(text: str) -> bool:
    self_harm_phrases = [
        "suicide",
        "kill myself",
        "end my life",
        "self harm",
        "self-harm",
        "hurt myself",
    ]
    return contains_any(text, self_harm_phrases)

def get_self_harm_response() -> str:
    return (
        "ARAS: I'm really sorry you're feeling this way. You deserve support, and "
        "I can't help with self-harm, but I can listen. If you feel at risk, please "
        "reach out to someone you trust or a local support line in your country."
    )

# Load configuration for customizable responses
def load_config() -> Dict:
    config_path = Path("aras_config.json")
    if config_path.exists():
        with open(config_path, 'r') as f:
            return json.load(f)
    return {
        "responses": {
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
    }

# Predefined responses from config
config = load_config()
responses = config['responses']

# Load the AI model with fallback
def load_model() -> Optional:
    try:
        model = pipeline("conversational", model="microsoft/DialoGPT-medium")
        return model
    except ImportError:
        logging.warning("transformers library not found. AI features will be disabled.")
        return None

def get_time_response() -> str:
    current_time = datetime.datetime.now().strftime("%H:%M")
    return f"ARAS: The current time is {current_time}."

def get_name_response(name: str) -> str:
    return f"ARAS: You are {name}." if name else "ARAS: I don't know your name yet."

# Improved ARAS with better conversation handling
def aras():
    print("👋 Hello! I am ARAS (A Really Awesome System).")
    name = ""
    model = load_model()

    # Initialize database for persistent memory
    conn = sqlite3.connect('aras_memory.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_input TEXT,
            bot_response TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()

    def save_to_memory(user_input: str, bot_response: str):
        cursor.execute('INSERT INTO memory (user_input, bot_response) VALUES (?, ?)', (user_input, bot_response))
        conn.commit()

    while True:
        user_input = input("You: ").strip()
        if not user_input:
            print("ARAS: Please type something.")
            continue

        user_text = user_input.lower()

        if is_self_harm_related(user_text):
            response = get_self_harm_response()
            print(response)
            save_to_memory(user_input, response)
            continue

        # AI-powered conversation (if model available)
        if model:
            conversation = Conversation(user_input)
            response = model(conversation, max_length=100, pad_token_id=1)
            bot_response = response[0]['generated_text']
            print(f"ARAS: {bot_response}")
            save_to_memory(user_input, bot_response)
            continue

        # Greeting detection
        if is_greeting(user_text):
            response = random.choice(responses['greeting'])
            print(f"ARAS: {response}")
            save_to_memory(user_input, response)

        # Name introduction
        elif contains_any(user_text, ["your name", "who are you", "what's your name"]):
            response = random.choice(responses['name_introduction'])
            print(f"ARAS: {response}")
            save_to_memory(user_input, response)

        # Name extraction
        elif (extracted_name := extract_name(user_input)) is not None:
            name = extracted_name
            response = f"ARAS: Nice to meet you, {name}!"
            print(response)
            save_to_memory(user_input, response)

        # Identity questions
        elif contains_any(user_text, ["who am i", "what's my name", "do you know my name"]):
            response = get_name_response(name)
            print(response)
            save_to_memory(user_input, response)

        # Farewell
        elif is_farewell(user_text):
            print("ARAS: Goodbye! Have a great day 🚀")
            save_to_memory(user_input, "Goodbye! Have a great day 🚀")
            break

        # Time query
        elif "time" in user_text:
            response = get_time_response()
            print(response)
            save_to_memory(user_input, response)

        # Default response
        else:
            response = random.choice(responses['unknown'])
            print(f"ARAS: {response}")
            save_to_memory(user_input, response)

    conn.close()

# Start ARAS
if __name__ == "__main__":
    aras()
