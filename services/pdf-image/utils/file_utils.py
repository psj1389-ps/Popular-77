import os

def ensure_dirs(paths):
    for p in paths:
        os.makedirs(p, exist_ok=True)

def parse_pages(spec: str | None, total_pages: int):
    if not spec:
        return list(range(1, total_pages + 1))
    pages = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            a, b = int(a), int(b)
            pages.update(range(min(a, b), max(a, b) + 1))
        else:
            pages.add(int(part))
    return sorted([p for p in pages if 1 <= p <= total_pages])