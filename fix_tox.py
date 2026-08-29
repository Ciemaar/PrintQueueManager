with open("pyproject.toml", "r") as f:
    text = f.read()

text = text.replace("runner = uv-venv-lock-runner", "")

with open("pyproject.toml", "w") as f:
    f.write(text)
