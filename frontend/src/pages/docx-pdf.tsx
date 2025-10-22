import React, { useState, useRef, useEffect } from 'react';
import { Helmet } from 'react-helmet-async';

const API_BASE = "https://docx-pdf-g6zu.onrender.com";

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
    if (j?.error) return j.error;
  }
  const t = await res.text().catch(() => "");
  return t || `요청 실패(${res.status})`;
}

const DocxPdfPage: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [conversionMode, setConversionMode] = useState<"docx-to-pdf" | "pdf-to-docx">("docx-to-pdf");
  const [quality, setQuality] = useState<"low" | "standard" | "high">("standard");
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
      // 파일 형식 검증
      const isValidFile = conversionMode === "docx-to-pdf" 
        ? file.name.toLowerCase().endsWith('.docx')
        : file.name.toLowerCase().endsWith('.pdf');
      
      if (!isValidFile) {
        const expectedFormat = conversionMode === "docx-to-pdf" ? "DOCX" : "PDF";
        setErrorMessage(`${expectedFormat} 파일만 업로드할 수 있습니다.`);
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
      const isValidFile = conversionMode === "docx-to-pdf" 
        ? file.name.toLowerCase().endsWith('.docx')
        : file.name.toLowerCase().endsWith('.pdf');
      
      if (!isValidFile) {
        const expectedFormat = conversionMode === "docx-to-pdf" ? "DOCX" : "PDF";
        setErrorMessage(`${expectedFormat} 파일만 업로드할 수 있습니다.`);
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

  const handleModeToggle = () => {
    setConversionMode(prev => prev === "docx-to-pdf" ? "pdf-to-docx" : "docx-to-pdf");
    handleReset();
  };

  const handleConvert = async () => {
    if (!selectedFile) return;
    
    setErrorMessage('');
    setShowSuccessMessage(false);
    setConvertedFileUrl(null);
    setConvertedFileName('');
    setIsConverting(true);
    setConversionProgress(10);

    const form = new FormData();
    form.append("file", selectedFile);
    form.append("quality", quality);

    try {
      setConversionProgress(30);
      const response = await fetch(`${API_BASE}/convert`, {
        method: "POST",
        body: form,
      });

      setConversionProgress(70);

      if (!response.ok) {
        const errorText = await getErrorMessage(response);
        setErrorMessage(errorText);
        setIsConverting(false);
        return;
      }

      setConversionProgress(90);

      // 파일명 결정
      const baseName = selectedFile.name.replace(/\.(docx|pdf)$/i, "");
      const extension = conversionMode === "docx-to-pdf" ? "pdf" : "docx";
      let fileName = safeGetFilename(response, `${baseName}.${extension}`);
      
      if (!fileName.toLowerCase().endsWith(`.${extension}`)) {
        fileName = `${baseName}.${extension}`;
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      
      setConvertedFileUrl(url);
      setConvertedFileName(fileName);
      setConversionProgress(100);
      setIsConverting(false);
      
      // 성공 메시지 표시
      const modeText = conversionMode === "docx-to-pdf" ? "DOCX → PDF" : "PDF → DOCX";
      setSuccessMessage(`${modeText} 변환 완료! ${fileName}로 다운로드됩니다.`);
      setShowSuccessMessage(true);
      
      // 자동 다운로드
      setTimeout(() => {
        downloadBlob(blob, fileName);
      }, 1000);

    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : '변환 중 예상치 못한 문제가 발생했습니다.');
      setIsConverting(false);
    }
  };

  const getAcceptedFileTypes = () => {
    return conversionMode === "docx-to-pdf" ? ".docx" : ".pdf";
  };

  const getFileTypeText = () => {
    return conversionMode === "docx-to-pdf" ? "DOCX" : "PDF";
  };

  const getConversionText = () => {
    return conversionMode === "docx-to-pdf" ? "DOCX → PDF" : "PDF → DOCX";
  };

  const getTargetFormat = () => {
    return conversionMode === "docx-to-pdf" ? "PDF" : "DOCX";
  };

  return (
    <>
      <Helmet>
        <title>{`${getConversionText()} 변환기 - 77-tools.xyz`}</title>
        <meta name="description" content={`${getFileTypeText()} 파일을 ${getTargetFormat()}로 무료 변환. 빠르고 안전한 온라인 문서 변환 도구.`} />
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
              <svg className="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
              <h1 className="text-4xl font-bold">{getConversionText()} 변환기</h1>
            </div>
            <p className="text-lg opacity-90 max-w-2xl mx-auto">
              {conversionMode === "docx-to-pdf" 
                ? "DOCX 문서를 PDF로 변환하여 어디서나 안전하게 공유하세요"
                : "PDF 파일을 편집 가능한 DOCX 문서로 변환하세요"
              }
            </p>
            
            {/* 모드 토글 버튼 */}
            <div className="flex justify-center mt-6">
              <div className="bg-white/20 backdrop-blur-sm rounded-lg p-1">
                <button
                  onClick={handleModeToggle}
                  className={`px-6 py-2 rounded-md font-medium transition-all ${
                    conversionMode === "docx-to-pdf"
                      ? "bg-white text-purple-600 shadow-md"
                      : "text-white hover:bg-white/10"
                  }`}
                >
                  DOCX → PDF
                </button>
                <button
                  onClick={handleModeToggle}
                  className={`px-6 py-2 rounded-md font-medium transition-all ${
                    conversionMode === "pdf-to-docx"
                      ? "bg-white text-purple-600 shadow-md"
                      : "text-white hover:bg-white/10"
                  }`}
                >
                  PDF → DOCX
                </button>
              </div>
            </div>
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
            <h2 className="text-2xl font-semibold text-gray-800">{getConversionText()} 변환기</h2>
            <p className="text-gray-500">안정적인 문서 변환 서비스</p>
          </div>
          
          {!selectedFile ? (
            // 파일 선택 전 UI
            <label htmlFor="file-upload" className="block border-2 border-dashed border-gray-300 rounded-lg p-10 text-center cursor-pointer hover:border-blue-500 hover:bg-gray-50 transition-colors">
              <input 
                id="file-upload" 
                ref={fileInputRef} 
                type="file" 
                accept={getAcceptedFileTypes()} 
                onChange={handleFileChange} 
                className="hidden" 
              />
              <p className="font-semibold text-gray-700">파일을 선택하세요</p>
              <p className="text-sm text-gray-500 mt-1">{getFileTypeText()} 파일을 클릭하여 선택 (최대 100MB)</p>
            </label>
          ) : (
            // 파일 선택 후 UI
            <div className="space-y-6">
              <div>
                <p className="text-gray-700"><span className="font-semibold">파일명:</span> {selectedFile.name}</p>
                <p className="text-gray-700"><span className="font-semibold">크기:</span> {formatFileSize(selectedFile.size)}</p>
              </div>
              
              <div className="space-y-2 mb-4">
                <p className="font-medium">변환 품질 선택:</p>
                <label className="flex items-center gap-2">
                  <input 
                    type="radio" 
                    name="quality" 
                    value="low" 
                    checked={quality === "low"} 
                    onChange={(e) => setQuality(e.target.value as "low" | "standard" | "high")} 
                  />
                  <span>빠른 변환 (권장)</span>
                </label>
                <label className="flex items-center gap-2">
                  <input 
                    type="radio" 
                    name="quality" 
                    value="standard" 
                    checked={quality === "standard"} 
                    onChange={(e) => setQuality(e.target.value as "low" | "standard" | "high")} 
                  />
                  <span>표준 변환</span>
                </label>
                <label className="flex items-center gap-2">
                  <input 
                    type="radio" 
                    name="quality" 
                    value="high" 
                    checked={quality === "high"} 
                    onChange={(e) => setQuality(e.target.value as "low" | "standard" | "high")} 
                  />
                  <span>고품질 변환</span>
                </label>
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

              {/* 진행률 바 - JPG/BMP와 동일한 스타일 */}
              {isConverting && (
                <div className="mt-4">
                  <div className="flex justify-between text-sm mb-1">
                    <span>변환 진행률</span>
                    <span>{conversionProgress}%</span>
                  </div>
                  <div className="h-2 bg-gray-200 rounded">
                    <div 
                      className="h-2 bg-indigo-500 rounded transition-[width] duration-300"
                      style={{ width: `${Math.max(2, conversionProgress)}%` }}
                    />
                  </div>
                  {isConverting && (
                    <div className="mt-2 text-sm text-gray-500">⏳ 변환 중...</div>
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

      {/* 문서 변환 가이드 섹션 */}
      <div className="bg-gray-50 py-16">
        <div className="max-w-4xl mx-auto px-4">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-800 mb-4">
              {conversionMode === "docx-to-pdf" ? "DOCX를 PDF로 변환하는 방법" : "PDF를 DOCX로 변환하는 방법"}
            </h2>
            <p className="text-gray-600">간단한 4단계로 문서를 변환하세요</p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* 1단계: 파일 업로드 */}
            <div className="bg-white rounded-lg p-6 shadow-md hover:shadow-lg transition-shadow">
              <div className="flex items-center justify-center w-12 h-12 bg-blue-100 rounded-full mb-4 mx-auto">
                <span className="text-xl font-bold text-blue-600">1️⃣</span>
              </div>
              <h3 className="text-lg font-semibold text-gray-800 mb-2 text-center">{getFileTypeText()} 업로드</h3>
              <p className="text-gray-600 text-sm text-center">{getFileTypeText()} 파일을 드래그하거나 "파일 선택" 버튼을 클릭하여 업로드해주세요.</p>
            </div>

            {/* 2단계: 변환 옵션 선택 */}
            <div className="bg-white rounded-lg p-6 shadow-md hover:shadow-lg transition-shadow">
              <div className="flex items-center justify-center w-12 h-12 bg-green-100 rounded-full mb-4 mx-auto">
                <span className="text-xl font-bold text-green-600">2️⃣</span>
              </div>
              <h3 className="text-lg font-semibold text-gray-800 mb-2 text-center">변환 옵션 선택 (선택 사항)</h3>
              <p className="text-gray-600 text-sm text-center">빠른 변환, 표준 변환, 고품질 변환 등 원하는 품질 옵션을 선택해주세요.</p>
            </div>

            {/* 3단계: 자동 변환 시작 */}
            <div className="bg-white rounded-lg p-6 shadow-md hover:shadow-lg transition-shadow">
              <div className="flex items-center justify-center w-12 h-12 bg-yellow-100 rounded-full mb-4 mx-auto">
                <span className="text-xl font-bold text-yellow-600">3️⃣</span>
              </div>
              <h3 className="text-lg font-semibold text-gray-800 mb-2 text-center">자동 변환 시작</h3>
              <p className="text-gray-600 text-sm text-center">"변환하기" 버튼을 클릭하세요. AI 기반 엔진이 문서의 레이아웃과 텍스트를 분석하여 변환을 시작합니다.</p>
            </div>

            {/* 4단계: 파일 다운로드 */}
            <div className="bg-white rounded-lg p-6 shadow-md hover:shadow-lg transition-shadow">
              <div className="flex items-center justify-center w-12 h-12 bg-purple-100 rounded-full mb-4 mx-auto">
                <span className="text-xl font-bold text-purple-600">4️⃣</span>
              </div>
              <h3 className="text-lg font-semibold text-gray-800 mb-2 text-center">{getTargetFormat()} 파일 다운로드</h3>
              <p className="text-gray-600 text-sm text-center">변환이 완료되면, 완벽하게 편집 가능한 {getTargetFormat()} 파일을 즉시 다운로드할 수 있습니다.</p>
            </div>
          </div>
        </div>
      </div>
      </div>
    </>
  );
};

export default DocxPdfPage;