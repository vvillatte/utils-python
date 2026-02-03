import sys
import tomllib
import tomli_w
from pathlib import Path

pyproject_path = Path("pyproject.toml")

if len(sys.argv) < 2:
    print("Usage: set_package.py <package> | all")
    sys.exit(1)

target = sys.argv[1]
data = tomllib.loads(pyproject_path.read_text())

# --- Read original project name from [project] ---
original_name = data["project"]["name"]

# --- Modify packages section under [tool.poetry] ---
if target == "all":
    # Keep original packages list
    pass
else:
    data["tool"]["poetry"]["packages"] = [
        {"include": target, "from": "src"}
    ]

# --- Modify project name for individual builds ---
if target == "all":
    new_name = original_name
else:
    # Convert snake_case to kebab-case for wheel name
    new_name = target.replace("_", "-")

data["project"]["name"] = new_name

# --- Write updated pyproject.toml ---
pyproject_path.write_text(tomli_w.dumps(data))