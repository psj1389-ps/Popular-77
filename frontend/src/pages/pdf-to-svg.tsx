import React, { useState, useRef, useEffect } from 'react';
import PageTitle from '../shared/PageTitle';

// 직접 다운로드를 위한 보조 함수 (컴포넌트 밖에 정의)
function triggerDirectDownload(downloadUrl: string) {
  // a.click() → 실패 대비 iframe 폴백
  const a = document.createElement("a");
  a.href = downloadUrl;
  a.style.display = "none";
  document.body.appendChild(a);
  a.click();
  a.remove();
  
  // 일부 브라우저/확장기능에서 a.click을 막을 경우 폴백
  setTimeout(() => {
    const iframe = document.createElement("iframe");
    iframe.style.display = "none";
    iframe.src = downloadUrl;
    document.body.appendChild(iframe);
    setTimeout(() => iframe.remove(), 60_000);
  }, 400);
}

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

const triggerDownload = (url: string, name: string) => {
  const a = document.createElement('a');
  a.href = url;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url); // 메모리 해제
};

const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const API_BASE = "/api/pdf-svg";

function safeGetFilename(res: Response, fallback: string) {
  const cd = res.headers.get("content-disposition") || "";
  const star = /filename\*\=UTF-8''([^;]+)/i.exec(cd);
  if (star?.[1]) { try { return decodeURIComponent(star[1]); } catch {} }
  const normal = /filename="?([^";]+)"?/i.exec(cd);
  return normal?.[1] || fallback;
}

