import os

def ensure_dirs(paths):
    for p in paths:
        os.makedirs(p, exist_ok=True)