# package_init.py
import os

def ensure_init(path: str):
    """
    Ensures that 'path' exists and contains an __init__.py file.
    This allows Python to treat it as a package.
    """
    if not os.path.exists(path):
        os.makedirs(path)

    init_file = os.path.join(path, "__init__.py")
    if not os.path.isfile(init_file):
        with open(init_file, "w", encoding="utf-8") as f:
            f.write("# Auto-created to make this directory a Python package.\n")
