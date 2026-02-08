```python
# ARAS - A Really Awesome System 🤖
import random
import datetime
import re
import string

# Helper functions for better modularity and testability
def is_greeting(text):
    greetings = ["hi", "hello", "hey", "greetings", "howdy"]
    return re.search(r'\b(' + '|'.join(greetings) + r')\b', text)

def is_farewell(text):
    farewells = ["bye", "exit", "quit", "goodbye", "see you"]
    return re.search(r'\b(' + '|'.join(farewells) + r')\b', text)

def extract_name(text):
    match = re.search(r'my name is (\w+)', text)
    return match.group(1).title() if match else None

def contains_any(text, phrases):
    return any(q in text for q in phrases)

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

def aras():
    print("👋 Hello! I am ARAS (A Really Awesome System).")
    name = ""

    while True:
        user = input("You: ").lower().strip()
        if not user:
            print("ARAS: Please type something.")
            continue

        # Greeting detection
        if is_greeting(user):
            print(f"ARAS: {random.choice(responses['greeting'])}")

        # Name introduction
        elif contains_any(user, ["your name", "who are you", "what's your name"]):
            print(f"ARAS: {random.choice(responses['name_introduction'])}")

        # Name extraction
        elif (extracted_name := extract_name(user)) is not None:
            name = extracted_name
            print(f"ARAS: Nice to meet you, {name}!")

        # Identity questions
        elif contains_any(user, ["who am i", "what's my name", "do you know my name"]):
            if name:
                print(f"ARAS: You are {name}.")
            else:
                print("ARAS: I don't know your name yet.")

        # Farewell
        elif is_farewell(user):
            print("ARAS: Goodbye! Have a great day 🚀")
            break

        # Time query
        elif "time" in user:
            current_time = datetime.datetime.now().strftime("%H:%M")
            print(f"ARAS: The current time is {current_time}.")

        # Default response
        else:
            print(f"ARAS: {random.choice(responses['unknown'])}")

# Start ARAS
if __name__ == "__main__":
    aras()
```