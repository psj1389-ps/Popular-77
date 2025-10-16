from flask import Flask, request, send_file, jsonify
from werkzeug.utils import secure_filename
import os, io, zipfile

from converters.pdf_to_images import pdf_to_images
from utils.file_utils import ensure_dirs

BASE = os.path.dirname(__file__)
UPLOAD_DIR = os.path.join(BASE, "uploads")
OUTPUT_DIR = os.path.join(BASE, "outputs")

app = Flask(__name__)
ensure_dirs([UPLOAD_DIR, OUTPUT_DIR])

@app.route("/health", methods=["GET", "HEAD"])
def health():
    return jsonify({"ok": True})

def _zip_paths(paths):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for p in paths:
            z.write(p, arcname=os.path.basename(p))
    buf.seek(0)
    return buf

def _flag(v, default=False):
    if v is None:
        return default
    return str(v).strip().lower() in ("1","true","yes","y","on")

@app.route("/api/pdf-to-images", methods=["POST"])
def api_pdf_to_images():
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "file is required"}), 400

    fmt = (request.form.get("format") or "png").lower()    # png|jpg|webp|tiff|bmp|gif
    dpi = int(request.form.get("dpi") or 144)
    quality = request.form.get("quality")                  # 75~100 또는 low/medium/high
    pages_spec = request.form.get("pages")                 # "1-3,5"

    transparent_bg = _flag(request.form.get("transparentBg"), False)
    transparent_color = request.form.get("transparentColor")   # 예: ffffff, #fff
    tolerance = int(request.form.get("tolerance") or 8)
    webp_lossless = _flag(request.form.get("webpLossless"), True)
    white_threshold = int(request.form.get("whiteThreshold") or 250)  # PDF-PNG 방식 밝기 임계값

    name = secure_filename(f.filename)
    in_path = os.path.join(UPLOAD_DIR, name)
    f.save(in_path)

    out_dir = os.path.join(OUTPUT_DIR, os.path.splitext(name)[0])
    os.makedirs(out_dir, exist_ok=True)

    out_files = pdf_to_images(
        in_path, out_dir,
        fmt=fmt, dpi=dpi, quality=quality, pages_spec=pages_spec,
        transparent_bg=transparent_bg, transparent_color=transparent_color,
        tolerance=tolerance, webp_lossless=webp_lossless,
        white_threshold=white_threshold
    )

    if not out_files:
        return jsonify({"error": "no output files generated"}), 500

    # 1개면 단일 파일, 2개 이상이면 ZIP
    if len(out_files) == 1:
        fp = out_files[0]
        resp = send_file(fp, as_attachment=True, download_name=os.path.basename(fp))
        resp.headers["Content-Length"] = str(os.path.getsize(fp))
        return resp

    buf = _zip_paths(out_files)
    buf.seek(0, os.SEEK_END)
    length = buf.tell()
    buf.seek(0)
    resp = send_file(buf, mimetype="application/zip", as_attachment=True,
                     download_name=f"{os.path.splitext(name)[0]}_{fmt}.zip")
    resp.headers["Content-Length"] = str(length)
    return resp

# 호환 라우트: 당신의 테스트 URL대로도 동작합니다.
@app.route("/api/pdf-image/convert_to_images", methods=["POST"])
def compat_convert_to_images():
    return api_pdf_to_images()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)