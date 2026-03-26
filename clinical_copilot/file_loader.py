import os
from pathlib import Path
from typing import List


def get_data_dir() -> Path:
    raw = os.getenv("DATA_DIR", "")
    if raw:
        return Path(raw)
    return Path.home() / "Desktop" / "autonomize_demo_data"


def get_available_files() -> List[str]:
    data_dir = get_data_dir()
    if not data_dir.exists():
        return []
    files = []
    for f in sorted(data_dir.iterdir()):
        if f.suffix.lower() in (".txt", ".wav"):
            files.append(f.name)
    return files


def read_text_file(filename: str) -> str:
    path = get_data_dir() / filename
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


def file_path(filename: str) -> Path:
    return get_data_dir() / filename
