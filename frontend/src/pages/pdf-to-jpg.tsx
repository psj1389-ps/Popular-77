import React, { useState, useRef, useEffect } from 'react';
import PageTitle from '../shared/PageTitle';

// PDF.js (표준 빌드로 변경 - Vercel 호환성 개선)
import { getDocument, GlobalWorkerOptions } from "pdfjs-dist";

// 워커 설정을 조건부로 처리 (SSR 환경 고려)
if (typeof window !== "undefined") {
  GlobalWorkerOptions.workerSrc = new URL(
    /* @vite-ignore */ "pdfjs-dist/build/pdf.worker.min.js",
    import.meta.url
  ).toString();
}

// Force Vercel deployment - Updated: 2024-12-30 16:15 - GITHUB INTEGRATION

const API_BASE = "/api/pdf-jpg";

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

// 응답 처리 공통 유틸
function safeGetFilename(res: Response, fallback: string) {
  const cd = res.headers.get("content-disposition") || "";
  const star = /filename\*\=UTF-8''([^;]+)/i.exec(cd);
  if (star?.[1]) {
    try { return decodeURIComponent(star[1]); } catch {}
  }
  const normal = /filename="?([^";]+)"?/i.exec(cd);
  return normal?.[1] || fallback;
}

// 에러 메시지 파싱
async function getErrorMessage(res: Response) {
  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) {
    const j = await res.json().catch(() => null);
    if (j?.error) return j.error; // 서버가 { error: "메시지" }로 내려줄 때
  }
  const t = await res.text().catch(() => "");
  return t || `요청 실패(${res.status})`;
}

