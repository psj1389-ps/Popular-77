import os, io, zipfile

def ensure_dirs(paths):
    for p in paths:
        os.makedirs(p, exist_ok=True)

def zip_paths(paths):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for p in paths:
            z.write(p, arcname=os.path.basename(p))
    buf.seek(0)
    return buf

def parse_pages(spec, total_pages):
    if not spec:
        return list(range(1, total_pages+1))
    s = set()
    for part in spec.split(","):
        part = part.strip()
        if not part: continue
        if "-" in part:
            a,b = part.split("-",1)
            a,b = int(a), int(b)
            s.update(range(min(a,b), max(a,b)+1))
        else:
            s.add(int(part))
    return sorted([p for p in s if 1 <= p <= total_pages])