import os
import re
import json
import yt_dlp
import subprocess
import base64
from flask import Flask, render_template, request, jsonify, send_file, Response
from werkzeug.utils import secure_filename

app = Flask(__name__)

# 환경변수 설정
UA_DEFAULT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
COOKIES_FILE = os.getenv("YT_COOKIES_FILE")  # /etc/secrets/cookies.txt
USER_AGENT = os.getenv("YT_USER_AGENT", UA_DEFAULT)
MAX_FILE_MB = int(os.getenv("YT_MAX_FILE_MB", "200"))
DEFAULT_FORMAT = os.getenv("YT_FORMAT", "bv*+ba/b[ext=mp4]/b")
MERGE_FORMAT = os.getenv("YT_MERGE", "mp4")
LEGAL_NOTICE_ENABLED = os.getenv("YT_LEGAL_NOTICE_ENABLED", "true").lower() == "true"

# 업로드 및 출력 폴더 설정
if os.environ.get('VERCEL'):
    UPLOAD_FOLDER = '/tmp/uploads'
    OUTPUT_FOLDER = '/tmp/outputs'
else:
    UPLOAD_FOLDER = 'uploads'
    OUTPUT_FOLDER = 'outputs'

# 폴더 생성
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
# 다운로드 중간 파일을 위한 임시 폴더 분리
TEMP_FOLDER = os.path.join(OUTPUT_FOLDER, 'temp')
os.makedirs(TEMP_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

# 허용된 파일 확장자
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_valid_youtube_url(url):
    """YouTube URL 유효성 검사(완화)"""
    url = url.strip().rstrip(',').strip()
    return ('youtube.com' in url) or ('youtu.be' in url)

def extract_video_id(url):
    """YouTube URL에서 비디오 ID 추출"""
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/)([0-9A-Za-z_-]{11})',
        r'(?:v\/|v=|\/videos\/|embed\/|youtu.be\/|\/v\/|watch\?v%3D|watch\?feature=player_embedded&v=|%2Fvideos%2F|embed%2F|youtu.be%2F|%2Fv%2F)([^#\&\?\n]*)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None



def get_video_info(url):
    """YouTube 비디오 정보 가져오기"""
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'cookiefile': COOKIES_FILE,
            'http_headers': {
                'User-Agent': USER_AGENT,
                'Accept-Language': 'en-US,en;q=0.9'
            },
            'sleep_interval': 1,
            'max_sleep_interval': 5,
            'extractor_retries': 3,
            'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
            'geo_bypass': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # 사용 가능한 포맷 정보 추출
            formats = []
            if 'formats' in info:
                for fmt in info['formats']:
                    if fmt.get('vcodec') != 'none' and fmt.get('acodec') != 'none':
                        formats.append({
                            'format_id': fmt.get('format_id'),
                            'ext': fmt.get('ext'),
                            'resolution': fmt.get('resolution', 'N/A'),
                            'fps': fmt.get('fps'),
                            'vcodec': fmt.get('vcodec'),
                            'acodec': fmt.get('acodec'),
                            'filesize': fmt.get('filesize')
                        })
            
            return {
                'title': info.get('title', '알 수 없음'),
                'duration': info.get('duration', 0),
                'view_count': info.get('view_count', 0),
                'uploader': info.get('uploader', '알 수 없음'),
                'description': info.get('description', ''),
                'thumbnail': info.get('thumbnail', ''),
                'formats': formats[:10]  # 처음 10개 포맷만 반환
            }
    except Exception as e:
        print(f"비디오 정보 추출 오류: {str(e)}")
        return None

