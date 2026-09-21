import sys
from pathlib import Path

import tomllib
import tomli_w

PYPROJECT_PATH = Path("pyproject.toml")

if len(sys.argv) < 2:
    print("Usage: set_package.py <package> | all")
    sys.exit(1)

target = sys.argv[1]

with open(PYPROJECT_PATH, "rb") as f:
    data = tomllib.load(f)

packages = data["tool"]["utility_scripts"]["packages"]

# ------------------------------------------------------------------
# Validate package name
# ------------------------------------------------------------------

if target != "all" and target not in packages:
    print(f"Unknown package: {target}")
    print(f"Available packages: {', '.join(sorted(packages.keys()))}")
    sys.exit(1)

# ------------------------------------------------------------------
# Build ALL packages
# ------------------------------------------------------------------

if target == "all":

    all_config = data["tool"]["utility_scripts"]["all"]

    data["project"]["name"] = all_config["name"]

    # --------------------------------------------------------------
    # Restore all package inclusions
    # --------------------------------------------------------------

    data["tool"]["poetry"]["packages"] = [
        {"include": "config_loader", "from": "src"},
        {"include": "logger", "from": "src"},
        ] + [
        {"include": package_name, "from": "src"}
        for package_name in packages.keys()
    ]

    # --------------------------------------------------------------
    # Aggregate dependencies
    # --------------------------------------------------------------

    all_dependencies = set()

    for package_config in packages.values():
        for dependency in package_config.get("dependencies", []):
            all_dependencies.add(dependency)

    data["project"]["dependencies"] = sorted(all_dependencies)

    # --------------------------------------------------------------
    # Aggregate scripts
    # --------------------------------------------------------------

    data["project"]["scripts"] = {}

    for package_config in packages.values():
        data["project"]["scripts"][
            package_config["script_name"]
        ] = package_config["entrypoint"]

# ------------------------------------------------------------------
# Build single package
# ------------------------------------------------------------------

else:

    package_config = packages[target]

    data["project"]["name"] = target.replace("_", "-")

    # --------------------------------------------------------------
    # Package include
    # --------------------------------------------------------------

    data["tool"]["poetry"]["packages"] = [
        {"include": "config_loader", "from": "src"},
        {"include": "logger", "from": "src"},
        {"include": target, "from": "src"},
    ]

    # --------------------------------------------------------------
    # Dependencies
    # --------------------------------------------------------------

    data["project"]["dependencies"] = (
        package_config.get("dependencies", [])
    )

    # --------------------------------------------------------------
    # Single script
    # --------------------------------------------------------------

    data["project"]["scripts"] = {
        package_config["script_name"]:
            package_config["entrypoint"]
    }

# ------------------------------------------------------------------
# Write modified pyproject.toml
# ------------------------------------------------------------------

with open(PYPROJECT_PATH, "wb") as f:
    tomli_w.dump(data, f)

print(f"Prepared package: {target}")