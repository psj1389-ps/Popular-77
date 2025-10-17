#!/usr/bin/env python3
"""
투명 처리 디버깅 스크립트
"""
import fitz
from PIL import Image
import os

def debug_transparency():
    """투명 처리 디버깅"""
    print("🔍 투명 처리 디버깅...")
    
    # PDF 파일 열기
    pdf_path = "test_sample.pdf"
    if not os.path.exists(pdf_path):
        print("❌ test_sample.pdf 파일을 찾을 수 없습니다.")
        return
    
    doc = fitz.open(pdf_path)
    page = doc[0]  # 첫 번째 페이지
    
    # 알파 채널 포함하여 렌더링
    pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0), alpha=True)
    
    # RGBA 변환
    mode = "RGBA" if pix.alpha else "RGB"
    img = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
    if mode != "RGBA":
        img = img.convert("RGBA")
    
    print(f"원본 이미지: {img.size}, 모드: {img.mode}")
    
    # 그레이스케일 변환
    gray = img.convert("L")
    print(f"그레이스케일 변환: {gray.size}, 모드: {gray.mode}")
    
    # 픽셀 값 분석 (샘플링으로 성능 개선)
    gray_data = list(gray.getdata())
    sample_size = min(10000, len(gray_data))  # 최대 10000개 샘플
    sample_data = gray_data[::len(gray_data)//sample_size] if len(gray_data) > sample_size else gray_data
    
    white_pixels = sum(1 for p in sample_data if p >= 250)
    total_sample = len(sample_data)
    white_ratio = (white_pixels / total_sample) * 100
    
    print(f"샘플 픽셀: {total_sample} (전체: {len(gray_data)})")
    print(f"흰색 픽셀 (>=250): {white_pixels} ({white_ratio:.1f}%)")
    print(f"밝기 범위: {min(sample_data)} ~ {max(sample_data)}")
    
    # 다양한 임계값으로 테스트
    thresholds = [200, 220, 240, 250, 260]
    for threshold in thresholds:
        white_count = sum(1 for p in sample_data if p >= threshold)
        ratio = (white_count / total_sample) * 100
        print(f"임계값 {threshold}: {white_count} 픽셀 ({ratio:.1f}%)")
    
    # 투명 마스크 생성 (임계값 240 사용)
    alpha_mask = gray.point(lambda p: 0 if p >= 240 else 255)
    print(f"알파 마스크: {alpha_mask.size}, 모드: {alpha_mask.mode}")
    
    # 결과 이미지 생성
    result = img.copy()
    result.putalpha(alpha_mask)
    
    # 결과 저장
    result.save("debug_transparency_result.png", "PNG")
    print("✅ 결과 이미지 저장: debug_transparency_result.png")
    
    # 결과 분석
    result_alpha = result.getchannel('A')
    result_alpha_data = list(result_alpha.getdata())
    sample_alpha = result_alpha_data[::len(result_alpha_data)//sample_size] if len(result_alpha_data) > sample_size else result_alpha_data
    result_transparent = sum(1 for p in sample_alpha if p == 0)
    
    print(f"최종 투명 픽셀: {result_transparent} ({(result_transparent/len(sample_alpha))*100:.1f}%)")
    
    doc.close()

if __name__ == "__main__":
    debug_transparency()