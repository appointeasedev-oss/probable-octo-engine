from pathlib import Path

file_path = Path("counter.txt")

# Ensure file exists
if not file_path.exists():
    file_path.write_text("0")

# Read current value
current = int(file_path.read_text().strip())

# Increment
current += 1

# Write back
file_path.write_text(str(current))

print(f"[probable-octo-engine] Counter updated to {current}")

