import os
import io
import urllib.parse
import tempfile
import shutil
import zipfile
import logging
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import fitz
from PIL import Image

app = Flask(__name__)
CORS(app, resources={r"/*": {
    "origins": [
        "http://localhost:5173",
        "https://77-tools.xyz",
        "https://www.77-tools.xyz", 
        "https://popular-77.vercel.app"
    ],
    "expose_headers": ["Content-Disposition"]
}})

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(OUTPUTS_DIR, exist_ok=True)

executor = ThreadPoolExecutor(max_workers=2)
JOBS = {}

def send_download_memory(path, download_name, ctype):
    """Send file from memory with proper headers"""
    with open(path, "rb") as f:
        data = f.read()
    resp = send_file(
        io.BytesIO(data), 
        mimetype=ctype, 
        as_attachment=True, 
        download_name=download_name, 
        conditional=False
    )
    resp.direct_passthrough = False
    resp.headers["Content-Length"] = str(len(data))
    resp.headers["Cache-Control"] = "no-store"
    resp.headers["Content-Disposition"] = f"attachment; filename*=UTF-8''{urllib.parse.quote(download_name)}"
    return resp

def pix_to_rgba(pix: fitz.Pixmap) -> Image.Image:
    """Convert fitz.Pixmap to PIL RGBA Image"""
    mode = "RGBA" if pix.alpha else "RGB"
    img = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
    return img if mode == "RGBA" else img.convert("RGBA")

def remove_white_to_alpha(rgba: Image.Image, white_threshold: int = 250) -> Image.Image:
    """Convert white/light areas to transparent"""
    gray = rgba.convert("L")
    # Bright areas (paper) become transparent (0), others stay opaque (255)
    alpha_mask = gray.point(lambda p: 0 if p >= white_threshold else 255)
    out = rgba.copy()
    out.putalpha(alpha_mask)
    return out

def perform_png_conversion(in_path: str, base_name: str, scale: float = 1.0, transparent: int = 0, white_threshold: int = 250):
    """Convert PDF to PNG with optional transparency"""
    try:
        with tempfile.TemporaryDirectory(dir=OUTPUTS_DIR) as tmp:
            doc = fitz.open(in_path)
            mat = fitz.Matrix(scale, scale)
            paths = []
            
            for i in range(doc.page_count):
                page = doc.load_page(i)
                # Render with alpha channel for transparency support
                pix = page.get_pixmap(matrix=mat, alpha=True)
                rgba = pix_to_rgba(pix)
                
                if transparent:
                    rgba = remove_white_to_alpha(rgba, white_threshold=white_threshold)
                
                out_path = os.path.join(tmp, f"{base_name}_{i+1:02d}.png")
                rgba.save(out_path, format="PNG", optimize=True)
                paths.append(out_path)
            
            doc.close()
            
            if len(paths) == 1:
                # Single page - return PNG file
                final_name = f"{base_name}.png"
                final_path = os.path.join(OUTPUTS_DIR, final_name)
                if os.path.exists(final_path):
                    os.remove(final_path)
                shutil.move(paths[0], final_path)
                return final_path, final_name, "image/png"
            else:
                # Multiple pages - return ZIP file
                final_name = f"{base_name}.zip"
                final_path = os.path.join(OUTPUTS_DIR, final_name)
                if os.path.exists(final_path):
                    os.remove(final_path)
                with zipfile.ZipFile(final_path, "w", zipfile.ZIP_DEFLATED) as zf:
                    for p in paths:
                        zf.write(p, arcname=os.path.basename(p))
                return final_path, final_name, "application/zip"
                
    except Exception as e:
        logger.error(f"PNG conversion error: {str(e)}")
        raise

def clamp_num(v, lo, hi, default, T=float):
    """Clamp numeric value within range"""
    try:
        x = T(v)
    except:
        return default
    return max(lo, min(hi, x))

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "pdf-png"})

