import React, { useState, useRef, useEffect } from 'react';
import PageTitle from '../shared/PageTitle';

// Force Vercel deployment - Updated: 2024-12-30 16:15 - GITHUB INTEGRATION

const API_BASE = "/api/pdf-vector";

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

const PdfVectorPage: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [quality, setQuality] = useState<"low" | "medium" | "high">("medium");
  const [isConverting, setIsConverting] = useState(false);
  const [progress, setProgress] = useState(0);
  const [progressText, setProgressText] = useState('');
  const [showSuccessMessage, setShowSuccessMessage] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [convertedFileUrl, setConvertedFileUrl] = useState<string | null>(null);
  const [convertedFileName, setConvertedFileName] = useState<string>('');
  const fileInputRef = useRef<HTMLInputElement>(null);

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

  const handleRemoveFile = () => {
    setSelectedFile(null);
    setProgress(0);
    setIsConverting(false);
    setErrorMessage('');
    setShowSuccessMessage(false);
    setConvertedFileUrl(null);
    setConvertedFileName('');
    
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
    form.append("mode", "svg"); // Default to SVG mode
    form.append("text_as_path", "true"); // Convert text to paths for better compatibility
    
    // Map quality to zoom level
    const zoomMap = {
      "low": "1.0",
      "medium": "1.5", 
      "high": "2.0"
    };
    form.append("zoom", zoomMap[quality]);
    form.append("split", "true"); // Allow splitting into multiple files if needed

    setIsConverting(true);
    setProgress(10);
    setProgressText("PDF를 벡터 파일로 변환 중...");

    try {
      // 직접 convert_to_vector 엔드포인트 호출 (blob 응답 처리)
      const response = await fetch(`${API_BASE}/convert_to_vector`, { 
        method: "POST", 
        body: form 
      });

      if (!response.ok) {
        const errorMsg = await getErrorMessage(response);
        setErrorMessage(errorMsg);
        setIsConverting(false);
        return;
      }

      setProgress(90);
      setProgressText("파일 다운로드 준비 중...");

      // Content-Type 확인
      const contentType = (response.headers.get("content-type") || "").toLowerCase();
      const base = selectedFile.name.replace(/\.pdf$/i, "");
      
      // 파일명 추출
      let filename = safeGetFilename(response, base);
      
      // 파일 확장자 결정
      const isZip = contentType.includes("zip") || /\.zip$/i.test(filename);
      const isSvg = contentType.includes("svg") || /\.svg$/i.test(filename);
      
      if (!/\.(zip|svg|ai)$/i.test(filename)) {
        if (isZip) {
          filename = `${filename}.zip`;
        } else if (isSvg) {
          filename = `${filename}.svg`;
        } else {
          filename = `${filename}.ai`; // 기본값
        }
      }

      // Blob으로 파일 다운로드
      const blob = await response.blob();
      
      setConvertedFileName(filename);
      setProgress(100);
      setIsConverting(false);
      
      // 성공 메시지 표시
      setSuccessMessage(`변환 완료! 파일명: ${filename}로 다운로드됩니다.`);
      setShowSuccessMessage(true);
      
      // 잠시 후 다운로드 시작
      setTimeout(() => {
        downloadBlob(blob, filename);
      }, 1000);

    } catch (error) {
      console.error('변환 중 오류:', error);
      setErrorMessage(error instanceof Error ? error.message : '변환 중 오류가 발생했습니다.');
      setIsConverting(false);
    }
  };

  return (
    <>
      <PageTitle 
        title="PDF → Vector 변환기 - 77tools.xyz" 
        description="PDF 파일을 벡터 형식(SVG, AI)으로 변환하는 무료 온라인 도구입니다. 고품질 벡터 변환을 지원합니다."
      />
      
      {/* 히어로 섹션 */}
      <div className="relative min-h-[400px] bg-gradient-to-br from-purple-600 via-blue-600 to-indigo-700 text-white overflow-hidden">
        <div 
          className="absolute inset-0 opacity-20"
          style={{
            backgroundImage: `url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><defs><pattern id='grain' width='100' height='100' patternUnits='userSpaceOnUse'><circle cx='12' cy='8' r='0.6' fill='%23ffffff' opacity='0.18'/><circle cx='37' cy='23' r='1.8' fill='%23ffffff' opacity='0.12'/><circle cx='71' cy='15' r='1.2' fill='%23ffffff' opacity='0.15'/><circle cx='85' cy='42' r='0.9' fill='%23ffffff' opacity='0.2'/><circle cx='23' cy='67' r='1.5' fill='%23ffffff' opacity='0.1'/><circle cx='58' cy='78' r='0.7' fill='%23ffffff' opacity='0.16'/><circle cx='91' cy='89' r='1.1' fill='%23ffffff' opacity='0.13'/><circle cx='6' cy='91' r='1.3' fill='%23ffffff' opacity='0.14'/></pattern></defs><rect width='100' height='100' fill='url(%23grain)'/></svg>")`,
            backgroundRepeat: 'repeat',
            animation: 'float 20s ease-in-out infinite'
          }}
        />
        
        <div className="container mx-auto relative z-10">
            <div className="flex justify-center items-center gap-4 mb-4">
              <svg className="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
              <h1 className="text-4xl font-bold">PDF → Vector 변환기</h1>
            </div>
            <p className="text-lg opacity-90 max-w-2xl mx-auto">AI 기반 PDF to Vector 변환 서비스로 문서를 고품질 벡터 파일로 쉽게 변환하세요.</p>
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
            <h2 className="text-2xl font-semibold text-gray-800">PDF → Vector 변환기</h2>
            <p className="text-gray-500">고품질 벡터 파일 변환</p>
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
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">변환 품질</label>
                <select 
                  value={quality} 
                  onChange={(e) => setQuality(e.target.value as "low" | "medium" | "high")}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  disabled={isConverting}
                >
                  <option value="low">빠른 변환 (낮은 품질)</option>
                  <option value="medium">표준 변환 (중간 품질)</option>
                  <option value="high">고품질 변환 (높은 품질)</option>
                </select>
              </div>
              
              {/* 변환 버튼 */}
              <div className="flex gap-4">
                <button
                  onClick={handleConvert}
                  disabled={isConverting}
                  className="flex-1 bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-semibold"
                >
                  {isConverting ? '변환 중...' : '변환하기'}
                </button>
                <button
                  onClick={handleRemoveFile}
                  disabled={isConverting}
                  className="bg-gray-500 text-white py-3 px-6 rounded-lg hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  파일 제거
                </button>
              </div>
              
              {/* 진행률 표시 */}
              {isConverting && (
                <div className="space-y-2">
                  <div className="flex justify-between text-sm text-gray-600">
                    <span>{progressText}</span>
                    <span>{progress}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300" 
                      style={{ width: `${progress}%` }}
                    ></div>
                  </div>
                </div>
              )}
              
              {/* 성공 메시지 */}
              {showSuccessMessage && (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div className="ml-3">
                      <p className="text-sm font-medium text-green-800">{successMessage}</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
          
          {/* 에러 메시지 */}
          {errorMessage && (
            <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm font-medium text-red-800">{errorMessage}</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* PDF를 Vector로 변환하는 방법 가이드 섹션 */}
      <div className="bg-gray-50 py-16">
        <div className="max-w-4xl mx-auto px-4">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-800 mb-4">PDF를 Vector로 변환하는 방법</h2>
            <p className="text-gray-600">간단한 4단계로 PDF를 고품질 벡터 파일로 변환하세요</p>
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
              <p className="text-gray-600 text-sm text-center">빠른 변환 또는 고품질 벡터 변환 등 원하는 품질 옵션을 선택해주세요.</p>
            </div>

            {/* 3단계: 자동 변환 시작 */}
            <div className="bg-white rounded-lg p-6 shadow-md hover:shadow-lg transition-shadow">
              <div className="flex items-center justify-center w-12 h-12 bg-yellow-100 rounded-full mb-4 mx-auto">
                <span className="text-xl font-bold text-yellow-600">3️⃣</span>
              </div>
              <h3 className="text-lg font-semibold text-gray-800 mb-2 text-center">자동 변환 시작</h3>
              <p className="text-gray-600 text-sm text-center">"변환하기" 버튼을 클릭하세요. AI 기반 엔진이 PDF를 벡터 형식으로 변환합니다.</p>
            </div>

            {/* 4단계: Vector 파일 다운로드 */}
            <div className="bg-white rounded-lg p-6 shadow-md hover:shadow-lg transition-shadow">
              <div className="flex items-center justify-center w-12 h-12 bg-purple-100 rounded-full mb-4 mx-auto">
                <span className="text-xl font-bold text-purple-600">4️⃣</span>
              </div>
              <h3 className="text-lg font-semibold text-gray-800 mb-2 text-center">Vector 파일 다운로드</h3>
              <p className="text-gray-600 text-sm text-center">변환이 완료되면, 벡터 파일(.svg, .ai) 또는 ZIP 파일을 즉시 다운로드할 수 있습니다.</p>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default PdfVectorPage;