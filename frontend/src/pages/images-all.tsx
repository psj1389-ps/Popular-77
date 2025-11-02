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

const ImagesAllPage: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [outputFormat, setOutputFormat] = useState<'jpg' | 'png' | 'webp' | 'gif' | 'bmp' | 'tiff'>('jpg');
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
    form.append('format', outputFormat);
    form.append('quality', quality);
    form.append('transparent_background', String(transparentBackground));
    form.append('scale', String(scale));

    try {
      const res = await fetch('/api/images-all', { method: 'POST', body: form });
      if (!res.ok) {
        const msg = await getErrorMessage(res);
        throw new Error(msg);
      }
      clearInterval(progressInterval);
      setConversionProgress(100);

      const blob = await res.blob();
      const base = selectedFile.name.replace(/\.[^/.]+$/, '');
      const name = base + '.' + outputFormat;

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
      <PageTitle suffix="이미지 변환기 (All Formats)" />
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
                Universal Image Converter - 모든 형식 지원
              </h1>
            </div>
            <p className="text-lg opacity-90 max-w-2xl mx-auto">JPG, PNG, WEBP, GIF, BMP, TIFF, SVG, PSD, HEIC, RAW 등 모든 이미지 형식을 원하는 형식으로 변환합니다.</p>
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
              <h2 className="text-2xl font-semibold text-gray-800">Universal Image Converter</h2>
              <p className="text-gray-500">모든 이미지 형식을 지원하는 만능 변환기 (JPG/PNG/WEBP/GIF/BMP/TIFF/SVG/PSD/HEIC/RAW)</p>
            </div>

            {!selectedFile ? (
              <label htmlFor="file-upload" className="block border-2 border-dashed border-gray-300 rounded-lg p-10 text-center cursor-pointer hover:border-blue-500 hover:bg-gray-50 transition-colors">
                <input id="file-upload" ref={fileInputRef} type="file" accept=".jpg,.jpeg,.png,.webp,.gif,.bmp,.tiff,.svg,.psd,.heif,.heic" onChange={handleFileChange} className="hidden" />
                <p className="font-semibold text-gray-700">파일을 선택하세요</p>
                <p className="text-sm text-gray-500 mt-1">파일을 드래그하거나 클릭하여 선택하세요 (최대 100개 파일, 총 500MB)</p>
              </label>
            ) : (
              <div className="space-y-6">
                <div>
                  <p className="text-gray-700"><span className="font-semibold">파일명:</span> {selectedFile.name}</p>
                  <p className="text-gray-700"><span className="font-semibold">크기:</span> {formatFileSize(selectedFile.size)}</p>
                </div>

                {/* 출력 형식 선택 */}
                <div>
                  <h3 className="font-semibold text-gray-800 mb-3">출력 형식:</h3>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                    {[
                      { value: 'jpg', label: '📷 JPG - 사진 최적화', desc: '작은 파일 크기' },
                      { value: 'png', label: '🖼️ PNG - 투명 배경', desc: '무손실 압축' },
                      { value: 'webp', label: '🌐 WEBP - 웹 최적화', desc: '최신 웹 표준' },
                      { value: 'gif', label: '🎞️ GIF - 애니메이션', desc: '움직이는 이미지' },
                      { value: 'bmp', label: '🖥️ BMP - 비트맵', desc: '무압축 형식' },
                      { value: 'tiff', label: '📄 TIFF - 고품질', desc: '전문가용 형식' }
                    ].map((format) => (
                      <label key={format.value} className={`flex flex-col p-3 border rounded-lg cursor-pointer transition-colors ${outputFormat === format.value ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'}`}>
                        <input 
                          type="radio" 
                          name="format" 
                          value={format.value} 
                          checked={outputFormat === format.value} 
                          onChange={(e) => setOutputFormat(e.target.value as any)} 
                          className="sr-only" 
                        />
                        <span className="font-medium text-sm">{format.label}</span>
                        <span className="text-xs text-gray-500">{format.desc}</span>
                      </label>
                    ))}
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

                    {/* 투명 배경 옵션 (PNG/WEBP만) */}
                    {(outputFormat === 'png' || outputFormat === 'webp') && (
                      <div className="flex items-center">
                        <input
                          type="checkbox"
                          id="transparent"
                          checked={transparentBackground}
                          onChange={(e) => setTransparentBackground(e.target.checked)}
                          className="w-4 h-4 text-blue-600 mr-3"
                        />
                        <label htmlFor="transparent" className="text-sm font-medium text-gray-700">
                          투명 배경 유지 (가능한 경우)
                        </label>
                      </div>
                    )}
                  </div>
                </div>

                {/* 변환 품질 선택 */}
                <div>
                  <h3 className="font-semibold text-gray-800 mb-3">변환 품질:</h3>
                  <div className="grid grid-cols-3 gap-3">
                    {(['low', 'medium', 'high'] as const).map((q) => (
                      <label key={q} className={`flex items-center p-3 border rounded-lg cursor-pointer transition-colors ${quality === q ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'}`}>
                        <input type="radio" name="quality" value={q} checked={quality === q} onChange={(e) => setQuality(e.target.value as 'low' | 'medium' | 'high')} className="w-4 h-4 text-blue-600 mr-3" />
                        <div className="flex-1">
                          <span className="font-medium">{q === 'low' ? '낮음' : q === 'medium' ? '보통' : '높음'}</span>
                          <div className="text-xs text-gray-500">{q === 'low' ? '빠른 변환' : q === 'medium' ? '균형잡힌 품질' : '최고 품질'}</div>
                        </div>
                      </label>
                    ))}
                  </div>
                </div>

                {/* 변환 버튼 */}
                <div className="flex gap-3">
                  <button onClick={handleConvert} disabled={isConverting} className="flex-1 bg-blue-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors">
                    {isConverting ? '변환 중...' : `${outputFormat.toUpperCase()}로 변환하기`}
                  </button>
                  <button onClick={handleReset} className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors">
                    초기화
                  </button>
                </div>

                {/* 진행률 표시 */}
                {isConverting && (
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <div className="flex justify-between text-sm text-gray-600 mb-2">
                      <span>변환 진행률</span>
                      <span>{Math.round(conversionProgress)}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div className="bg-blue-600 h-2 rounded-full transition-all duration-300" style={{ width: `${conversionProgress}%` }}></div>
                    </div>
                  </div>
                )}

                {/* 성공 메시지 */}
                {showSuccessMessage && (
                  <div className="bg-green-50 border border-green-200 text-green-800 px-4 py-3 rounded-lg">
                    <p className="font-medium">{successMessage}</p>
                  </div>
                )}

                {/* 에러 메시지 */}
                {errorMessage && (
                  <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg">
                    <p className="font-medium">{errorMessage}</p>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* 사용법 섹션 */}
          <div className="max-w-4xl mx-auto mt-16">
            <h2 className="text-3xl font-bold text-center text-gray-800 mb-12">Universal Image Converter 사용법</h2>
            <p className="text-center text-gray-600 mb-12">간단한 4단계로 모든 이미지 형식을 원하는 형식으로 변환하세요</p>
            
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
              <div className="text-center">
                <div className="bg-blue-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-2xl font-bold text-blue-600">1️⃣</span>
                </div>
                <h3 className="font-semibold text-lg mb-2">이미지 업로드</h3>
                <p className="text-gray-600">JPG, PNG, WEBP, GIF, BMP, TIFF, SVG, PSD, HEIC, RAW 등 모든 형식을 지원합니다.</p>
              </div>
              
              <div className="text-center">
                <div className="bg-green-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-2xl font-bold text-green-600">2️⃣</span>
                </div>
                <h3 className="font-semibold text-lg mb-2">출력 형식 선택</h3>
                <p className="text-gray-600">JPG, PNG, WEBP, GIF, BMP, TIFF 중 원하는 형식을 선택하세요.</p>
              </div>
              
              <div className="text-center">
                <div className="bg-yellow-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-2xl font-bold text-yellow-600">3️⃣</span>
                </div>
                <h3 className="font-semibold text-lg mb-2">옵션 설정</h3>
                <p className="text-gray-600">품질, 크기, 투명 배경 등 세부 옵션을 조정하세요.</p>
              </div>
              
              <div className="text-center">
                <div className="bg-purple-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-2xl font-bold text-purple-600">4️⃣</span>
                </div>
                <h3 className="font-semibold text-lg mb-2">변환 완료</h3>
                <p className="text-gray-600">변환된 파일을 자동으로 다운로드합니다.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default ImagesAllPage;