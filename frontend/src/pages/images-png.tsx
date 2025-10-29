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
    return '업로드 파일이 너무 큽니다 (413). 이미지는 용량이 큰 편이라 크기/품질을 낮추거나 압축 후 다시 시도해 주세요.';
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

const ImagesPngPage: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [quality, setQuality] = useState<'low' | 'medium' | 'high'>('medium');
  const [scale, setScale] = useState(0.5); // 0.2 ~ 2.0
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
        if (prev >= 90) return prev;
        return prev + Math.random() * 15;
      });
    }, 200);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('quality', quality);
      formData.append('scale', scale.toString());

      const response = await fetch('/api/images-png', {
        method: 'POST',
        body: formData,
      });

      clearInterval(progressInterval);
      setConversionProgress(100);

      if (!response.ok) {
        const errorMsg = await getErrorMessage(response);
        setErrorMessage(errorMsg);
        return;
      }

      const blob = await response.blob();
      const originalName = selectedFile.name.replace(/\.[^.]+$/, '');
      const filename = safeGetFilename(response, `${originalName}.png`);
      
      downloadBlob(blob, filename);
      
      setSuccessMessage(`파일이 성공적으로 PNG로 변환되었습니다: ${filename}`);
      setShowSuccessMessage(true);
      
      setTimeout(() => {
        setShowSuccessMessage(false);
      }, 5000);

    } catch (error) {
      clearInterval(progressInterval);
      setConversionProgress(0);
      setErrorMessage('변환 중 오류가 발생했습니다. 네트워크 연결을 확인해주세요.');
    } finally {
      setIsConverting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <PageTitle 
        title="Image(JPG, WEBP, BMP, TIFF, GIF, SVG, PSD, HEIC, RAW) → PNG 변환기"
        description="JPG, WEBP, BMP, TIFF, GIF, SVG, PSD, HEIC, RAW 이미지를 고품질 PNG로 변환합니다."
      />
      
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="bg-white rounded-lg shadow-lg p-8">
          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold text-gray-800 mb-2">Image → PNG 변환기</h2>
            <p className="text-gray-600">
              다양한 이미지 형식을 고품질 PNG로 변환<br />
              (JPG/WEBP/BMP/TIFF/GIF/SVG/PSD/HEIC/RAW → PNG)
            </p>
          </div>

          {/* 파일 업로드 영역 */}
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center mb-6 hover:border-purple-400 transition-colors">
            <input
              ref={fileInputRef}
              type="file"
              onChange={handleFileChange}
              accept=".jpg,.jpeg,.webp,.bmp,.tiff,.tif,.gif,.svg,.psd,.heic,.raw,.cr2,.nef,.arw,.dng"
              className="hidden"
              id="file-upload"
            />
            <label htmlFor="file-upload" className="cursor-pointer">
              <div className="text-6xl mb-4">📁</div>
              <h3 className="text-xl font-semibold text-gray-700 mb-2">파일을 선택하세요</h3>
              <p className="text-gray-500">
                파일을 드래그하거나 클릭하여 선택하세요 (최대 50개 파일, 총 500MB)
              </p>
            </label>
          </div>

          {/* 선택된 파일 정보 */}
          {selectedFile && (
            <div className="bg-gray-50 rounded-lg p-4 mb-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-gray-800">{selectedFile.name}</p>
                  <p className="text-sm text-gray-600">
                    크기: {formatFileSize(selectedFile.size)}
                    {dims && ` | 해상도: ${dims.width}×${dims.height}px`}
                  </p>
                </div>
                <button
                  onClick={handleReset}
                  className="text-red-500 hover:text-red-700 font-medium"
                >
                  제거
                </button>
              </div>
            </div>
          )}

          {/* 출력 형식 */}
          <div className="mb-6">
            <h4 className="text-lg font-semibold text-gray-800 mb-3">출력 형식</h4>
            <div className="bg-green-50 border border-green-200 rounded-lg p-3">
              <span className="text-green-800 font-medium">PNG (고품질 무손실)</span>
            </div>
          </div>

          {/* 크기 조절 */}
          <div className="mb-6">
            <h4 className="text-lg font-semibold text-gray-800 mb-3">크기 조절 (Scale)</h4>
            <div className="flex items-center space-x-4">
              <input
                type="range"
                min="0.2"
                max="2.0"
                step="0.1"
                value={scale}
                onChange={(e) => setScale(parseFloat(e.target.value))}
                className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
              />
              <span className="text-gray-700 font-medium min-w-[60px]">{scale}x</span>
            </div>
            {dims && (
              <p className="text-sm text-gray-600 mt-2">
                변환 후 크기: {Math.round(dims.width * scale)}×{Math.round(dims.height * scale)}px
              </p>
            )}
          </div>

          {/* 변환 품질 */}
          <div className="mb-6">
            <h4 className="text-lg font-semibold text-gray-800 mb-3">변환 품질</h4>
            <div className="grid grid-cols-3 gap-3">
              {[
                { value: 'low', label: '저품질', desc: '빠른 변환' },
                { value: 'medium', label: '중간품질', desc: '균형잡힌 품질' },
                { value: 'high', label: '고품질', desc: '최고 품질' }
              ].map((option) => (
                <button
                  key={option.value}
                  onClick={() => setQuality(option.value as 'low' | 'medium' | 'high')}
                  className={`p-3 rounded-lg border-2 text-center transition-colors ${
                    quality === option.value
                      ? 'border-purple-500 bg-purple-50 text-purple-700'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="font-medium">{option.label}</div>
                  <div className="text-sm text-gray-600">{option.desc}</div>
                </button>
              ))}
            </div>
          </div>

          {/* 진행률 표시 */}
          {isConverting && (
            <div className="mb-6">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-700">변환 진행률</span>
                <span className="text-sm text-gray-600">{Math.round(conversionProgress)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-purple-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${conversionProgress}%` }}
                ></div>
              </div>
            </div>
          )}

          {/* 성공 메시지 */}
          {showSuccessMessage && (
            <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-center">
                <div className="text-green-600 mr-3">✅</div>
                <p className="text-green-800">{successMessage}</p>
              </div>
            </div>
          )}

          {/* 에러 메시지 */}
          {errorMessage && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-center">
                <div className="text-red-600 mr-3">❌</div>
                <p className="text-red-800">{errorMessage}</p>
              </div>
            </div>
          )}

          {/* 변환 버튼 */}
          <div className="flex space-x-4">
            <button
              onClick={handleConvert}
              disabled={!selectedFile || isConverting}
              className={`flex-1 py-3 px-6 rounded-lg font-medium transition-colors ${
                !selectedFile || isConverting
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-purple-600 text-white hover:bg-purple-700'
              }`}
            >
              {isConverting ? '변환 중...' : 'PNG로 변환하기'}
            </button>
            
            <button
              onClick={handleReset}
              className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
            >
              초기화
            </button>
          </div>
        </div>

        {/* 사용법 안내 */}
        <div className="mt-8 bg-white rounded-lg shadow-lg p-8">
          <h3 className="text-xl font-bold text-gray-800 mb-6">이미지를 PNG로 변환하는 방법</h3>
          <p className="text-gray-600 mb-6">간단한 4단계로 다양한 이미지를 고품질 PNG로 변환하세요</p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="text-center">
              <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-3">
                <span className="text-purple-600 font-bold">1️⃣</span>
              </div>
              <h4 className="font-semibold text-gray-800 mb-2">이미지 업로드</h4>
              <p className="text-sm text-gray-600">JPG, WEBP, BMP, TIFF, GIF, SVG, PSD, HEIC, RAW 등 파일을 업로드하세요.</p>
            </div>
            
            <div className="text-center">
              <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-3">
                <span className="text-purple-600 font-bold">2️⃣</span>
              </div>
              <h4 className="font-semibold text-gray-800 mb-2">품질/크기 선택</h4>
              <p className="text-sm text-gray-600">변환 품질과 크기 조절 옵션을 선택해 최적화하세요.</p>
            </div>
            
            <div className="text-center">
              <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-3">
                <span className="text-purple-600 font-bold">3️⃣</span>
              </div>
              <h4 className="font-semibold text-gray-800 mb-2">자동 변환 시작</h4>
              <p className="text-sm text-gray-600">"변환하기" 버튼을 클릭하면 엔진이 PNG로 변환합니다.</p>
            </div>
            
            <div className="text-center">
              <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-3">
                <span className="text-purple-600 font-bold">4️⃣</span>
              </div>
              <h4 className="font-semibold text-gray-800 mb-2">PNG 다운로드</h4>
              <p className="text-sm text-gray-600">변환 완료 후 PNG 파일을 바로 다운로드합니다.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ImagesPngPage;