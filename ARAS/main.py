# ARAS AI main entry point
# This is the starting AI that brain will improve automatically

print("ARAS AI started")
print("Hello! I am ARAS, your evolving AI brain.")

# ARAS basic memory
memory = {"conversations": [], "modules": []}

# ARAS simple chat function
def chat(user_input):
    reply = f"ARAS received: {user_input}"
    memory["conversations"].append({"user": user_input, "aras": reply})
    return reply

# Example usage
if __name__ == "__main__":
    print(chat("Hi ARAS"))
