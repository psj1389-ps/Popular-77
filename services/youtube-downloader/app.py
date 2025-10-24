import os
import re
import json
import yt_dlp
import subprocess
import base64
import shutil
import tempfile
import sys
import ssl
from flask import Flask, render_template, request, jsonify, send_file, Response
from werkzeug.utils import secure_filename
from yt_dlp.version import __version__ as YDL_VERSION

app = Flask(__name__)

# 환경변수 설정
UA_WEB_DEFAULT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
UA_ANDROID_DEFAULT = "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"
UA_IOS_DEFAULT = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1"
UA_TV_DEFAULT = UA_WEB_DEFAULT
UA_MWEB_DEFAULT = UA_WEB_DEFAULT

UA_WEB = os.getenv("YT_USER_AGENT_WEB", UA_WEB_DEFAULT)
UA_ANDROID = os.getenv("YT_USER_AGENT_ANDROID", UA_ANDROID_DEFAULT)
UA_IOS = os.getenv("YT_USER_AGENT_IOS", UA_IOS_DEFAULT)
UA_TV = os.getenv("YT_USER_AGENT_TV", UA_TV_DEFAULT)
UA_MWEB = os.getenv("YT_USER_AGENT_MWEB", UA_MWEB_DEFAULT)
USER_AGENT = os.getenv("YT_USER_AGENT", UA_WEB_DEFAULT)  # 하위 호환성을 위해 유지
# PO 토큰 환경변수 (mweb/web용)
YT_PO_TOKEN_MWEB_GVS = os.getenv("YT_PO_TOKEN_MWEB_GVS")
YT_PO_TOKEN_MWEB_PLAYER = os.getenv("YT_PO_TOKEN_MWEB_PLAYER")
YT_PO_TOKEN_WEB_GVS = os.getenv("YT_PO_TOKEN_WEB_GVS")
YT_PO_TOKEN_WEB_PLAYER = os.getenv("YT_PO_TOKEN_WEB_PLAYER")
COOKIES_SRC = os.getenv("YT_COOKIES_FILE", "/etc/secrets/cookies.txt")
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

