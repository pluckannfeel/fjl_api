import os

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_directory_path() -> str:
    return str(ROOT_DIR)