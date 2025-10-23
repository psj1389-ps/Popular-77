import React, { useState, useRef, useEffect } from 'react';
import { Helmet } from 'react-helmet-async';
import { safeGetFilename, downloadBlob } from '@/utils/pdfUtils';

const API_BASE = import.meta.env.PROD 
  ? "https://docx-pdf-docker.onrender.com" 
  : "http://127.0.0.1:10000";

const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// 에러 메시지 파싱
async function getErrorMessage(res: Response) {
  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) {
    const j = await res.json().catch(() => null);
    if (j?.error) return j.error;
  }
  const t = await res.text().catch(() => "");
  return t || `요청 실패(${res.status})`;
}

const DocxPdfPage: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [quality, setQuality] = useState<"fast" | "standard">("fast");
  const [isConverting, setIsConverting] = useState(false);
  const [conversionProgress, setConversionProgress] = useState(0);
  const [showSuccessMessage, setShowSuccessMessage] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [convertedFileUrl, setConvertedFileUrl] = useState<string | null>(null);
  const [convertedFileName, setConvertedFileName] = useState<string>('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      // DOCX 파일만 허용
      if (!file.name.toLowerCase().endsWith('.docx')) {
        setErrorMessage('DOCX 파일만 업로드할 수 있습니다.');
        return;
      }
      
      setSelectedFile(file);
      setErrorMessage('');
      setShowSuccessMessage(false);
      setConvertedFileUrl(null);
      setConvertedFileName('');
    }
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    const file = event.dataTransfer.files[0];
    if (file) {
      // DOCX 파일만 허용
      if (!file.name.toLowerCase().endsWith('.docx')) {
        setErrorMessage('DOCX 파일만 업로드할 수 있습니다.');
        return;
      }
      
      setSelectedFile(file);
      setErrorMessage('');
      setShowSuccessMessage(false);
      setConvertedFileUrl(null);
      setConvertedFileName('');
    }
  };

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
  };

  const handleReset = () => {
    setSelectedFile(null);
    setErrorMessage('');
    setShowSuccessMessage(false);
    setConvertedFileUrl(null);
    setConvertedFileName('');
    setConversionProgress(0);
    setIsConverting(false);
    
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
    setIsConverting(true);
    setConversionProgress(0);

    // 부드러운 진행률 애니메이션을 위한 함수
    const smoothProgressUpdate = (targetProgress: number, duration: number = 1000) => {
      return new Promise<void>((resolve) => {
        const startProgress = conversionProgress;
        const progressDiff = targetProgress - startProgress;
        const startTime = Date.now();
        
        const updateProgress = () => {
          const elapsed = Date.now() - startTime;
          const progress = Math.min(elapsed / duration, 1);
          const easeOutProgress = 1 - Math.pow(1 - progress, 3); // ease-out 효과
          const currentProgress = startProgress + (progressDiff * easeOutProgress);
          
          setConversionProgress(Math.round(currentProgress));
          
          if (progress < 1) {
            requestAnimationFrame(updateProgress);
          } else {
            resolve();
          }
        };
        
        requestAnimationFrame(updateProgress);
      });
    };

    const form = new FormData();
    form.append("file", selectedFile);
    form.append("quality", quality);

    try {
      // 초기 진행률을 천천히 15%까지 증가
      await smoothProgressUpdate(15, 800);
      
      const response = await fetch(`${API_BASE}/convert`, {
        method: "POST",
        body: form,
      });

      // 요청 완료 후 45%까지 증가
      await smoothProgressUpdate(45, 1200);

      if (!response.ok) {
        const errorText = await getErrorMessage(response);
        setErrorMessage(errorText);
        setIsConverting(false);
        setConversionProgress(0);
        return;
      }

      // 응답 처리 중 75%까지 증가
      await smoothProgressUpdate(75, 1000);

      const blob = await response.blob();
      if (blob.size === 0) {
        setErrorMessage('변환된 파일이 비어있습니다.');
        setIsConverting(false);
        setConversionProgress(0);
        return;
      }

      // 파일 처리 중 95%까지 증가
      await smoothProgressUpdate(95, 800);

      const filename = safeGetFilename(response, 
        selectedFile.name.replace(/\.(docx?)$/i, '.pdf')
      );

      setConvertedFileName(filename);
      setConvertedFileUrl(URL.createObjectURL(blob));
      setSuccessMessage(`변환 완료! 파일명: ${filename}로 다운로드됩니다.`);
      setShowSuccessMessage(true);
      
      // 최종 완료까지 부드럽게 증가
      await smoothProgressUpdate(100, 500);

      // 자동 다운로드
      downloadBlob(blob, filename);

    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : '변환 중 예상치 못한 문제가 발생했습니다.');
    } finally {
      setIsConverting(false);
    }
  };

  return (
    <>
      <Helmet>
        <title>DOCX → PDF 변환기 - 77-tools.xyz</title>
        <meta name="description" content="DOCX 파일을 PDF로 무료 변환. 빠르고 안전한 온라인 문서 변환 도구." />
      </Helmet>
      
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
              <svg className="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
              <h1 className="text-4xl font-bold">DOCX → PDF 변환기</h1>
            </div>
            <p className="text-lg opacity-90 max-w-2xl mx-auto">
              DOCX 문서를 PDF로 변환하여 어디서나 안전하게 공유하세요
            </p>
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
            <h2 className="text-2xl font-semibold text-gray-800">DOCX → PDF 변환기</h2>
            <p className="text-gray-500">안정적인 문서 변환 서비스</p>
          </div>
          
          {!selectedFile ? (
            // 파일 선택 전 UI
            <label htmlFor="file-upload" className="block border-2 border-dashed border-gray-300 rounded-lg p-10 text-center cursor-pointer hover:border-blue-500 hover:bg-gray-50 transition-colors">
              <input 
                id="file-upload" 
                ref={fileInputRef} 
                type="file" 
                accept=".docx" 
                onChange={handleFileChange} 
                className="hidden" 
              />
              <p className="font-semibold text-gray-700">파일을 선택하세요</p>
              <p className="text-sm text-gray-500 mt-1">DOCX 파일을 클릭하여 선택 (최대 100MB)</p>
            </label>
          ) : (
            // 파일 선택 후 UI
            <div className="space-y-6">
              {/* 선택된 파일 정보 */}
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-gray-800">{selectedFile.name}</p>
                    <p className="text-sm text-gray-500">{formatFileSize(selectedFile.size)}</p>
                  </div>
                  <div className="text-green-600">
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                </div>
              </div>

              {/* 변환 품질 선택 */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">변환 품질 선택:</label>
                <div className="space-y-2">
                  <label className="flex items-center gap-2">
                    <input
                      type="radio"
                      name="quality"
                      value="fast"
                      checked={quality === "fast"}
                      onChange={(e) => setQuality(e.target.value as "fast" | "standard")}
                    />
                    <span>빠른 변환 (권장)</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input
                      type="radio"
                      name="quality"
                      value="standard"
                      checked={quality === "standard"}
                      onChange={(e) => setQuality(e.target.value as "fast" | "standard")}
                    />
                    <span>표준 변환</span>
                  </label>
                </div>
              </div>

              {/* 성공 메시지 */}
              {showSuccessMessage && (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <div className="flex items-center">
                    <svg className="w-5 h-5 text-green-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <p className="text-green-800 font-medium">{successMessage}</p>
                  </div>
                </div>
              )}

              {/* 변환 진행률 표시 */}
              {isConverting && !showSuccessMessage && (
                <div className="mb-4">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm font-medium text-blue-700">변환 진행률</span>
                    <span className="text-sm font-medium text-blue-700">{Math.round(conversionProgress)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2.5">
                    <div 
                      className="bg-gradient-to-r from-purple-600 to-indigo-600 h-2.5 rounded-full transition-all duration-300 ease-out"
                      style={{ width: `${conversionProgress}%` }}
                    ></div>
                  </div>
                  <div className="flex items-center justify-center mt-3">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-purple-600 mr-2"></div>
                    <span className="text-sm text-gray-600">변환 중입니다... 잠시만 기다려주세요.</span>
                  </div>
                </div>
              )}

              {/* 버튼 영역 */}
              <div className="flex gap-4">
                <button onClick={handleConvert} disabled={isConverting} className="flex-1 text-white px-6 py-3 rounded-lg text-lg font-semibold disabled:bg-gray-400 disabled:cursor-not-allowed" style={{background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'}} onMouseEnter={(e) => e.currentTarget.style.background = 'linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%)'} onMouseLeave={(e) => e.currentTarget.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'}>
                  {isConverting ? '변환 중...' : 'PDF로 변환하기'}
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

      {/* 문서 변환 가이드 섹션 */}
      <div className="bg-gray-50 py-16">
        <div className="max-w-4xl mx-auto px-4">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-800 mb-4">
              DOCX → PDF 변환 가이드
            </h2>
            <p className="text-gray-600 text-lg">
              간단한 4단계로 DOCX 파일을 PDF로 변환하세요
            </p>
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            <div className="text-center">
              <div className="bg-purple-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-purple-600">1</span>
              </div>
              <h3 className="text-xl font-semibold text-gray-800 mb-2">파일 업로드</h3>
              <p className="text-gray-600">변환할 DOCX 파일을 선택하거나 드래그하여 업로드하세요.</p>
            </div>
            
            <div className="text-center">
              <div className="bg-purple-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-purple-600">2</span>
              </div>
              <h3 className="text-xl font-semibold text-gray-800 mb-2">변환 품질 선택</h3>
              <p className="text-gray-600">용도에 맞는 PDF 품질을 선택하세요. 표준 품질을 권장합니다.</p>
            </div>
            
            <div className="text-center">
              <div className="bg-purple-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-purple-600">3</span>
              </div>
              <h3 className="text-xl font-semibold text-gray-800 mb-2">자동 변환 시작</h3>
              <p className="text-gray-600">변환 버튼을 클릭하면 자동으로 DOCX가 PDF로 변환됩니다.</p>
            </div>
            
            <div className="text-center">
              <div className="bg-purple-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-purple-600">4</span>
              </div>
              <h3 className="text-xl font-semibold text-gray-800 mb-2">변환된 파일 다운로드</h3>
              <p className="text-gray-600">변환이 완료되면 PDF 파일이 자동으로 다운로드됩니다.</p>
            </div>
          </div>
        </div>
      </div>
      </div>
    </>
  );
};

export default DocxPdfPage;