def download_youtube_video(url, quality='medium', format_type='mp4'):
    """YouTube 비디오 다운로드"""
    try:
        print(f"=== YouTube 다운로드 시작: {url} ===")

        # 품질 설정(현재 포맷 선택식에서 자동 최적화이므로 보류)
        if quality == 'high':
            format_selector = 'best[height<=1080]'
        elif quality == 'medium':
            format_selector = 'best[height<=720]'
        else:
            format_selector = 'best[height<=480]'

        # yt-dlp 옵션 설정: 파일명은 %(id)s.%(ext)s 로 일관 생성
        if format_type == 'mp3':
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': '%(id)s.%(ext)s',
                'noplaylist': True,
                'overwrites': True,
                'nopart': True,
                'paths': {'home': OUTPUT_FOLDER, 'temp': TEMP_FOLDER},
                'cookiefile': COOKIES_FILE,
                'http_headers': {
                    'User-Agent': USER_AGENT,
                    'Accept-Language': 'en-US,en;q=0.9'
                },
                'sleep_interval': 1,
                'max_sleep_interval': 5,
                'extractor_retries': 3,
                'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
                'geo_bypass': True,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                # MP3 튜닝: 라임 코덱 및 품질 설정 (faststart는 MP4에만 적용됨)
                'postprocessor_args': {
                    'extractaudio+ffmpeg_o': ['-codec:a', 'libmp3lame', '-q:a', '2', '-id3v2_version', '3']
                }
            }
        else:
            ydl_opts = {
                'format': DEFAULT_FORMAT,
                'outtmpl': '%(id)s.%(ext)s',
                'noplaylist': True,
                'overwrites': True,
                'nopart': True,
                'paths': {'home': OUTPUT_FOLDER, 'temp': TEMP_FOLDER},
                'merge_output_format': MERGE_FORMAT,
                'cookiefile': COOKIES_FILE,
                'http_headers': {
                    'User-Agent': USER_AGENT,
                    'Accept-Language': 'en-US,en;q=0.9'
                },
                'sleep_interval': 1,
                'max_sleep_interval': 5,
                'extractor_retries': 3,
                'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
                'geo_bypass': True,
                'postprocessors': [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4',
                }, {
                    'key': 'FFmpegMetadata',
                    'add_metadata': True,
                }],
                # FFmpeg 튜닝: H.264 재인코드 + veryfast, AAC 오디오 및 faststart 적용
                'postprocessor_args': {
                    'videoconvertor+ffmpeg_o': ['-c:v', 'libx264', '-preset', 'veryfast', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart'],
                    'videoremuxer+ffmpeg_o': ['-movflags', '+faststart']
                }
            }

        ffmpeg_path = os.path.join(os.path.dirname(__file__), 'ffmpeg', 'ffmpeg-8.0-essentials_build', 'bin', 'ffmpeg.exe')
        if os.path.exists(ffmpeg_path):
            ffmpeg_bin_dir = os.path.join(os.path.dirname(__file__), 'ffmpeg', 'ffmpeg-8.0-essentials_build', 'bin')
            ydl_opts['ffmpeg_location'] = ffmpeg_bin_dir
            print(f"FFmpeg 경로 설정: {ffmpeg_bin_dir}")
        else:
            print(f"FFmpeg를 찾을 수 없습니다: {ffmpeg_path}")

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 비디오 정보 먼저 가져오기
            info = ydl.extract_info(url, download=False)
            video_id = info.get('id')

            # 다운로드 실행
            ydl.download([url])

            # 기대 파일명 결정
            expected_ext = 'mp3' if format_type == 'mp3' else 'mp4'
            expected_file = f"{video_id}.{expected_ext}"
            expected_path = os.path.join(OUTPUT_FOLDER, expected_file)
            if os.path.exists(expected_path):
                file_size = os.path.getsize(expected_path)
                print(f"다운로드 완료: {expected_file} ({file_size:,} bytes)")
                return expected_file, None

            # 폴더 스캔하여 id 기반 파일 찾기(혹시 확장자 상이 시)
            for file in os.listdir(OUTPUT_FOLDER):
                if video_id and video_id in file:
                    if file.endswith('.part'):
                        continue
                    file_path = os.path.join(OUTPUT_FOLDER, file)
                    file_size = os.path.getsize(file_path)
                    print(f"다운로드 완료(스캔): {file} ({file_size:,} bytes)")
                    return file, None

            return None, "다운로드된 파일을 찾을 수 없습니다."

    except Exception as e:
        error_msg = f"다운로드 오류: {str(e)}"
        print(error_msg)
        return None, error_msg

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert_file():
    # 기존 파일 변환 로직 (PDF/이미지)
    pass

@app.route('/download', methods=['POST'])
def download():
    # 기존 다운로드 로직
    pass

