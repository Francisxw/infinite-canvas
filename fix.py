# Read as binary to preserve line endings
with open("app/routers/comfy.py", "rb") as f:
    content = f.read()

# Decode
text = content.decode("utf-8")
lines = text.split("\n")

# Fix lines 84-126 (indices 83-125)
indent = " " * 4
for i in range(84, min(127, len(lines))):
    line = lines[i]
    stripped = line.lstrip()
    if stripped:
        # Non-empty: add 4 spaces
        lines[i] = indent + stripped
    elif i > 84 and i < 126:
        # Empty line inside with block
        lines[i] = indent

# Join and write back with Windows line endings
new_text = "\n".join(lines)
with open("app/routers/comfy.py", "wb") as f:
    f.write(new_text.encode("utf-8"))
print("Done")
