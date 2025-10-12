import React, { useState, useRef, useEffect } from 'react';
import PageTitle from '../shared/PageTitle';
import { getPdfPageCount, directPostAndDownload, triggerDirectDownload } from '@/utils/pdfUtils';

// Force Vercel deployment - Updated: 2024-12-30 16:16 - GITHUB INTEGRATION

// 버튼 클래스 상수
const BTN_PRIMARY = 
  "w-full sm:w-auto px-6 py-4 rounded-xl text-base md:text-lg font-semibold text-white " + 
  "bg-gradient-to-r from-indigo-500 to-purple-500 hover:from-indigo-600 hover:to-purple-600 " + 
  "shadow transition disabled:opacity-60 disabled:cursor-not-allowed";

const BTN_SECONDARY = 
  "w-full sm:w-auto px-6 py-4 rounded-xl text-base md:text-lg font-semibold text-white " + 
  "bg-gray-700 hover:bg-gray-800 shadow transition disabled:opacity-60 disabled:cursor-not-allowed";

const API_PROXY_BASE = "/api/pdf-pptx";
const API_DIRECT_BASE = import.meta.env.PROD 
  ? "https://pdf-pptx.onrender.com" 
  : "/api/pdf-pptx";

// 임계값(조정 가능)
const SYNC_MAX_SIZE = 8 * 1024 * 1024; // 8MB 이하
const SYNC_MAX_PAGES = 20;             // 20페이지 이하

// 공통 유틸리티 함수들 (import된 함수들 사용)

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


