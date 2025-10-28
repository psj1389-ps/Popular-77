import React, { useState, useRef } from 'react';
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
  const ct = (res.headers.get('content-type') || '').toLowerCase();
  if (ct.includes('application/json')) {
    try {
      const j = await res.json();
      return j?.error || `요청 실패(${res.status})`;
    } catch {}
  }
  try { return await res.text(); } catch { return `요청 실패(${res.status})`; }
}

const ImageJpgPage: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [quality, setQuality] = useState<'low' | 'medium' | 'high'>('medium');
  const [scale, setScale] = useState(1.0); // 0.1 ~ 3.0
  const [isConverting, setIsConverting] = useState(false);
  const [progress, setProgress] = useState(0);
  const [showSuccessMessage, setShowSuccessMessage] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0] || null;
    setSelectedFile(f);
    setErrorMessage('');
    setShowSuccessMessage(false);
    setSuccessMessage('');
  };

  const handleReset = () => {
    setSelectedFile(null);
    setErrorMessage('');
    setShowSuccessMessage(false);
    setSuccessMessage('');
    setProgress(0);
    setIsConverting(false);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleConvert = async () => {
    if (!selectedFile) {
      setErrorMessage('먼저 변환할 이미지를 선택해주세요.');
      return;
    }

    setIsConverting(true);
    setProgress(10);
    setErrorMessage('');
    setShowSuccessMessage(false);

    const form = new FormData();
    form.append('file', selectedFile);
    form.append('quality', quality);
    form.append('resize', String(scale));

    try {
      const res = await fetch('/api/image-to-jpg', { method: 'POST', body: form });
      if (!res.ok) {
        const msg = await getErrorMessage(res);
        throw new Error(msg);
      }
      setProgress(70);

      const blob = await res.blob();
      setProgress(100);

      const base = selectedFile.name.replace(/\.[^/.]+$/, '');
      let name = safeGetFilename(res, base + '.jpg');
      if (!/\.(jpg|jpeg)$/i.test(name)) name = base + '.jpg';

      setSuccessMessage(`변환 완료! ${name} 파일을 다운로드합니다.`);
      setShowSuccessMessage(true);

      setTimeout(() => downloadBlob(blob, name), 800);
    } catch (e) {
      setErrorMessage(e instanceof Error ? e.message : '변환 중 오류가 발생했습니다.');
      setProgress(0);
    } finally {
      setTimeout(() => {
        setIsConverting(false);
        setProgress(0);
      }, 1500);
    }
  };

  return (
    <>
      <PageTitle suffix="이미지 → JPG" />
      <div className="w-full bg-white">
        {/* 상단 헤더 섹션 */}
        <div className="bg-gradient-to-r from-indigo-600 to-blue-600 text-white py-16 px-4 text-center">
          <div className="container mx-auto">
            <h1 className="text-4xl font-bold mb-2">이미지 → JPG 변환기</h1>
            <p className="opacity-90">PNG, SVG, WEBP, BMP, TIFF, GIF 등 이미지를 고품질 JPG로 변환합니다.</p>
          </div>
        </div>

        {/* 본문 */}
        <div className="container mx-auto px-4 py-10 max-w-3xl">
          {/* 업로드 카드 */}
          <div className="bg-white rounded-2xl shadow p-6 mb-8">
            <h2 className="text-xl font-semibold mb-4">파일 업로드</h2>
            <input
              ref={fileInputRef}
              type="file"
              accept=".png,.jpg,.jpeg,.webp,.bmp,.tiff,.gif,.svg,.psd,.heif,.heic"
              onChange={handleFileChange}
              className="block w-full text-sm text-gray-700"
            />

            {selectedFile && (
              <p className="mt-2 text-sm text-gray-600">선택됨: {selectedFile.name}</p>
            )}

            <div className="flex flex-col sm:flex-row gap-6 mt-6">
              <div className="flex-1">
                <label className="block text-sm font-medium text-gray-700 mb-2">품질</label>
                <select
                  value={quality}
                  onChange={(e) => setQuality(e.target.value as 'low' | 'medium' | 'high')}
                  className="w-full border rounded-lg px-3 py-2"
                >
                  <option value="low">낮음</option>
                  <option value="medium">보통</option>
                  <option value="high">높음</option>
                </select>
              </div>
              <div className="flex-1">
                <label className="block text-sm font-medium text-gray-700 mb-2">크기 배율 (0.1~3.0)</label>
                <input
                  type="number"
                  step="0.1"
                  min={0.1}
                  max={3.0}
                  value={scale}
                  onChange={(e) => setScale(Math.max(0.1, Math.min(3.0, parseFloat(e.target.value || '1.0'))))}
                  className="w-full border rounded-lg px-3 py-2"
                />
              </div>
            </div>

            <div className="flex flex-wrap gap-3 mt-6">
              <button
                onClick={handleConvert}
                disabled={!selectedFile || isConverting}
                className={`px-4 py-2 rounded-lg text-white ${isConverting ? 'bg-gray-400' : 'bg-blue-600 hover:bg-blue-700'}`}
              >
                {isConverting ? '변환 중…' : 'JPG로 변환'}
              </button>
              <button
                onClick={handleReset}
                className="px-4 py-2 rounded-lg border"
              >
                초기화
              </button>
              {isConverting && (
                <span className="text-sm text-gray-600">진행률: {progress}%</span>
              )}
            </div>

            {errorMessage && (
              <div className="mt-4 p-3 rounded bg-red-50 text-red-700 text-sm">{errorMessage}</div>
            )}
            {showSuccessMessage && (
              <div className="mt-4 p-3 rounded bg-green-50 text-green-700 text-sm">{successMessage}</div>
            )}
          </div>

          {/* 안내 섹션 */}
          <div className="bg-white rounded-2xl shadow p-6">
            <h3 className="text-lg font-semibold mb-2">지원 형식</h3>
            <p className="text-sm text-gray-700">PNG, WEBP, BMP, TIFF, GIF, JPEG, SVG, PSD, HEIF/HEIC 등</p>
            <p className="text-xs text-gray-500 mt-2">SVG는 내부적으로 렌더링 후 JPG로 변환합니다.</p>
          </div>
        </div>
      </div>
    </>
  );
};

export default ImageJpgPage;