const PdfToJpgPage: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [quality, setQuality] = useState<"low" | "medium" | "high">("medium"); // JPG와 동일한 3단계 품질
  const [scale, setScale] = useState(0.5); // 크기 배율 (0.2 ~ 2.0)
  const [isConverting, setIsConverting] = useState(false);
  const [conversionProgress, setConversionProgress] = useState(0);
  const [showSuccessMessage, setShowSuccessMessage] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [convertedFileUrl, setConvertedFileUrl] = useState<string | null>(null);
  const [convertedFileName, setConvertedFileName] = useState<string>('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 다운로드 방지 및 타이머 관리용 refs
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const downloadedRef = useRef(false);

  // 진행률 상태
  const [progress, setProgress] = useState(0);
  const [progressText, setProgressText] = useState("");

  // 픽셀 기준(1.0 배율일 때의 가로/세로 픽셀)
  const [baseSize, setBaseSize] = useState<{ width: number; height: number } | null>(null);

  // PDF 첫 페이지 크기 측정
  async function measurePdfFirstPage(file: File): Promise<{ width: number; height: number } | null> {
    try {
      const buf = await file.arrayBuffer();
      const pdf = await getDocument({ data: buf }).promise;
      const page = await pdf.getPage(1);
      const viewport = page.getViewport({ scale: 1 }); // 1.0 기준
      const size = { width: Math.round(viewport.width), height: Math.round(viewport.height) };
      console.log("[JPG] PDF 첫 페이지 크기:", size); // 확인용
      return size;
    } catch (e) {
      console.warn("[JPG] PDF 크기 측정 실패:", e);
      return null; // 실패 시 표시 생략
    }
  }

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setErrorMessage('');
      setShowSuccessMessage(false);
      setConvertedFileUrl(null);
      setConvertedFileName('');
      
      // PDF 크기 측정
      measurePdfFirstPage(file).then(size => {
        setBaseSize(size);
      });
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setErrorMessage('');
    setShowSuccessMessage(false);
    setConvertedFileUrl(null);
    setConvertedFileName('');
    setConversionProgress(0);
    setIsConverting(false);
    setBaseSize(null);
    
    // 타이머 정리
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleConvert = async () => {
    if (!selectedFile) return;
    
    setErrorMessage('');
    setShowSuccessMessage(false);
    setConvertedFileUrl(null);
    setConvertedFileName('');
    
    const form = new FormData();
    form.append("file", selectedFile);
    form.append("quality", quality);
    form.append("scale", String(scale));

    setIsConverting(true);
    setProgress(1);
    setProgressText("PDF를 JPG로 변환 중...");
    downloadedRef.current = false;
    if (timerRef.current) { 
      clearInterval(timerRef.current); 
      timerRef.current = null; 
    }

    try {
      const up = await fetch(`${API_BASE}/convert-async`, { method: "POST", body: form });
      if (!up.ok) { 
        setErrorMessage(await up.text()); 
        setIsConverting(false); 
        return; 
      }
      const { job_id } = await up.json();

      timerRef.current = setInterval(async () => {
        try {
          const r = await fetch(`${API_BASE}/job/${job_id}`);
          const j = await r.json();
          if (typeof j.progress === "number") setProgress(j.progress);
          if (j.message) setProgressText(j.message);

          if (j.status === "done") {
            if (downloadedRef.current) return;
            downloadedRef.current = true;
            if (timerRef.current) { 
              clearInterval(timerRef.current); 
              timerRef.current = null; 
            }

            const d = await fetch(`${API_BASE}/download/${job_id}`);
            if (!d.ok) { 
              setErrorMessage(await d.text()); 
              setIsConverting(false); 
              return; 
            }

            const contentType = (d.headers.get("content-type") || "").toLowerCase();
            const base = selectedFile.name.replace(/\.pdf$/i, "");
            let name = safeGetFilename(d, base);
            const isZip = contentType.includes("zip") || /\.zip$/i.test(name);
            if (!/\.(zip|jpg|jpeg)$/i.test(name)) name = isZip ? `${name}.zip` : `${name}.jpg`;

            const blob = await d.blob();
            const url = URL.createObjectURL(blob);
            setConvertedFileUrl(url);
            setConvertedFileName(name);
            setProgress(100);
            setIsConverting(false);
            
            // 성공 메시지 표시
            setSuccessMessage(`변환 완료! 파일명: ${name}로 다운로드됩니다.`);
            setShowSuccessMessage(true);
            
            // 잠시 후 다운로드 시작
            setTimeout(() => {
              downloadBlob(blob, name);
            }, 1000);
          }
          if (j.status === "error") {
            if (timerRef.current) { 
              clearInterval(timerRef.current); 
              timerRef.current = null; 
            }
            setErrorMessage(j.error || "변환 중 오류");
            setIsConverting(false);
          }
        } catch (error) {
          console.error("Polling error:", error);
        }
      }, 1500);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : '변환 중 예상치 못한 문제 발생');
      setIsConverting(false);
    }
  };

  // 컴포넌트 언마운트 시 타이머 정리
  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, []);

  return (
    <>
      <PageTitle suffix="PDF → JPG" />
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
              <svg className="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
              <h1 className="text-4xl font-bold">PDF → JPG 변환기</h1>
            </div>
            <p className="text-lg opacity-90 max-w-2xl mx-auto">고화질 이미지 변환 서비스로 PDF를 JPG 이미지로 쉽게 변환하세요.</p>
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
            <h2 className="text-2xl font-semibold text-gray-800">PDF → JPG 변환기</h2>
            <p className="text-gray-500">고화질 이미지 변환</p>
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
              
              <div>
                <h3 className="font-semibold text-gray-800 mb-2">변환 품질 선택:</h3>
                <div className="space-y-2">
                  <label className="flex items-center">
                    <input type="radio" name="quality" value="low" checked={quality === 'low'} onChange={(e) => setQuality(e.target.value as "low" | "medium" | "high")} className="w-4 h-4 text-blue-600" />
                    <span className="ml-2 text-gray-700">저품질 (품질이 낮고 파일이 더 컴팩트함)</span>
                  </label>
                  <label className="flex items-center">
                    <input type="radio" name="quality" value="medium" checked={quality === 'medium'} onChange={(e) => setQuality(e.target.value as "low" | "medium" | "high")} className="w-4 h-4 text-blue-600" />
                    <span className="ml-2 text-gray-700">중간 품질 (중간 품질 및 파일 크기)</span>
                  </label>
                  <label className="flex items-center">
                    <input type="radio" name="quality" value="high" checked={quality === 'high'} onChange={(e) => setQuality(e.target.value as "low" | "medium" | "high")} className="w-4 h-4 text-blue-600" />
                    <span className="ml-2 text-gray-700">고품질 (더 높은 품질, 더 큰 파일 크기)</span>
                  </label>
                </div>
              </div>

              {/* 고급 옵션 - 크기 조정 */}
              <div>
                <h3 className="font-semibold text-gray-800 mb-2">고급 옵션:</h3>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-sm font-medium text-gray-700">크기 x</label>
                    <span className="text-sm text-gray-600">{scale}x</span>
                  </div>
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
                  
                  {/* 픽셀 크기 표시 */}
                  {baseSize && (
                    <div className="mt-2 text-sm text-gray-600">
                      예상 크기: {Math.round(baseSize.width * scale)} × {Math.round(baseSize.height * scale)} 픽셀
                    </div>
                  )}
                </div>
              </div>

              {/* 성공 메시지 */}
              {showSuccessMessage && (
                <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                  <div className="flex items-center">
                    <svg className="w-5 h-5 text-green-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    <span className="text-green-700 font-medium">{successMessage}</span>
                  </div>
                </div>
              )}

              {/* 진행률 바 - BMP와 동일한 스타일 */}
              {isConverting && (
                <div className="mt-4">
                  <div className="flex justify-between text-sm mb-1">
                    <span>변환 진행률</span>
                    <span>{progress}%</span>
                  </div>
                  <div className="h-2 bg-gray-200 rounded">
                    <div 
                      className="h-2 bg-indigo-500 rounded transition-[width] duration-300"
                      style={{ width: `${Math.max(2, progress)}%` }}
                    />
                  </div>
                  {isConverting && (
                    <div className="mt-2 text-sm text-gray-500">⏳ {progressText || "변환 중..."}</div>
                  )}
                </div>
              )}

              <div className="flex gap-4">
                <button onClick={handleConvert} disabled={isConverting} className="flex-1 text-white px-6 py-3 rounded-lg text-lg font-semibold disabled:bg-gray-400 disabled:cursor-not-allowed" style={{background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'}} onMouseEnter={(e) => e.currentTarget.style.background = 'linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%)'} onMouseLeave={(e) => e.currentTarget.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'}>
                  {isConverting ? '변환 중...' : '변환하기'}
                </button>
                <button onClick={handleReset} disabled={isConverting} className="flex-1 bg-gray-600 text-white px-6 py-3 rounded-lg text-lg font-semibold hover:bg-gray-700 disabled:bg-gray-400 disabled:cursor-not-allowed">
                  파일 초기화
                </button>
              </div>
            </div>
          )}
          
          {errorMessage && <p className="mt-4 text-center text-red-500">{errorMessage}</p>}
        </div>
      </div>

      {/* PDF를 이미지로 변환하는 방법 가이드 섹션 */}
      <div className="bg-gray-50 py-16">
        <div className="max-w-4xl mx-auto px-4">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-800 mb-4">PDF를 이미지로 변환하는 방법</h2>
            <p className="text-gray-600">간단한 4단계로 PDF를 고품질 이미지로 변환하세요</p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* 1단계: PDF 업로드 */}
            <div className="bg-white rounded-lg p-6 shadow-md hover:shadow-lg transition-shadow">
              <div className="flex items-center justify-center w-12 h-12 bg-blue-100 rounded-full mb-4 mx-auto">
                <span className="text-xl font-bold text-blue-600">1️⃣</span>
              </div>
              <h3 className="text-lg font-semibold text-gray-800 mb-2 text-center">PDF 업로드</h3>
              <p className="text-gray-600 text-sm text-center">PDF 파일을 드래그하거나 클릭하여 선택해주세요.</p>
            </div>

            {/* 2단계: 설정 선택 */}
            <div className="bg-white rounded-lg p-6 shadow-md hover:shadow-lg transition-shadow">
              <div className="flex items-center justify-center w-12 h-12 bg-green-100 rounded-full mb-4 mx-auto">
                <span className="text-xl font-bold text-green-600">2️⃣</span>
              </div>
              <h3 className="text-lg font-semibold text-gray-800 mb-2 text-center">설정을 선택하세요</h3>
              <p className="text-gray-600 text-sm text-center">품질, 용량 및 해상도를 선택해주세요.</p>
            </div>

            {/* 3단계: 자동 변환 */}
            <div className="bg-white rounded-lg p-6 shadow-md hover:shadow-lg transition-shadow">
              <div className="flex items-center justify-center w-12 h-12 bg-yellow-100 rounded-full mb-4 mx-auto">
                <span className="text-xl font-bold text-yellow-600">3️⃣</span>
              </div>
              <h3 className="text-lg font-semibold text-gray-800 mb-2 text-center">자동 변환</h3>
              <p className="text-gray-600 text-sm text-center">잠시만 기다리면 변환이 시작됩니다.</p>
            </div>

            {/* 4단계: 다운로드 */}
            <div className="bg-white rounded-lg p-6 shadow-md hover:shadow-lg transition-shadow">
              <div className="flex items-center justify-center w-12 h-12 bg-purple-100 rounded-full mb-4 mx-auto">
                <span className="text-xl font-bold text-purple-600">4️⃣</span>
              </div>
              <h3 className="text-lg font-semibold text-gray-800 mb-2 text-center">다운로드</h3>
              <p className="text-gray-600 text-sm text-center">개별 페이지 또는 전체 다운로드 선택.</p>
            </div>
          </div>
        </div>
      </div>
      </div>
    </>
  );
};

export default PdfToJpgPage;