const PdfToPptxPage: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [speed, setSpeed] = useState<"fast" | "standard">("fast");
  const [isLoading, setIsLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [showSuccessMessage, setShowSuccessMessage] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [convertedFileUrl, setConvertedFileUrl] = useState<string | null>(null);
  const [convertedFileName, setConvertedFileName] = useState<string>('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 다운로드 방지 및 타이머 관리용 refs
  const timerRef = useRef<number | null>(null);
  const downloadedRef = useRef(false);

  // 진행률 상태
  const [progressText, setProgressText] = useState("");

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setErrorMessage('');
      setShowSuccessMessage(false);
      setConvertedFileUrl(null);
      setConvertedFileName('');
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setErrorMessage('');
    setShowSuccessMessage(false);
    setConvertedFileUrl(null);
    setConvertedFileName('');
    setProgress(0);
    setIsLoading(false);
    
    // 타이머 정리
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  async function handleConvert() {
    if (!selectedFile) return;
    setIsLoading(true);
    setProgress(1);
    setProgressText("PDF를 PPTX로 변환 중...");
    setErrorMessage("");
    downloadedRef.current = false;

    try {
      const form = new FormData();
      form.append("file", selectedFile);
      form.append("quality", speed === "fast" ? "low" : "standard"); // doc과 동일 키
      form.append("scale", "1.0");

      const pages = await getPdfPageCount(selectedFile).catch(() => 0);
      const useSync = selectedFile.size <= SYNC_MAX_SIZE && (pages === 0 || pages <= SYNC_MAX_PAGES);

      if (useSync) {
        // 동기식: onrender 직행 (/convert)
        const base = selectedFile.name.replace(/\.[^.]+$/, "");
        const shown = await directPostAndDownload(`${API_DIRECT_BASE}/convert`, form, `${base}.pptx`);
        setConvertedFileName(shown);
        setProgress(100);
        setIsLoading(false);
        setShowSuccessMessage(true);
        setSuccessMessage(`변환 완료! 파일명: ${shown}로 다운로드됩니다.`);
        return;
      }

      // 비동기(/api 프록시 유지)
      const up = await fetch(`${API_PROXY_BASE}/convert-async`, { method: "POST", body: form });
      if (!up.ok) throw new Error(`요청 실패(${up.status})`);
      const { job_id } = await up.json();

      if (timerRef.current) { window.clearInterval(timerRef.current); timerRef.current = null; }
      timerRef.current = window.setInterval(async () => {
        const r = await fetch(`${API_PROXY_BASE}/job/${job_id}`);
        const j = await r.json();
        if (typeof j.progress === "number") setProgress(j.progress);
        if (j.message) setProgressText(j.message);

        if (j.status === "done") {
          if (timerRef.current) { window.clearInterval(timerRef.current); timerRef.current = null; }
          const downloadUrl = `${API_PROXY_BASE}/download/${job_id}`; // 주의: /job/.../download 아님
          const base = selectedFile.name.replace(/\.[^.]+$/, "");
          setConvertedFileUrl(downloadUrl);
          setConvertedFileName(`${base}.pptx`);
          setProgress(100);
          setIsLoading(false);
          setShowSuccessMessage(true);
          setSuccessMessage(`변환 완료! 파일명: ${base}.pptx로 다운로드됩니다.`);
          if (!downloadedRef.current) { downloadedRef.current = true; triggerDirectDownload(downloadUrl); }
        }
        if (j.status === "error") {
          if (timerRef.current) { window.clearInterval(timerRef.current); timerRef.current = null; }
          setErrorMessage(j.error || "변환 중 오류"); setIsLoading(false);
        }
      }, 1500);
    } catch (e: any) {
      setErrorMessage(e?.message || "변환 중 오류");
      setIsLoading(false);
    }
  }

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
      <PageTitle suffix="PDF → PowerPoint" />
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
              <svg className="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
              <h1 className="text-4xl font-bold">PDF → PPTX 변환기</h1>
            </div>
            <p className="text-lg opacity-90 max-w-2xl mx-auto">AI 기반 PDF to PPTX 변환 서비스로 문서를 프레젠테이션 파일로 쉽게 변환하세요.</p>
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
            <h2 className="text-2xl font-semibold text-gray-800">PDF → PPTX 변환기</h2>
            <p className="text-gray-500">프레젠테이션 파일 변환</p>
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
              
              {/* 변환 품질 선택: doc과 동일 */}
              <div className="space-y-2 mb-4">
                <p className="font-medium">변환 품질 선택:</p>
                <label className="flex items-center gap-2">
                  <input type="radio" name="speed" value="fast" checked={speed==="fast"} onChange={() => setSpeed("fast")} />
                  <span>빠른 변환 (권장)</span>
                </label>
                <label className="flex items-center gap-2">
                  <input type="radio" name="speed" value="standard" checked={speed==="standard"} onChange={() => setSpeed("standard")} />
                  <span>표준 변환</span>
                </label>
              </div>

              {/* 변환 진행률 표시 - pdf-doc과 동일한 스타일 */}
              <div className="mt-4">
                <div className="flex justify-between text-sm mb-1">
                  <span>변환 진행률</span>
                  <span>{Math.max(0, Math.min(100, Math.round(progress)))}%</span>
                </div>
                <div className="h-2 bg-gray-200 rounded">
                  <div className="h-2 bg-indigo-500 rounded transition-[width] duration-300" style={{ width: `${Math.max(2, progress)}%` }} />
                </div>
                {isLoading && (
                  <div className="mt-2 text-sm text-gray-500">
                    ⏳ PDF를 PPTX로 변환 중...
                  </div>
                )}
              </div>

              {/* 성공 메시지 */}
              {showSuccessMessage && (
                <div className="bg-green-50 border border-green-200 text-green-800 px-4 py-3 rounded-lg mb-4">
                  <div className="flex items-center">
                    <svg className="w-5 h-5 mr-2 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    <p>{successMessage}</p>
                  </div>
                </div>
              )}

              <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 gap-4">
                <button 
                  type="button" 
                  disabled={isLoading || !selectedFile} 
                  onClick={handleConvert}
                  className={BTN_PRIMARY}
                >
                  {isLoading ? "변환 중..." : "변환하기"}
                </button>
                <button 
                  type="button" 
                  disabled={isLoading} 
                  onClick={handleReset}
                  className={BTN_SECONDARY}
                >
                  파일 초기화
                </button>
              </div>
            </div>
          )}
          
          {errorMessage && <p className="mt-4 text-center text-red-500">{errorMessage}</p>}
        </div>
      </div>
      </div>
    </>
  );
};

export default PdfToPptxPage;