def validate_cookie_file(cookie_path):
    """쿠키 파일 유효성 검사"""
    if not cookie_path or not os.path.exists(cookie_path):
        return False, "Cookie file not found"
    
    try:
        with open(cookie_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if not content.strip():
            return False, "Cookie file is empty"
            
        # Netscape 형식 확인
        lines = content.strip().split('\n')
        valid_cookies = 0
        youtube_cookies = 0
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            parts = line.split('\t')
            if len(parts) >= 7:
                domain = parts[0]
                expiry = parts[4]
                
                valid_cookies += 1
                
                # YouTube/Google 도메인 확인
                if any(d in domain for d in ['.youtube.com', '.google.com', 'accounts.google.com']):
                    youtube_cookies += 1
                    
                # 만료일 확인 (Unix timestamp)
                try:
                    import time
                    if expiry.isdigit() and int(expiry) < time.time():
                        print(f"WARNING: Cookie for {domain} has expired")
                except:
                    pass
        
        if valid_cookies == 0:
            return False, "No valid cookies found in file"
            
        if youtube_cookies == 0:
            return False, "No YouTube/Google cookies found"
            
        print(f"Cookie validation: {valid_cookies} total cookies, {youtube_cookies} YouTube/Google cookies")
        return True, f"Valid cookie file with {youtube_cookies} YouTube cookies"
        
    except Exception as e:
        return False, f"Cookie file validation error: {str(e)}"

def _cookie_copy_to_tmp() -> str:
    """읽기 전용 쿠키 파일을 /tmp로 복사하여 쓰기 가능하게 만들기"""
    try:
        # 쿠키 파일 존재 여부 확인
        if not os.path.exists(COOKIES_SRC):
            print(f"WARNING: Cookie file not found at {COOKIES_SRC}")
            return None
            
        # 쿠키 파일이 비어있는지 확인
        if os.path.getsize(COOKIES_SRC) == 0:
            print(f"WARNING: Cookie file is empty at {COOKIES_SRC}")
            return None
            
        # 쿠키 파일 유효성 검사
        is_valid, message = validate_cookie_file(COOKIES_SRC)
        if not is_valid:
            print(f"WARNING: Cookie validation failed: {message}")
            return None
            
        dst = os.path.join(tempfile.gettempdir(), "yt_cookies.txt")
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(COOKIES_SRC, dst)
        os.chmod(dst, 0o600)
        print(f"Cookie file copied successfully from {COOKIES_SRC} to {dst}")
        print(f"Cookie validation: {message}")
        return dst
    except Exception as e:
        print(f"ERROR: Failed to copy cookie file: {e}")
        return None

def build_ydl_opts(player_client: str, use_cookies: bool = True, enable_debug: bool = False):
    """클라이언트별 yt-dlp 옵션 빌드"""
    headers = {"Accept-Language": "en-US,en;q=0.9"}
    ua = UA_WEB

    if player_client == "web":
        ua = UA_WEB
        headers.update({
            "User-Agent": ua,
            "Origin": "https://www.youtube.com",
            "Referer": "https://www.youtube.com/",
        })
    elif player_client == "mweb":
        ua = UA_MWEB
        headers.update({
            "User-Agent": ua,
        })
    elif player_client == "android":
        ua = UA_ANDROID
        headers.update({"User-Agent": ua})
    elif player_client == "ios":
        ua = UA_IOS
        headers.update({"User-Agent": ua})
    elif player_client == "tv":
        ua = UA_TV
        headers.update({"User-Agent": ua})
    else:
        headers.update({"User-Agent": ua})

    # extractor_args 구성 (클라이언트 및 PO 토큰)
    youtube_args = {"player_client": [player_client]}
    po_tokens = []
    if player_client == "mweb":
        if YT_PO_TOKEN_MWEB_GVS:
            po_tokens.append(f"mweb.gvs+{YT_PO_TOKEN_MWEB_GVS}")
        if YT_PO_TOKEN_MWEB_PLAYER:
            po_tokens.append(f"mweb.player+{YT_PO_TOKEN_MWEB_PLAYER}")
        # 가이드에 맞춰 default+mweb 지정
        youtube_args["player_client"] = ["default", "mweb"]
    elif player_client == "web":
        if YT_PO_TOKEN_WEB_GVS:
            po_tokens.append(f"web.gvs+{YT_PO_TOKEN_WEB_GVS}")
        if YT_PO_TOKEN_WEB_PLAYER:
            po_tokens.append(f"web.player+{YT_PO_TOKEN_WEB_PLAYER}")
    if po_tokens:
        youtube_args["po_token"] = po_tokens

    # youtubetab에도 동일한 player_client/po_token 적용
    youtubetab_args = {"player_client": youtube_args["player_client"]}
    if po_tokens:
        youtubetab_args["po_token"] = po_tokens

    opts = {
        "quiet": True,
        "no_warnings": True,
        "force_ipv4": True,
        "retries": 3,
        "extractor_retries": 3,
        "user_agent": ua,
        "http_headers": headers,
        "extractor_args": {"youtube": youtube_args, "youtubetab": youtubetab_args},
        "geo_bypass": True,
        "noplaylist": True,
    }

    # 프록시 설정 (옵션)
    proxy = os.getenv("YT_PROXY")
    if proxy:
        opts["proxy"] = proxy

    # 쿠키 필수 사용 정책
    if use_cookies:
        cookie_file = _cookie_copy_to_tmp()
        if cookie_file:
            opts["cookiefile"] = cookie_file
        else:
            print(f"WARNING: Cookie file not available for {player_client} client")

    # 디버그 모드 (첫 번째 시도에서만)
    if enable_debug:
        opts.update({
            "write_pages": True,
            "verbose": True
        })
        print(f"DEBUG: Enabled debug mode for {player_client} client")

    return opts

def get_video_info_with_fallback(url, attempt=1, max_attempts=4):
    """폴백 전략을 사용한 YouTube 비디오 정보 가져오기"""

    # mweb을 항상 포함하고 마지막은 tv로 확장
    fallback_configs = [
        {"player_client": "web", "use_cookies": True, "enable_debug": True},
        {"player_client": "android", "use_cookies": True, "enable_debug": False},
        {"player_client": "ios", "use_cookies": True, "enable_debug": False},
        {"player_client": "mweb", "use_cookies": True, "enable_debug": False},
        {"player_client": "tv", "use_cookies": True, "enable_debug": False},
    ]
    max_attempts = len(fallback_configs)

    config = fallback_configs[attempt - 1]
    
    try:
        print(f"==> 비디오 정보 추출 시도 {attempt}/{max_attempts} - {config['player_client']} 클라이언트")
        
        # build_ydl_opts 함수 사용
        ydl_opts = build_ydl_opts(
            player_client=config['player_client'],
            use_cookies=config['use_cookies'],
            enable_debug=config['enable_debug']
        )
        
        # 추가 옵션 설정
        ydl_opts.update({
            'extract_flat': False,
            'sleep_interval': 1,
            'max_sleep_interval': 5,
            'socket_timeout': 30,
            'fragment_retries': 5,
            'retry_sleep_functions': {'http': lambda n: min(2 ** n, 30)},
        })
        
        print(f"==> 플레이어 클라이언트: {config['player_client']}")
        
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
            
            print(f"==> 비디오 정보 추출 성공 (시도 {attempt})")
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
        print(f"==> 시도 {attempt} 실패: {str(e)}")
        
        # 다음 시도가 가능한 경우
        if attempt < max_attempts:
            print(f"==> 다음 전략으로 재시도...")
            import time
            time.sleep(2)  # 2초 대기
            return get_video_info_with_fallback(url, attempt + 1, max_attempts)
        else:
            print(f"==> 모든 시도 실패")
            return None

def get_video_info(url):
    """YouTube 비디오 정보 가져오기 (폴백 전략 사용)"""
    return get_video_info_with_fallback(url)

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

        # build_ydl_opts 함수 사용 (쿠키 필수 사용)
        if format_type == 'mp3':
            ydl_opts = build_ydl_opts(player_client='web', use_cookies=True)
            ydl_opts.update({
                'outtmpl': '%(id)s.%(ext)s',
                'format': 'bestaudio/best',
                'noplaylist': True,
                'overwrites': True,
                'paths': {'home': OUTPUT_FOLDER, 'temp': TEMP_FOLDER},
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                # MP3 튜닝: 라임 코덱 및 품질 설정 (faststart는 MP4에만 적용됨)
                'postprocessor_args': {
                    'extractaudio+ffmpeg_o': ['-codec:a', 'libmp3lame', '-q:a', '2', '-id3v2_version', '3']
                }
            })
        else:
            ydl_opts = build_ydl_opts(player_client='web', use_cookies=True)
            ydl_opts.update({
                'outtmpl': '%(id)s.%(ext)s',
                'format': DEFAULT_FORMAT,
                'merge_output_format': MERGE_FORMAT,
                'noplaylist': True,
                'overwrites': True,
                'paths': {'home': OUTPUT_FOLDER, 'temp': TEMP_FOLDER},
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
            })

        # 쿠키는 build_ydl_opts에서 이미 설정됨

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
            return jsonify({
                'error': error,
                'suggestions': [
                    '쿠키 파일이 최신인지 확인해주세요',
                    '브라우저에서 YouTube에 로그인한 상태로 쿠키를 다시 내보내기 해보세요',
                    '다른 품질이나 형식으로 시도해보세요',
                    '/debug-cookies-content 엔드포인트에서 쿠키 상태를 확인해보세요'
                ]
            }), 500
        
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
            return jsonify({
                'error': '비디오 정보를 가져올 수 없습니다.',
                'suggestions': [
                    '쿠키 파일이 최신인지 확인해주세요',
                    '브라우저에서 YouTube에 로그인한 상태로 쿠키를 다시 내보내기 해보세요',
                    '잠시 후 다시 시도해보세요',
                    '/debug-cookies-content 엔드포인트에서 쿠키 상태를 확인해보세요'
                ]
            }), 400
        
        return jsonify({
            'success': True,
            'video_info': video_info
        })
        
    except Exception as e:
        print(f"비디오 정보 조회 중 오류: {str(e)}")
        return jsonify({'error': f'서버 오류: {str(e)}'}), 500

@app.route('/debug-cookies-content')
def debug_cookies_content():
    """쿠키 파일 내용 디버깅"""
    try:
        if not os.path.exists(COOKIES_SRC):
            return jsonify({
                'error': f'Cookie file not found at {COOKIES_SRC}',
                'exists': False
            })
        
        file_size = os.path.getsize(COOKIES_SRC)
        if file_size == 0:
            return jsonify({
                'error': 'Cookie file is empty',
                'exists': True,
                'size': 0
            })
        
        # 쿠키 파일 유효성 검사
        is_valid, message = validate_cookie_file(COOKIES_SRC)
        
        # 쿠키 도메인 정보 수집
        domains = []
        cookie_count = 0
        youtube_count = 0
        
        try:
            with open(COOKIES_SRC, 'r', encoding='utf-8') as f:
                content = f.read()
                
            lines = content.strip().split('\n')
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                    
                parts = line.split('\t')
                if len(parts) >= 7:
                    domain = parts[0]
                    expiry = parts[4]
                    cookie_count += 1
                    
                    # 만료일 확인
                    import time
                    is_expired = False
                    try:
                        if expiry.isdigit() and int(expiry) < time.time():
                            is_expired = True
                    except:
                        pass
                    
                    # YouTube/Google 도메인 확인
                    is_youtube = any(d in domain for d in ['.youtube.com', '.google.com', 'accounts.google.com'])
                    if is_youtube:
                        youtube_count += 1
                    
                    domains.append({
                        'domain': domain,
                        'is_youtube': is_youtube,
                        'is_expired': is_expired,
                        'expiry': expiry
                    })
        
        except Exception as e:
            return jsonify({
                'error': f'Failed to read cookie file: {str(e)}',
                'exists': True,
                'size': file_size
            })
        
        return jsonify({
            'exists': True,
            'size': file_size,
            'is_valid': is_valid,
            'validation_message': message,
            'total_cookies': cookie_count,
            'youtube_cookies': youtube_count,
            'domains': domains[:20]  # 처음 20개 도메인만 표시
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Debug error: {str(e)}'
        })

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
        p = COOKIES_SRC
        ok = bool(p and os.path.exists(p))
        size = os.path.getsize(p) if ok else 0
        
        return jsonify({
            "has_secrets_file": ok,
            "path": p,
            "size": size,
            "user_agent": USER_AGENT,
            "format": DEFAULT_FORMAT,
            "merge_format": MERGE_FORMAT,
            "max_file_mb": MAX_FILE_MB
        })
    except Exception as e:
        return jsonify({
            "has_secrets_file": False,
            "error": str(e)
        }), 500

@app.route('/debug-cookies/summary')
def debug_cookie_summary():
    """쿠키 파일 내용 분석 및 핵심 쿠키 검증 엔드포인트"""
    try:
        p = COOKIES_SRC
        if not (p and os.path.exists(p)):
            return jsonify({"exists": False, "path": p})
        
        lines = open(p, "r", encoding="utf-8", errors="ignore").read().splitlines()
        domains, names, bad = set(), set(), 0
        
        for ln in lines:
            if not ln or ln.startswith("#"):
                continue
            parts = ln.split("\t")
            if len(parts) < 7:
                bad += 1
                continue
            domain, incl, path, secure, exp, name, value = parts[:7]
            domains.add(domain.strip())
            names.add(name.strip())
        
        need_domain = {".google.com", "accounts.google.com", ".youtube.com"}
        need_any_name = {"SAPISID", "__Secure-3PAPISID"}  # 둘 중 하나는 꼭 필요
        need_consent = {"CONSENT", "SOCS"}  # Consent 쿠키 확인
        
        return jsonify({
            "exists": True,
            "path": p,
            "lines": len(lines),
            "invalid_lines": bad,
            "domains_present": sorted(domains),
            "has_google_domain": bool(need_domain & domains),
            "has_key_cookie": bool(need_any_name & names),
            "key_cookies_present": sorted(need_any_name & names),
            "has_consent_cookie": bool(need_consent & names),
            "consent_cookies_present": sorted(need_consent & names),
        })
    except Exception as e:
        return jsonify({
            "exists": False,
            "error": str(e)
        }), 500

@app.route('/debug-yt')
def debug_yt():
    """yt-dlp 버전 및 시스템 정보 확인 엔드포인트"""
    try:
        # Git HEAD 정보 가져오기 시도
        git_head = "unknown"
        try:
            from yt_dlp.version import RELEASE_GIT_HEAD_SHORT
            git_head = RELEASE_GIT_HEAD_SHORT
        except ImportError:
            # RELEASE_GIT_HEAD_SHORT가 없는 경우 다른 방법 시도
            try:
                import yt_dlp
                git_head = getattr(yt_dlp.version, 'RELEASE_GIT_HEAD_SHORT', 'unknown')
            except:
                git_head = "unknown"
        
        return jsonify({
            "yt_dlp_version": YDL_VERSION,
            "git_head": git_head,
            "python": sys.version.split()[0],
            "openssl": ssl.OPENSSL_VERSION,
        })
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

@app.route('/debug-ua')
def debug_ua():
    import os
    return jsonify({
        "web": os.getenv("YT_USER_AGENT_WEB"),
        "android": os.getenv("YT_USER_AGENT_ANDROID"),
        "ios": os.getenv("YT_USER_AGENT_IOS"),
        "tv": os.getenv("YT_USER_AGENT_TV"),
        "mweb": os.getenv("YT_USER_AGENT_MWEB"),
        "single_USER_AGENT": os.getenv("YT_USER_AGENT"),
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)