@app.route("/convert-async", methods=["POST"])
def convert_async():
    """Start async PNG conversion"""
    f = request.files.get("file") or request.files.get("pdfFile")
    if not f:
        return jsonify({"error": "file field is required"}), 400
    
    job_id = uuid4().hex
    in_path = os.path.join(UPLOADS_DIR, f"{job_id}.pdf")
    f.save(in_path)
    
    # Parse parameters
    scale = clamp_num(request.form.get("scale", "1.0"), 0.2, 2.0, 1.0, float)
    transparent = clamp_num(request.form.get("transparent", "0"), 0, 1, 0, int)
    white_threshold = clamp_num(request.form.get("white_threshold", "250"), 200, 255, 250, int)
    
    base_name = f.filename.rsplit('.', 1)[0] if '.' in f.filename else f.filename
    
    # Start conversion job
    JOBS[job_id] = {"status": "processing", "progress": 0}
    
    def conversion_task():
        try:
            JOBS[job_id]["progress"] = 50
            final_path, final_name, content_type = perform_png_conversion(
                in_path, base_name, scale, transparent, white_threshold
            )
            JOBS[job_id].update({
                "status": "completed",
                "progress": 100,
                "output_path": final_path,
                "filename": final_name,
                "content_type": content_type
            })
        except Exception as e:
            logger.error(f"Conversion failed for job {job_id}: {str(e)}")
            JOBS[job_id].update({
                "status": "failed",
                "error": str(e)
            })
        finally:
            # Cleanup input file
            if os.path.exists(in_path):
                os.remove(in_path)
    
    executor.submit(conversion_task)
    return jsonify({"job_id": job_id})

@app.route("/job/<job_id>", methods=["GET"])
def get_job_status(job_id):
    """Get job status"""
    if job_id not in JOBS:
        return jsonify({"error": "Job not found"}), 404
    
    job = JOBS[job_id].copy()
    # Don't expose internal paths
    if "output_path" in job:
        del job["output_path"]
    
    return jsonify(job)

@app.route("/download/<job_id>", methods=["GET"])
def download_result(job_id):
    """Download conversion result"""
    if job_id not in JOBS:
        return jsonify({"error": "Job not found"}), 404
    
    job = JOBS[job_id]
    if job["status"] != "completed":
        return jsonify({"error": "Job not completed"}), 400
    
    output_path = job["output_path"]
    if not os.path.exists(output_path):
        return jsonify({"error": "Output file not found"}), 404
    
    try:
        return send_download_memory(
            output_path,
            job["filename"],
            job["content_type"]
        )
    finally:
        # Cleanup after download
        if os.path.exists(output_path):
            os.remove(output_path)
        del JOBS[job_id]

@app.route("/convert", methods=["POST"])
def convert_sync():
    """Synchronous PNG conversion for compatibility"""
    f = request.files.get("file") or request.files.get("pdfFile")
    if not f:
        return jsonify({"error": "file field is required"}), 400
    
    # Parse parameters
    scale = clamp_num(request.form.get("scale", "1.0"), 0.2, 2.0, 1.0, float)
    transparent = clamp_num(request.form.get("transparent", "0"), 0, 1, 0, int)
    white_threshold = clamp_num(request.form.get("white_threshold", "250"), 200, 255, 250, int)
    
    base_name = f.filename.rsplit('.', 1)[0] if '.' in f.filename else f.filename
    
    # Save input file
    job_id = uuid4().hex
    in_path = os.path.join(UPLOADS_DIR, f"{job_id}.pdf")
    f.save(in_path)
    
    try:
        final_path, final_name, content_type = perform_png_conversion(
            in_path, base_name, scale, transparent, white_threshold
        )
        
        return send_download_memory(final_path, final_name, content_type)
        
    except Exception as e:
        logger.error(f"Sync conversion failed: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        # Cleanup
        if os.path.exists(in_path):
            os.remove(in_path)
        if 'final_path' in locals() and os.path.exists(final_path):
            os.remove(final_path)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)