const PdfToSvgPage: React.FC = () => {
  // 호스트 판별 로직
  const isOnRender = typeof window !== "undefined" && window.location.hostname.endsWith(".onrender.com");
  
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [quality, setQuality] = useState<"low" | "medium" | "high">("medium");
  const [scale, setScale] = useState(1.0);
  const [progress, setProgress] = useState(0);
  const [progressText, setProgressText] = useState("");
  // 타이머 ref 타입(브라우저 환경)
  const timerRef = useRef<number | null>(null);
  const downloadedRef = useRef(false);
  const [isLoading, setIsLoading] = useState(false);
  const [convertedFileUrl, setConvertedFileUrl] = useState<string | null>(null);
  const [convertedFileName, setConvertedFileName] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // SVG 벡터화 옵션 상태
  const [vectorColors, setVectorColors] = useState(128);  // 2~256
  const [vectorDetail, setVectorDetail] = useState(5);    // 1~10
  const [vectorDenoise, setVectorDenoise] = useState(50); // 0~100

  // 기존 코드에서 쓰던 이름들을 표준 상태로 연결(별칭)
  const errorMessage = error ?? "";
  const isConverting = isLoading;
  const conversionProgress = progress;
  const showSuccessMessage = !!convertedFileUrl;
  const successMessage = convertedFileName 
    ? `변환 완료! ${convertedFileName} 파일이 다운로드됩니다.`
    : "변환 완료!";

  // 언마운트 시 자동 정리
  useEffect(() => {
    return () => {
      if (timerRef.current) window.clearInterval(timerRef.current);
    };
  }, []);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      const file = event.target.files[0];
      if (file.size > 100 * 1024 * 1024) {
        setError('파일 크기는 100MB를 초과할 수 없습니다.');
        setSelectedFile(null);
setError(null);
      } else {
        setSelectedFile(file);
        setError(null);
      }
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setError(null);
    setProgress(0);
    setProgressText('');
    setConvertedFileUrl(null);
    setConvertedFileName('');
    // 타이머 정리할 때
    if (timerRef.current) {
      window.clearInterval(timerRef.current);
      timerRef.current = null;
    }
    if (fileInputRef.current) {
      fileInputRef.current.value = ""; // 파일 입력 초기화
    }
  };

  const handleConvert = async () => {
    if (!selectedFile) {
      setError('먼저 파일을 선택해주세요.');
      return;
    }

    downloadedRef.current = false;
    if (timerRef.current) { window.clearInterval(timerRef.current); timerRef.current = null; }
    setIsLoading(true); setProgress(1); setProgressText("PDF를 SVG로 변환 중..."); setError(null);

    const form = new FormData();
    form.append("file", selectedFile);
    form.append("quality", quality);
    form.append("vector_colors", String(vectorColors));
    form.append("vector_detail", String(vectorDetail));
    form.append("vector_denoise", String(vectorDenoise));
    form.append("scale", "1.0"); // 크기 x UI 제거했으므로 기본값만 전송

    try {
      const up = await fetch(`${API_BASE}/convert-async`, { method: "POST", body: form });
      if (!up.ok) { setError(await up.text()); setIsLoading(false); return; }
      const { job_id } = await up.json();

      // 타이머 시작할 때
      timerRef.current = window.setInterval(async () => {
        const r = await fetch(`${API_BASE}/job/${job_id}`);
        const j = await r.json();
        if (typeof j.progress === "number") setProgress(j.progress);
        if (j.message) setProgressText(j.message);

        if (j.status === "done") {
          if (timerRef.current) { window.clearInterval(timerRef.current); timerRef.current = null; }

          // 다운로드 URL(직접 요청)
          const downloadUrl = `${API_BASE}/download/${job_id}`;
          
          // 이름 계산(있으면 유지)
          const d = await fetch(`${API_BASE}/download/${job_id}`, { method: 'HEAD' }).catch(() => null);
          const ct = (d?.headers?.get("content-type") || "").toLowerCase?.() || "";
          const base = selectedFile.name.replace(/\.[^.]+$/, "");
          let name = safeGetFilename?.(d, base) || base; // d가 없으면 fallback
          const isZip = /zip/i.test(name) || ct.includes("zip");
          if (!/\.(zip|svg)$/i.test(name)) name = isZip ? `${name}.zip` : `${name}.svg`;
          
          setConvertedFileName(name);
          setProgress(100);
          setIsLoading(false);
          
          // 자동 다운로드(1회)
          if (!downloadedRef.current) {
            downloadedRef.current = true;
            triggerDirectDownload(downloadUrl);
          }
        }
        if (j.status === "error") {
          if (timerRef.current) { window.clearInterval(timerRef.current); timerRef.current = null; }
          setError(j.error || "변환 중 오류");
          setIsLoading(false);
        }
      }, 1500);
    } catch (error) {
      setError(error instanceof Error ? error.message : '변환 중 예상치 못한 문제 발생');
      setIsLoading(false);
    }
  };

  return (
    <>
      <PageTitle suffix="PDF → SVG" />
      <div className="w-full bg-white">
        {/* 상단 보라색 배경 섹션 */}
        <div className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white py-20 px-4 text-center relative overflow-hidden">
          {/* 애니메이션 배경 패턴 */}
          <div 
            className="absolute inset-0 opacity-30"
            style={{
              backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Cdefs%3E%3Cpattern id='grain' width='100' height='100' patternUnits='userSpaceOnUse'%3E%3Ccircle cx='12' cy='8' r='0.6' fill='%23ffffff' opacity='0.18'/%3E%3Ccircle cx='37' cy='23' r='1.8' fill='%23ffffff' opacity='0.06'/%3E%3Ccircle cx='68' cy='15' r='0.9' fill='%23ffffff' opacity='0.14'/%3E%3Ccircle cx='91' cy='42' r='1.3' fill='%23ffffff' opacity='0.09'/%3E%3Ccircle cx='24' cy='56' r='0.7' fill='%23ffffff' opacity='0.16'/%3E%3Ccircle cx='55' cy='73' r='1.5' fill='%23ffffff' opacity='0.07'/%3E%3Ccircle cx='83' cy='88' r='1.1' fill='%23ffffff' opacity='0.11'/%3E%3Ccircle cx='6' cy='34' r='2.0' fill='%23ffffff' opacity='0.05'/%3E%3Ccircle cx='45' cy='47' r='0.8' fill='%23ffffff' opacity='0.13'/%3E%3Ccircle cx='72' cy='61' r='1.2' fill='%23ffffff' opacity='0.10'/%3E%3Ccircle cx='18' cy='79' r='0.5' fill='%23ffffff' opacity='0.19'/%3E%3Ccircle cx='63' cy='29' r='1.7' fill='%23ffffff' opacity='0.08'/%3E%3Ccircle cx='89' cy='18' r='0.9' fill='%23ffffff' opacity='0.15'/%3E%3Ccircle cx='31' cy='91' r='1.4' fill='%23ffffff' opacity='0.12'/%3E%3Ccircle cx='76' cy='5' r='0.6' fill='%23ffffff' opacity='0.17'/%3E%3Ccircle cx='9' cy='67' r='1.6' fill='%23ffffff' opacity='0.06'/%3E%3Ccircle cx='52' cy='12' r='1.0' fill='%23ffffff' opacity='0.14'/%3E%3Ccircle cx='95' cy='76' r='0.8' fill='%23ffffff' opacity='0.11'/%3E%3C/pattern%3E%3C/defs%3E%3Crect width='100' height='100' fill='url(%23grain)'/%3E%3C/svg%3E")`,
              backgroundRepeat: 'repeat',
              animation: 'float 20s ease-in-out infinite'
            }}
          />
          
          <div className="container mx-auto relative z-10">
              <div className="flex justify-center items-center gap-4 mb-4">
                <svg className="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                <h1 className="text-4xl font-bold">PDF → SVG 변환기</h1>
              </div>
              <p className="text-lg opacity-90 max-w-2xl mx-auto">AI 기반 PDF to SVG 변환 서비스로 문서를 벡터 이미지 파일로 쉽게 변환하세요.</p>
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
              <h2 className="text-2xl font-semibold text-gray-800">PDF → SVG 변환기</h2>
              <p className="text-gray-500">벡터 이미지 파일 변환</p>
            </div>
            
            {!selectedFile ? (
              // 파일 선택 전 UI
              <label htmlFor="file-upload" className="block border-2 border-dashed border-gray-300 rounded-lg p-10 text-center cursor-pointer hover:border-blue-500 hover:bg-gray-50 transition-colors">
                <input id="file-upload" ref={fileInputRef} type="file" accept=".pdf" onChange={handleFileChange} className="hidden" />
                <p className="font-semibold text-gray-700">파일을 선택하세요</p>
                <p className="text-sm text-gray-500 mt-1">PDF 파일을 클릭하여 선택 (최대 100MB)</p>
              </label>
            ) : (
              // 파일 선택 후 UI
              <div className="space-y-6">
                <div>
                  <p className="text-gray-700"><span className="font-semibold">파일명:</span> {selectedFile.name}</p>
                  <p className="text-gray-700"><span className="font-semibold">크기:</span> {formatFileSize(selectedFile.size)}</p>
                </div>
                
                {/* 변환 품질 선택 */}
                <div className="space-y-2 mb-4">
                  <p className="font-medium">변환 품질 선택:</p>
                  <label className="flex items-center gap-2">
                    <input type="radio" name="q" value="low"
                      checked={quality === "low"} onChange={() => setQuality("low")} />
                    <span>저품질 (품질이 낮고 파일이 더 컴팩트함)</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input type="radio" name="q" value="medium"
                      checked={quality === "medium"} onChange={() => setQuality("medium")} />
                    <span>중간 품질 (중간 품질 및 파일 크기)</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input type="radio" name="q" value="high"
                      checked={quality === "high"} onChange={() => setQuality("high")} />
                    <span>고품질 (더 높은 품질, 더 큰 파일 크기)</span>
                  </label>
                </div>

                {/* SVG 벡터화 옵션 */}
                <fieldset className="mt-4 rounded-xl border border-gray-200 bg-gray-50 p-4">
                  <legend className="px-1 text-sm font-semibold text-gray-700">SVG 벡터화 옵션</legend>

                  {/* 색상 수 */}
                  <div className="mt-3 mb-4">
                    <div className="flex justify-between text-sm mb-1">
                      <span>색상 수: {vectorColors}</span>
                      <span className="text-gray-400">2-256</span>
                    </div>
                    <input 
                      type="range" 
                      min={2} 
                      max={256} 
                      step={1} 
                      value={vectorColors} 
                      onChange={(e) => setVectorColors(Math.min(256, Math.max(2, Number(e.target.value))))} 
                      className="w-full" 
                    />
                    <p className="mt-1 text-xs text-gray-500">
                      변환될 SVG 파일에 사용될 색상의 개수를 조절합니다. (단순한 로고, 아이콘에 효과적)
                    </p>
                  </div>

                  {/* 상세 수준 */}
                  <div className="mb-4">
                    <div className="flex justify-between text-sm mb-1">
                      <span>상세 수준: {vectorDetail}</span>
                      <span className="text-gray-400">1-10</span>
                    </div>
                    <input 
                      type="range" 
                      min={1} 
                      max={10} 
                      step={1} 
                      value={vectorDetail} 
                      onChange={(e) => setVectorDetail(Math.min(10, Math.max(1, Number(e.target.value))))} 
                      className="w-full" 
                    />
                    <p className="mt-1 text-xs text-gray-500">
                      원본 이미지의 외곽선을 얼마나 정교하게 따라 그릴지 결정합니다.
                    </p>
                  </div>

                  {/* 노이즈 억제 */}
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>노이즈 억제: {vectorDenoise}%</span>
                      <span className="text-gray-400">0-100%</span>
                    </div>
                    <input 
                      type="range" 
                      min={0} 
                      max={100} 
                      step={1} 
                      value={vectorDenoise} 
                      onChange={(e) => setVectorDenoise(Math.min(100, Math.max(0, Number(e.target.value))))} 
                      className="w-full" 
                    />
                    <p className="mt-1 text-xs text-gray-500">
                      이미지의 작은 점이나 잡티를 무시하여 더 깔끔한 결과물을 만듭니다.
                    </p>
                  </div>
                </fieldset>

                <div className="flex gap-4">
                  <button onClick={handleConvert} disabled={isLoading} className="flex-1 text-white px-6 py-3 rounded-lg text-lg font-semibold disabled:bg-gray-400 disabled:cursor-not-allowed" style={{background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'}} onMouseEnter={(e) => e.currentTarget.style.background = 'linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%)'} onMouseLeave={(e) => e.currentTarget.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'}>
                    {isLoading ? '변환 중...' : '변환하기'}
                  </button>
                  <button onClick={handleReset} disabled={isLoading} className="flex-1 bg-gray-600 text-white px-6 py-3 rounded-lg text-lg font-semibold hover:bg-gray-700 disabled:bg-gray-400 disabled:cursor-not-allowed">
                    파일 초기화
                  </button>
                </div>

              </div>
            )}
            
            {error && <p className="mt-4 text-center text-red-500">{error}</p>}
            
            {convertedFileName && (
              <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                <div className="flex items-center justify-between">
                  <span className="text-green-700 font-medium">변환 완료! {convertedFileName}</span>
                  <div className="flex gap-2">
                    {!isOnRender && convertedFileUrl && convertedFileName && (
                      <button 
                        className="px-4 py-2 rounded bg-indigo-600 text-white hover:bg-indigo-700"
                        onClick={() => triggerDownload(convertedFileUrl!, convertedFileName!)}
                      >
                        파일 다시 받기
                      </button>
                    )}
                    {convertedFileUrl && (
                      <a
                        href={convertedFileUrl}
                        download={convertedFileName}
                        className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
                      >
                        다운로드
                      </a>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* PDF를 SVG로 변환하는 방법 가이드 섹션 */}
        <div className="bg-gray-50 py-16">
          <div className="max-w-4xl mx-auto px-4">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold text-gray-800 mb-4">PDF를 SVG로 변환하는 방법</h2>
              <p className="text-gray-600">간단한 4단계로 PDF를 벡터 이미지 파일로 변환하세요</p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {/* 1단계: PDF 업로드 */}
              <div className="bg-white rounded-lg p-6 shadow-md hover:shadow-lg transition-shadow">
                <div className="flex items-center justify-center w-12 h-12 bg-blue-100 rounded-full mb-4 mx-auto">
                  <span className="text-xl font-bold text-blue-600">1️⃣</span>
                </div>
                <h3 className="text-lg font-semibold text-gray-800 mb-2 text-center">PDF 업로드</h3>
                <p className="text-gray-600 text-sm text-center">PDF 파일을 드래그하거나 "파일 선택" 버튼을 클릭하여 업로드해주세요.</p>
              </div>

              {/* 2단계: 변환 옵션 선택 */}
              <div className="bg-white rounded-lg p-6 shadow-md hover:shadow-lg transition-shadow">
                <div className="flex items-center justify-center w-12 h-12 bg-green-100 rounded-full mb-4 mx-auto">
                  <span className="text-xl font-bold text-green-600">2️⃣</span>
                </div>
                <h3 className="text-lg font-semibold text-gray-800 mb-2 text-center">변환 옵션 선택 (선택 사항)</h3>
                <p className="text-gray-600 text-sm text-center">빠른 변환 또는 고품질 변환 등 원하는 품질 옵션을 선택해주세요.</p>
              </div>

              {/* 3단계: 자동 변환 시작 */}
              <div className="bg-white rounded-lg p-6 shadow-md hover:shadow-lg transition-shadow">
                <div className="flex items-center justify-center w-12 h-12 bg-yellow-100 rounded-full mb-4 mx-auto">
                  <span className="text-xl font-bold text-yellow-600">3️⃣</span>
                </div>
                <h3 className="text-lg font-semibold text-gray-800 mb-2 text-center">자동 변환 시작</h3>
                <p className="text-gray-600 text-sm text-center">"변환하기" 버튼을 클릭하세요. AI 기반 엔진이 문서를 SVG 파일로 변환합니다.</p>
              </div>

              {/* 4단계: SVG 파일 다운로드 */}
              <div className="bg-white rounded-lg p-6 shadow-md hover:shadow-lg transition-shadow">
                <div className="flex items-center justify-center w-12 h-12 bg-purple-100 rounded-full mb-4 mx-auto">
                  <span className="text-xl font-bold text-purple-600">4️⃣</span>
                </div>
                <h3 className="text-lg font-semibold text-gray-800 mb-2 text-center">SVG 파일 다운로드</h3>
                <p className="text-gray-600 text-sm text-center">변환이 완료되면, 벡터 이미지(.svg) 파일을 즉시 다운로드할 수 있습니다.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default PdfToSvgPage;