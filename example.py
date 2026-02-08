# ARAS - A Really Awesome System 🤖

def aras():
    print("👋 Hello! I am ARAS (A Really Awesome System).")
    name = ""

    while True:
        user = input("You: ").lower()

        if user in ["hi", "hello", "hey"]:
            print("ARAS: Hello there! 😊")

        elif "your name" in user:
            print("ARAS: My name is ARAS.")

        elif "my name is" in user:
            name = user.replace("my name is", "").strip().title()
            print(f"ARAS: Nice to meet you, {name}!")

        elif "who am i" in user:
            if name:
                print(f"ARAS: You are {name}.")
            else:
                print("ARAS: I don't know your name yet.")

        elif user in ["bye", "exit", "quit"]:
            print("ARAS: Goodbye! Have a great day 🚀")
            break

        else:
            print("ARAS: I'm still learning. Try something else!")

# Start ARAS
aras()