@app.route('/download_video', methods=['POST'])
def download_youtube():
    try:
        data = request.get_json()
        
        if not data or 'url' not in data:
            return jsonify({'error': 'YouTube URL이 필요합니다.'}), 400
        
        url = data['url'].strip().rstrip(',').strip()  # URL 정리
        quality = data.get('quality', 'medium')
        format_type = data.get('format', 'mp4')
        
        print(f"다운로드 요청: URL={url}, 품질={quality}, 형식={format_type}")
        
        # URL 유효성 검사
        if not is_valid_youtube_url(url):
            return jsonify({'error': '유효하지 않은 YouTube URL입니다.'}), 400
        
        # 스트리밍 응답 대신 일반 JSON 응답으로 변경 (호환성을 위해)
        filename, error = download_youtube_video(url, quality, format_type)
        
        if error:
            return jsonify({'error': error}), 500
        
        if filename:
            return jsonify({
                'success': True,
                'filename': filename,
                'download_url': f'/download-file/{filename}'
            })
        else:
            return jsonify({'error': '다운로드에 실패했습니다.'}), 500
            
    except Exception as e:
        print(f"다운로드 처리 중 오류: {str(e)}")
        return jsonify({'error': f'서버 오류: {str(e)}'}), 500

@app.route('/get_video_info', methods=['POST'])
def get_video_info_route():
    """비디오 정보만 가져오는 엔드포인트"""
    try:
        data = request.get_json()
        
        if not data or 'url' not in data:
            return jsonify({'error': 'YouTube URL이 필요합니다.'}), 400
        
        url = data['url'].strip().rstrip(',').strip()  # URL 정리
        
        # URL 유효성 검사
        if not is_valid_youtube_url(url):
            return jsonify({'error': '유효하지 않은 YouTube URL입니다.'}), 400
        
        # 비디오 정보 가져오기
        video_info = get_video_info(url)
        if not video_info:
            return jsonify({'error': '비디오 정보를 가져올 수 없습니다.'}), 400
        
        return jsonify({
            'success': True,
            'video_info': video_info
        })
        
    except Exception as e:
        print(f"비디오 정보 조회 중 오류: {str(e)}")
        return jsonify({'error': f'서버 오류: {str(e)}'}), 500

@app.route('/download-file/<filename>')
def download_file(filename):
    """다운로드된 파일 전송 - 스트리밍 방식으로 개선"""
    try:
        # .part 요청이 오면 최종 확장자로 매핑 시도
        if filename.endswith('.part'):
            base = filename[:-5]
            cand_mp4 = base + '.mp4'
            cand_mp3 = base + '.mp3'
            if os.path.exists(os.path.join(OUTPUT_FOLDER, cand_mp4)):
                filename = cand_mp4
            elif os.path.exists(os.path.join(OUTPUT_FOLDER, cand_mp3)):
                filename = cand_mp3
        
        file_path = os.path.join(OUTPUT_FOLDER, filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': '파일을 찾을 수 없습니다.'}), 404
        
        # 스트리밍 방식으로 파일 전송
        def generate():
            with open(file_path, 'rb') as f:
                while True:
                    data = f.read(8192)  # 8KB씩 읽기
                    if not data:
                        break
                    yield data
        
        file_size = os.path.getsize(file_path)
        
        return Response(
            generate(),
            mimetype='application/octet-stream',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Length': str(file_size),
                'Content-Type': 'application/octet-stream'
            }
        )
        
    except Exception as e:
        print(f"파일 전송 중 오류: {e}")
        return jsonify({'error': f'파일 전송 오류: {e}'}), 500

@app.route('/health')
def health_check():
    """헬스체크 엔드포인트"""
    try:
        # ffmpeg 버전 확인
        ffmpeg_result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        ffmpeg_version = ffmpeg_result.stdout.split('\n')[0] if ffmpeg_result.returncode == 0 else "Not available"
        
        # yt-dlp 버전 확인
        ytdlp_version = yt_dlp.version.__version__
        
        # Python 버전 확인
        import sys
        python_version = sys.version
        
        return jsonify({
            "status": "healthy",
            "ffmpeg": ffmpeg_version,
            "yt_dlp": ytdlp_version,
            "python": python_version
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@app.route('/debug-cookies')
def debug_cookies():
    """쿠키 파일 상태 확인 엔드포인트"""
    try:
        p = COOKIES_FILE
        ok = bool(p and os.path.exists(p))
        size = os.path.getsize(p) if ok else 0
        
        return jsonify({
            "has_cookies": ok,
            "path": p,
            "size": size,
            "user_agent": USER_AGENT,
            "format": DEFAULT_FORMAT,
            "merge_format": MERGE_FORMAT,
            "max_file_mb": MAX_FILE_MB
        })
    except Exception as e:
        return jsonify({
            "has_cookies": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)