import React, { useState, useRef, useEffect } from 'react';
import PageTitle from '../shared/PageTitle';

const downloadBlob = (blob: Blob, filename: string) => {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
};

const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// 안전한 파일명 추출
function safeGetFilename(res: Response, fallback: string) {
  const cd = res.headers.get('content-disposition') || '';
  const star = /filename\*=UTF-8''([^;]+)/i.exec(cd);
  if (star?.[1]) {
    try { return decodeURIComponent(star[1]); } catch {}
  }
  const normal = /filename="?([^";]+)"?/i.exec(cd);
  return normal?.[1] || fallback;
}

async function getErrorMessage(res: Response) {
  if (res.status === 413) {
    return '업로드 파일이 너무 큽니다 (413). 파일 크기를 줄이거나 품질을 낮춰서 다시 시도해 주세요.';
  }
  const ct = (res.headers.get('content-type') || '').toLowerCase();
  if (!ct.includes('application/json')) return `서버 오류: ${res.status}`;
  try {
    const j = await res.json();
    return j?.error || `서버 오류: ${res.status}`;
  } catch {
    try { return await res.text(); } catch { return `서버 오류: ${res.status}`; }
  }
}

const ImagesWebpPage: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [quality, setQuality] = useState<'low' | 'medium' | 'high'>('medium');
  const [transparentBackground, setTransparentBackground] = useState(false);
  const [scale, setScale] = useState(0.5);
  const [isConverting, setIsConverting] = useState(false);
  const [conversionProgress, setConversionProgress] = useState(0);
  const [showSuccessMessage, setShowSuccessMessage] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [dims, setDims] = useState<{width:number;height:number}|null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!selectedFile) { setDims(null); return; }
    const url = URL.createObjectURL(selectedFile);
    const img = new Image();
    img.onload = () => { setDims({ width: img.width, height: img.height }); URL.revokeObjectURL(url); };
    img.onerror = () => { setDims(null); URL.revokeObjectURL(url); };
    img.src = url;
  }, [selectedFile]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0] || null;
    if (f && f.size > 100 * 1024 * 1024) {
      setErrorMessage('파일 크기는 100MB를 초과할 수 없습니다.');
      setSelectedFile(null);
      return;
    }
    setSelectedFile(f);
    setErrorMessage('');
    setShowSuccessMessage(false);
    setSuccessMessage('');
    setConversionProgress(0);
  };

  const handleReset = () => {
    setSelectedFile(null);
    setErrorMessage('');
    setShowSuccessMessage(false);
    setSuccessMessage('');
    setConversionProgress(0);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleConvert = async () => {
    if (!selectedFile) {
      setErrorMessage('먼저 파일을 선택해주세요.');
      return;
    }
    setIsConverting(true);
    setErrorMessage('');
    setShowSuccessMessage(false);
    setConversionProgress(0);

    const progressInterval = setInterval(() => {
      setConversionProgress(prev => {
        if (prev >= 90) {
          clearInterval(progressInterval);
          return 90;
        }
        return Math.min(90, prev + Math.random() * 15);
      });
    }, 200);

    const form = new FormData();
    form.append('file', selectedFile);
    form.append('quality', quality);
    form.append('transparent_background', String(transparentBackground));

    try {
      const res = await fetch('/api/images-webp', { method: 'POST', body: form });
      if (!res.ok) {
        const msg = await getErrorMessage(res);
        throw new Error(msg);
      }
      clearInterval(progressInterval);
      setConversionProgress(100);

      const blob = await res.blob();
      const base = selectedFile.name.replace(/\.[^/.]+$/, '');
      const name = base + '.webp';

      setSuccessMessage(`변환 완료! ${name} 파일이 다운로드됩니다.`);
      setShowSuccessMessage(true);

      setTimeout(() => downloadBlob(blob, name), 1000);
    } catch (e) {
      clearInterval(progressInterval);
      setConversionProgress(0);
      setErrorMessage(e instanceof Error ? e.message : '변환 중 예상치 못한 문제 발생');
    } finally {
      setTimeout(() => {
        setIsConverting(false);
        setConversionProgress(0);
      }, 2000);
    }
  };

  const calculatePixelSize = () => {
    if (!dims) return '원본 크기 확인 중...';
    const scaledWidth = Math.round(dims.width * scale);
    const scaledHeight = Math.round(dims.height * scale);
    return `${scaledWidth}×${scaledHeight} px`;
  };

  return (
    <>
      <PageTitle suffix="이미지 → WEBP" />
      <div className="w-full bg-white">
        {/* 상단 보라색 배경 섹션 */}
        <div className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white py-20 px-4 text-center relative overflow-hidden">
          {/* 애니메이션 배경 패턴 */}
          <div 
            className="absolute inset-0 opacity-30"
            style={{
              backgroundImage: `url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><defs><pattern id='grain' width='100' height='100' patternUnits='userSpaceOnUse'><circle cx='12' cy='8' r='0.6' fill='%23ffffff' opacity='0.18'/><circle cx='37' cy='23' r='1.8' fill='%23ffffff' opacity='0.06'/><circle cx='68' cy='15' r='0.9' fill='%23ffffff' opacity='0.14'/><circle cx='91' cy='42' r='1.3' fill='%23ffffff' opacity='0.09'/><circle cx='24' cy='56' r='0.7' fill='%23ffffff' opacity='0.16'/><circle cx='55' cy='73' r='1.5' fill='%23ffffff' opacity='0.07'/><circle cx='83' cy='88' r='1.1' fill='%23ffffff' opacity='0.11'/><circle cx='6' cy='34' r='2.0' fill='%23ffffff' opacity='0.05'/><circle cx='45' cy='47' r='0.8' fill='%23ffffff' opacity='0.13'/><circle cx='72' cy='61' r='1.2' fill='%23ffffff' opacity='0.10'/><circle cx='18' cy='79' r='0.5' fill='%23ffffff' opacity='0.19'/><circle cx='63' cy='29' r='1.7' fill='%23ffffff' opacity='0.08'/><circle cx='89' cy='18' r='0.9' fill='%23ffffff' opacity='0.15'/><circle cx='31' cy='91' r='1.4' fill='%23ffffff' opacity='0.12'/><circle cx='76' cy='5' r='0.6' fill='%23ffffff' opacity='0.17'/><circle cx='9' cy='67' r='1.6' fill='%23ffffff' opacity='0.06'/><circle cx='52' cy='12' r='1.0' fill='%23ffffff' opacity='0.14'/><circle cx='95' cy='76' r='0.8' fill='%23ffffff' opacity='0.11'/></pattern></defs><rect width='100' height='100' fill='url(%23grain)'/></svg>")`,
              backgroundRepeat: 'repeat',
              animation: 'float 20s ease-in-out infinite'
            }}
          />
          <div className="container mx-auto relative z-10">
            <div className="flex justify-center items-center gap-4 mb-4">
              <h1 className="text-4xl font-bold">
                <svg className="w-12 h-12 inline-block mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                Image(JPG, PNG, BMP, TIFF, GIF, SVG, PSD, HEIC, RAW) → WEBP 변환기
              </h1>
            </div>
            <p className="text-lg opacity-90 max-w-2xl mx-auto">JPG, PNG, BMP, TIFF, GIF, SVG, PSD, HEIC, RAW 이미지를 고품질 WEBP로 변환합니다.</p>
          </div>
        </div>

        <style>{`
          @keyframes float {
            0% { transform: translateX(0px) translateY(0px); }
            33% { transform: translateX(-25px) translateY(18px); }
            66% { transform: translateX(22px) translateY(-15px); }
            100% { transform: translateX(0px) translateY(0px); }
          }
        `}</style>

        <div className="container mx-auto px-4 py-16">
          <div className="bg-white p-8 rounded-xl shadow-lg max-w-2xl mx-auto">
            <div className="text-center mb-6">
              <h2 className="text-2xl font-semibold text-gray-800">Image → WEBP 변환기</h2>
              <p className="text-gray-500">다양한 이미지 형식을 고품질 WEBP로 변환 (JPG/PNG/BMP/TIFF/GIF/SVG/PSD/HEIC/RAW → WEBP)</p>
            </div>

            {!selectedFile ? (
              <label htmlFor="file-upload" className="block border-2 border-dashed border-gray-300 rounded-lg p-10 text-center cursor-pointer hover:border-blue-500 hover:bg-gray-50 transition-colors">
                <input id="file-upload" ref={fileInputRef} type="file" accept=".png,.jpg,.jpeg,.bmp,.tiff,.gif,.svg,.psd,.heif,.heic" onChange={handleFileChange} className="hidden" />
                <p className="font-semibold text-gray-700">파일을 선택하세요</p>
                <p className="text-sm text-gray-500 mt-1">파일을 드래그하거나 클릭하여 선택하세요 (최대 100개 파일, 총 500MB)</p>
              </label>
            ) : (
              <div className="space-y-6">
                <div>
                  <p className="text-gray-700"><span className="font-semibold">파일명:</span> {selectedFile.name}</p>
                  <p className="text-gray-700"><span className="font-semibold">크기:</span> {formatFileSize(selectedFile.size)}</p>
                </div>

                {/* 출력 형식 (고정 WEBP) */}
                <div>
                  <h3 className="font-semibold text-gray-800 mb-3">출력 형식:</h3>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <label className="flex items-center p-3 border rounded-lg">
                      <input type="radio" name="format" value="webp" checked readOnly className="w-4 h-4 text-blue-600 mr-3" />
                      <div className="flex-1"><span className="font-medium">🖼️ WEBP - 고효율 압축, 투명도 지원</span></div>
                    </label>
                  </div>
                </div>

                {/* 고급 옵션 */}
                <div>
                  <h3 className="font-semibold text-gray-800 mb-2">고급 옵션:</h3>
                  <div className="bg-gray-50 p-4 rounded-lg space-y-4">
                    {/* 크기 슬라이더 */}
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <label className="text-sm font-medium text-gray-700">크기 x</label>
                        <span className="text-sm text-gray-600">{scale}</span>
                      </div>
                      <div className="text-sm text-gray-500 mb-2">{calculatePixelSize()}</div>
                      <input
                        type="range"
                        min="0.2"
                        max="2.0"
                        step="0.1"
                        value={scale}
                        onChange={(e) => setScale(parseFloat(e.target.value))}
                        className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                      />
                      <div className="flex justify-between text-xs text-gray-500 mt-1">
                        <span>0.2x (작게)</span>
                        <span>2.0x (크게)</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* 변환 품질 선택 */}
                <div>
                  <h3 className="font-semibold text-gray-800 mb-2">변환 품질 선택:</h3>
                  <div className="space-y-2">
                    <label className="flex items-center">
                      <input type="radio" name="quality" value="low" checked={quality === 'low'} onChange={(e) => setQuality(e.target.value as 'low' | 'medium' | 'high')} className="w-4 h-4 text-blue-600" />
                      <span className="ml-2 text-gray-700">저품질 (품질이 낮고 파일이 더 컴팩트함)</span>
                    </label>
                    <label className="flex items-center">
                      <input type="radio" name="quality" value="medium" checked={quality === 'medium'} onChange={(e) => setQuality(e.target.value as 'low' | 'medium' | 'high')} className="w-4 h-4 text-blue-600" />
                      <span className="ml-2 text-gray-700">중간 품질 (중간 품질 및 파일 크기)</span>
                    </label>
                    <label className="flex items-center">
                      <input type="radio" name="quality" value="high" checked={quality === 'high'} onChange={(e) => setQuality(e.target.value as 'low' | 'medium' | 'high')} className="w-4 h-4 text-blue-600" />
                      <span className="ml-2 text-gray-700">고품질 (더 높은 품질, 더 큰 파일 크기)</span>
                    </label>
                  </div>
                </div>

                {/* 투명 배경 옵션 */}
                <div>
                  <h3 className="font-semibold text-gray-800 mb-2">투명 배경: (PNG, WEBP에서 지원)</h3>
                  <div className="space-y-2">
                    <label className="flex items-center">
                      <input type="radio" name="transparent" value="false" checked={!transparentBackground} onChange={() => setTransparentBackground(false)} className="w-4 h-4 text-blue-600" />
                      <span className="ml-2 text-gray-700">사용 안함</span>
                    </label>
                    <label className="flex items-center">
                      <input type="radio" name="transparent" value="true" checked={transparentBackground} onChange={() => setTransparentBackground(true)} className="w-4 h-4 text-blue-600" />
                      <span className="ml-2 text-gray-700">사용</span>
                    </label>
                  </div>
                  <div className="mt-2 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                    <div className="flex items-start">
                      <span className="text-blue-500 mr-2">💡</span>
                      <div className="text-sm text-blue-700">
                        <div><strong>투명 배경 지원:</strong> PNG, WEBP 형식</div>
                        <div><strong>흰색 배경 변환:</strong> JPG, JPEG, TIFF, GIF, BMP</div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* 진행률 */}
                {isConverting && (
                  <div className="mb-4">
                    <div className="flex justify-between text-sm mb-1">
                      <span>변환 진행률</span>
                      <span>{Math.round(conversionProgress)}%</span>
                    </div>
                    <div className="h-2 bg-gray-200 rounded">
                      <div 
                        className="h-2 bg-indigo-500 rounded transition-[width] duration-300"
                        style={{ width: `${Math.max(2, Math.round(conversionProgress))}%` }}
                      />
                    </div>
                    <div className="mt-2 text-sm text-gray-500">⏳ 이미지를 WEBP로 변환 중...</div>
                  </div>
                )}

                {/* 성공 메시지 */}
                {showSuccessMessage && (
                  <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                    <div className="flex items-center">
                      <svg className="w-5 h-5 text-green-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                      <span className="text-green-700 font-medium">{successMessage}</span>
                    </div>
                  </div>
                )}

                <div className="flex gap-4">
                  <button onClick={handleConvert} disabled={isConverting || !selectedFile} className="flex-1 text-white px-6 py-3 rounded-lg text-lg font-semibold disabled:bg-gray-400 disabled:cursor-not-allowed" style={{background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'}} onMouseEnter={(e) => e.currentTarget.style.background = 'linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%)'} onMouseLeave={(e) => e.currentTarget.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'}>
                    {isConverting ? '변환 중...' : '변환하기'}
                  </button>
                  <button onClick={handleReset} disabled={isConverting} className="flex-1 bg-gray-600 text-white px-6 py-3 rounded-lg text-lg font-semibold hover:bg-gray-700 disabled:bg-gray-400 disabled:cursor-not-allowed">
                    파일 초기화
                  </button>
                </div>
              </div>
            )}

            {errorMessage && selectedFile && <p className="mt-4 text-center text-red-500">{errorMessage}</p>}
          </div>
        </div>

        {/* 이미지를 WEBP로 변환하는 방법 가이드 */}
        <div className="bg-gray-50 py-16">
          <div className="max-w-4xl mx-auto px-4">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold text-gray-800 mb-4">이미지를 WEBP로 변환하는 방법</h2>
              <p className="text-gray-600">간단한 4단계로 다양한 이미지를 고품질 WEBP로 변환하세요</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="bg-white rounded-lg p-6 shadow-md hover:shadow-lg transition-shadow">
                <div className="flex items-center justify-center w-12 h-12 bg-blue-100 rounded-full mb-4 mx-auto"><span className="text-xl font-bold text-blue-600">1️⃣</span></div>
                <h3 className="text-lg font-semibold text-gray-800 mb-2 text-center">이미지 업로드</h3>
                <p className="text-gray-600 text-sm text-center">JPG, PNG, BMP, TIFF, GIF, SVG, PSD, HEIC, RAW 등 파일을 업로드하세요.</p>
              </div>
              <div className="bg-white rounded-lg p-6 shadow-md hover:shadow-lg transition-shadow">
                <div className="flex items-center justify-center w-12 h-12 bg-green-100 rounded-full mb-4 mx-auto"><span className="text-xl font-bold text-green-600">2️⃣</span></div>
                <h3 className="text-lg font-semibold text-gray-800 mb-2 text-center">품질/투명도 선택</h3>
                <p className="text-gray-600 text-sm text-center">변환 품질과 투명 배경 옵션을 선택해 최적화하세요.</p>
              </div>
              <div className="bg-white rounded-lg p-6 shadow-md hover:shadow-lg transition-shadow">
                <div className="flex items-center justify-center w-12 h-12 bg-yellow-100 rounded-full mb-4 mx-auto"><span className="text-xl font-bold text-yellow-600">3️⃣</span></div>
                <h3 className="text-lg font-semibold text-gray-800 mb-2 text-center">자동 변환 시작</h3>
                <p className="text-gray-600 text-sm text-center">"변환하기" 버튼을 클릭하면 엔진이 WEBP로 변환합니다.</p>
              </div>
              <div className="bg-white rounded-lg p-6 shadow-md hover:shadow-lg transition-shadow">
                <div className="flex items-center justify-center w-12 h-12 bg-purple-100 rounded-full mb-4 mx-auto"><span className="text-xl font-bold text-purple-600">4️⃣</span></div>
                <h3 className="text-lg font-semibold text-gray-800 mb-2 text-center">WEBP 다운로드</h3>
                <p className="text-gray-600 text-sm text-center">변환 완료 후 WEBP 파일을 바로 다운로드합니다.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default ImagesWebpPage;