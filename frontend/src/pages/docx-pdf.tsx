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
      
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
        {/* 배경 패턴 */}
        <div 
          className="absolute inset-0 opacity-5"
          style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23000000' fill-opacity='0.1'%3E%3Ccircle cx='7' cy='7' r='1'/%3E%3Ccircle cx='53' cy='7' r='1'/%3E%3Ccircle cx='7' cy='53' r='1'/%3E%3Ccircle cx='53' cy='53' r='1'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
            backgroundRepeat: 'repeat',
            animation: 'float 20s ease-in-out infinite'
          }}
        />
        
        <div className="container mx-auto relative z-10">
          <div className="flex justify-center items-center gap-4 mb-4">
            <svg className="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <h1 className="text-4xl font-bold">{getConversionText()} 변환기</h1>
          </div>
          
          {/* 모드 토글 버튼 */}
          <div className="flex justify-center mb-6">
            <div className="bg-white rounded-lg p-1 shadow-md">
              <button
                onClick={handleModeToggle}
                className={`px-6 py-2 rounded-md font-medium transition-all ${
                  conversionMode === "docx-to-pdf"
                    ? "bg-blue-500 text-white shadow-md"
                    : "text-gray-600 hover:bg-gray-100"
                }`}
              >
                DOCX → PDF
              </button>
              <button
                onClick={handleModeToggle}
                className={`px-6 py-2 rounded-md font-medium transition-all ${
                  conversionMode === "pdf-to-docx"
                    ? "bg-blue-500 text-white shadow-md"
                    : "text-gray-600 hover:bg-gray-100"
                }`}
              >
                PDF → DOCX
              </button>
            </div>
          </div>

          <div className="text-center mb-8">
            <p className="text-gray-600 text-lg">
              {conversionMode === "docx-to-pdf" 
                ? "DOCX 문서를 PDF로 변환하여 어디서나 안전하게 공유하세요"
                : "PDF 파일을 편집 가능한 DOCX 문서로 변환하세요"
              }
            </p>
            <p className="text-gray-500">안정적인 변환 서비스</p>
          </div>
          
          {!selectedFile ? (
            // 파일 선택 전 UI
            <div className="max-w-2xl mx-auto">
              <div 
                className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center hover:border-blue-400 transition-colors cursor-pointer bg-white/50 backdrop-blur-sm"
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onClick={() => fileInputRef.current?.click()}
              >
                <svg className="mx-auto h-12 w-12 text-gray-400 mb-4" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                  <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
                <p className="text-xl font-medium text-gray-700 mb-2">
                  {getFileTypeText()} 파일을 드래그하거나 클릭하여 선택하세요
                </p>
                <p className="text-gray-500">
                  지원 형식: {getFileTypeText()} 파일
                </p>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept={getAcceptedFileTypes()}
                  onChange={handleFileChange}
                  className="hidden"
                />
              </div>
            </div>
          ) : (
            // 파일 선택 후 UI
            <div className="max-w-2xl mx-auto">
              <div className="bg-white/70 backdrop-blur-sm rounded-lg shadow-lg p-6 mb-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center">
                    <svg className="w-8 h-8 text-blue-500 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <div>
                      <p className="font-medium text-gray-800">{selectedFile.name}</p>
                      <p className="text-sm text-gray-500">{formatFileSize(selectedFile.size)}</p>
                    </div>
                  </div>
                  <button
                    onClick={handleReset}
                    className="text-gray-400 hover:text-gray-600 transition-colors"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>

                {/* 품질 선택 */}
                <div className="mb-6">
                  <label className="block text-sm font-medium text-gray-700 mb-3">변환 품질</label>
                  <div className="grid grid-cols-3 gap-3">
                    <label className={`flex items-center justify-center p-3 border rounded-lg cursor-pointer transition-all ${
                      quality === "low" ? "border-blue-500 bg-blue-50" : "border-gray-200 hover:border-gray-300"
                    }`}>
                      <input
                        type="radio"
                        name="quality"
                        value="low"
                        checked={quality === "low"}
                        onChange={(e) => setQuality(e.target.value as "low" | "standard" | "high")}
                        className="sr-only"
                      />
                      <div className="text-center">
                        <div className="font-medium">빠른 변환</div>
                        <div className="text-xs text-gray-500">기본 품질</div>
                      </div>
                    </label>
                    <label className={`flex items-center justify-center p-3 border rounded-lg cursor-pointer transition-all ${
                      quality === "standard" ? "border-blue-500 bg-blue-50" : "border-gray-200 hover:border-gray-300"
                    }`}>
                      <input
                        type="radio"
                        name="quality"
                        value="standard"
                        checked={quality === "standard"}
                        onChange={(e) => setQuality(e.target.value as "low" | "standard" | "high")}
                        className="sr-only"
                      />
                      <div className="text-center">
                        <div className="font-medium">표준 변환</div>
                        <div className="text-xs text-gray-500">균형잡힌 품질</div>
                      </div>
                    </label>
                    <label className={`flex items-center justify-center p-3 border rounded-lg cursor-pointer transition-all ${
                      quality === "high" ? "border-blue-500 bg-blue-50" : "border-gray-200 hover:border-gray-300"
                    }`}>
                      <input
                        type="radio"
                        name="quality"
                        value="high"
                        checked={quality === "high"}
                        onChange={(e) => setQuality(e.target.value as "low" | "standard" | "high")}
                        className="sr-only"
                      />
                      <div className="text-center">
                        <div className="font-medium">고품질 변환</div>
                        <div className="text-xs text-gray-500">최고 품질</div>
                      </div>
                    </label>
                  </div>
                </div>

                {/* 변환 버튼 */}
                <button
                  onClick={handleConvert}
                  disabled={isConverting}
                  className="w-full bg-blue-500 hover:bg-blue-600 disabled:bg-gray-400 text-white font-medium py-3 px-6 rounded-lg transition-colors flex items-center justify-center"
                >
                  {isConverting ? (
                    <>
                      <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      변환 중... ({conversionProgress}%)
                    </>
                  ) : (
                    `${getTargetFormat()}로 변환하기`
                  )}
                </button>

                {/* 진행률 바 */}
                {isConverting && (
                  <div className="mt-4">
                    <div className="bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${conversionProgress}%` }}
                      ></div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* 성공 메시지 */}
          {showSuccessMessage && (
            <div className="max-w-2xl mx-auto mb-6">
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="flex items-center">
                  <svg className="w-5 h-5 text-green-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <p className="text-green-800">{successMessage}</p>
                </div>
              </div>
            </div>
          )}
          
          {errorMessage && <p className="mt-4 text-center text-red-500">{errorMessage}</p>}
        </div>
      </div>

      {/* 사용법 가이드 섹션 */}
      <div className="bg-gray-50 py-16">
        <div className="max-w-4xl mx-auto px-4">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-800 mb-4">
              {conversionMode === "docx-to-pdf" ? "DOCX를 PDF로 변환하는 방법" : "PDF를 DOCX로 변환하는 방법"}
            </h2>
            <p className="text-gray-600">간단한 4단계로 문서를 변환하세요</p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* 1단계 */}
            <div className="bg-white rounded-lg p-6 shadow-md hover:shadow-lg transition-shadow">
              <div className="flex items-center justify-center w-12 h-12 bg-blue-100 rounded-full mb-4 mx-auto">
                <span className="text-xl font-bold text-blue-600">1️⃣</span>
              </div>
              <h3 className="text-lg font-semibold text-gray-800 mb-2 text-center">
                {getFileTypeText()} 파일 업로드
              </h3>
              <p className="text-gray-600 text-sm text-center">
                변환할 {getFileTypeText()} 파일을 드래그하거나 클릭하여 선택해주세요.
              </p>
            </div>

            {/* 2단계 */}
            <div className="bg-white rounded-lg p-6 shadow-md hover:shadow-lg transition-shadow">
              <div className="flex items-center justify-center w-12 h-12 bg-green-100 rounded-full mb-4 mx-auto">
                <span className="text-xl font-bold text-green-600">2️⃣</span>
              </div>
              <h3 className="text-lg font-semibold text-gray-800 mb-2 text-center">변환 품질 선택</h3>
              <p className="text-gray-600 text-sm text-center">
                빠른 변환, 표준 변환, 고품질 변환 중 원하는 옵션을 선택해주세요.
              </p>
            </div>

            {/* 3단계 */}
            <div className="bg-white rounded-lg p-6 shadow-md hover:shadow-lg transition-shadow">
              <div className="flex items-center justify-center w-12 h-12 bg-yellow-100 rounded-full mb-4 mx-auto">
                <span className="text-xl font-bold text-yellow-600">3️⃣</span>
              </div>
              <h3 className="text-lg font-semibold text-gray-800 mb-2 text-center">자동 변환 시작</h3>
              <p className="text-gray-600 text-sm text-center">
                변환 버튼을 클릭하면 자동으로 {getTargetFormat()} 변환이 시작됩니다.
              </p>
            </div>

            {/* 4단계 */}
            <div className="bg-white rounded-lg p-6 shadow-md hover:shadow-lg transition-shadow">
              <div className="flex items-center justify-center w-12 h-12 bg-purple-100 rounded-full mb-4 mx-auto">
                <span className="text-xl font-bold text-purple-600">4️⃣</span>
              </div>
              <h3 className="text-lg font-semibold text-gray-800 mb-2 text-center">{getTargetFormat()} 파일 다운로드</h3>
              <p className="text-gray-600 text-sm text-center">
                변환이 완료되면 {getTargetFormat()} 파일을 즉시 다운로드할 수 있습니다.
              </p>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default DocxPdfPage;