# Read all lines
with open("app/routers/comfy.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Lines 84-126 (indices 83-125) need proper indentation
# Line 84 (index 83) is "with open..." - this stays at column 0
# Lines 85-126 (indices 84-125) need 4 spaces indentation

for i in range(84, min(127, len(lines))):
    line = lines[i]
    if line.strip():  # Non-empty line
        # Remove any leading whitespace and add 4 spaces
        lines[i] = "    " + line.lstrip()
    else:
        # Empty line - just add 4 spaces to maintain block
        if i > 84 and i < 126:  # Inside the with block
            lines[i] = "    \n"

# Write back
with open("app/routers/comfy.py", "w", encoding="utf-8") as f:
    f.writelines(lines)

print("Fixed")
