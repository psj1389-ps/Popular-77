from PIL import Image

try:
    img = Image.open('test_webp_debug.webp')
    print(f'Final WEBP file: {img.size}, Mode: {img.mode}')
    print(f'Has alpha: {img.mode == "RGBA"}')
    
    if img.mode == 'RGBA':
        alpha_channel = img.split()[-1]
        transparent_pixels = sum(1 for pixel in alpha_channel.getdata() if pixel == 0)
        total_pixels = img.width * img.height
        transparency_ratio = (transparent_pixels / total_pixels) * 100
        print(f'투명 픽셀 비율: {transparency_ratio:.1f}%')
    else:
        print('투명 채널이 없습니다')
except Exception as e:
    print(f'오류: {e}')