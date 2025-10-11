import React, { useState, useRef } from 'react';
import PageTitle from '../shared/PageTitle';

const API_BASE = "/api/pdf-pptx";

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

const triggerDirectDownload = (url: string, filename?: string) => {
  const a = document.createElement('a');
  a.href = url;
  if (filename) a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
};

const PdfToPptxPage: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [speed, setSpeed] = useState<"fast" | "standard">("fast");
  const [isConverting, setIsConverting] = useState(false);
  const [conversionProgress, setConversionProgress] = useState(0);
  const [showSuccessMessage, setShowSuccessMessage] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [convertedFileName, setConvertedFileName] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      const file = event.target.files[0];
      if (file.size > 100 * 1024 * 1024) {
        setErrorMessage('파일 크기는 100MB를 초과할 수 없습니다.');
        setSelectedFile(null);
      } else {
        setSelectedFile(file);
        setErrorMessage('');
      }
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setErrorMessage('');
    setShowSuccessMessage(false);
    setSuccessMessage('');
    setConversionProgress(0);
    setConvertedFileName(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = ""; // 파일 입력 초기화
    }
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
    
    const formData = new FormData();
    formData.append('file', selectedFile);
    const quality = speed === "fast" ? "low" : "standard";
    formData.append("quality", quality); // doc과 동일 key
    formData.append("scale", "1.0"); // UI에선 숨기고 기본값만 전송
    
    try {
      const response = await fetch(`${API_BASE}/convert-async`, { method: 'POST', body: formData });
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: '알 수 없는 서버 오류' }));
        throw new Error(errorData.error || `서버 오류: ${response.status}`);
      }
      
      const { job_id } = await response.json();
      
      // 진행률 폴링
      const pollProgress = async () => {
        try {
          const statusResponse = await fetch(`${API_BASE}/job/${job_id}`);
          if (!statusResponse.ok) throw new Error('상태 확인 실패');
          
          const status = await statusResponse.json();
          setConversionProgress(status.progress || 0);
          
          if (status.status === 'done') {
            setConversionProgress(100);
            const baseName = selectedFile.name.replace(/\.[^/.]+$/, "");
            const fileName = `${baseName}.pptx`;
            setConvertedFileName(fileName);
            
            // 자동 다운로드
            const downloadUrl = `${API_BASE}/download/${job_id}`;
            triggerDirectDownload(downloadUrl, fileName);
            
            setSuccessMessage(`변환 완료! ${fileName} 파일이 다운로드됩니다.`);
            setShowSuccessMessage(true);
            setIsConverting(false);
          } else if (status.status === 'error') {
            throw new Error(status.error || '변환 중 오류 발생');
          } else {
            setTimeout(pollProgress, 1000);
          }
        } catch (error) {
          setErrorMessage(error instanceof Error ? error.message : '상태 확인 중 오류 발생');
          setIsConverting(false);
        }
      };
      
      pollProgress();
      
    } catch (error) {
      setConversionProgress(0);
      setErrorMessage(error instanceof Error ? error.message : '변환 중 예상치 못한 문제 발생');
      setIsConverting(false);
    }
  };

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
              
              <div className="space-y-2 mb-4">
                <p className="font-medium">변환 품질 선택:</p>
                <label className="flex items-center gap-2">
                  <input 
                    type="radio" 
                    name="pptx-speed" 
                    value="fast" 
                    checked={speed === "fast"} 
                    onChange={() => setSpeed("fast")} 
                  />
                  <span>빠른 변환 (권장)</span>
                </label>
                <label className="flex items-center gap-2">
                  <input 
                    type="radio" 
                    name="pptx-speed" 
                    value="standard" 
                    checked={speed === "standard"} 
                    onChange={() => setSpeed("standard")} 
                  />
                  <span>표준 변환</span>
                </label>
              </div>

              {false && (/* 기존 크기 x 블록 */)}

              {/* 변환 진행률 표시 */}
              {isConverting && (
                <div className="mb-4">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm font-medium text-blue-700">변환 진행률</span>
                    <span className="text-sm font-medium text-blue-700">{Math.round(conversionProgress)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2.5">
                    <div 
                      className="bg-blue-600 h-2.5 rounded-full transition-all duration-300 ease-out"
                      style={{ width: `${conversionProgress}%` }}
                    ></div>
                  </div>
                  <div className="flex items-center justify-center mt-3">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mr-2"></div>
                    <span className="text-sm text-gray-600">PDF를 PPTX로 변환 중...</span>
                  </div>
                </div>
              )}

              {/* 성공 메시지 */}
              {showSuccessMessage && (
                <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-4">
                  <p>{successMessage}</p>
                </div>
              )}

              {/* 버튼들 */}
              <div className="flex gap-4">
                <button 
                  onClick={handleConvert} 
                  disabled={isConverting}
                  className="flex-1 bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                >
                  {isConverting ? '변환 중...' : '변환하기'}
                </button>
                <button 
                  onClick={handleReset} 
                  className="bg-gray-500 text-white py-3 px-6 rounded-lg hover:bg-gray-600 transition-colors"
                >
                  다시 선택
                </button>
              </div>
            </div>
          )}
          
          {errorMessage && <p className="mt-4 text-center text-red-500">{errorMessage}</p>}
        </div>
      </div>

      {/* PDF를 PPTX로 변환하는 방법 가이드 섹션 */}
      <div className="bg-gray-50 py-16">
        <div className="max-w-4xl mx-auto px-4">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-800 mb-4">PDF를 PPTX로 변환하는 방법</h2>
            <p className="text-gray-600">간단한 4단계로 PDF를 프레젠테이션 파일로 변환하세요</p>
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
              <p className="text-gray-600 text-sm text-center">"변환하기" 버튼을 클릭하세요. AI 기반 엔진이 문서를 PPTX 파일로 변환합니다.</p>
            </div>

            {/* 4단계: PPTX 파일 다운로드 */}
            <div className="bg-white rounded-lg p-6 shadow-md hover:shadow-lg transition-shadow">
              <div className="flex items-center justify-center w-12 h-12 bg-purple-100 rounded-full mb-4 mx-auto">
                <span className="text-xl font-bold text-purple-600">4️⃣</span>
              </div>
              <h3 className="text-lg font-semibold text-gray-800 mb-2 text-center">PPTX 파일 다운로드</h3>
              <p className="text-gray-600 text-sm text-center">변환이 완료되면, 프레젠테이션(.pptx) 파일을 즉시 다운로드할 수 있습니다.</p>
            </div>
          </div>
        </div>
      </div>
      </div>
    </>
  );
};

export default PdfToPptxPage;