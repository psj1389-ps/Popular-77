// frontend/src/pages/pdf-to-doc.tsx

import React, { useState, useRef } from 'react';

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

const PdfToDocPage: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isConverting, setIsConverting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
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

  const handleConvert = async () => {
    if (!selectedFile) {
      setErrorMessage('먼저 파일을 선택해주세요.');
      return;
    }
    setIsConverting(true);
    setErrorMessage('');
    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('quality', 'low');
    try {
      const response = await fetch('/api/pdf-doc/convert', { method: 'POST', body: formData });

      // 서버 응답이 정상이 아닐 때, 더 자세한 에러 메시지를 처리합니다.
      if (!response.ok) {
        // 서버가 JSON 형태의 에러 메시지를 보냈는지 확인
        const contentType = response.headers.get("content-type");
        if (contentType && contentType.indexOf("application/json") !== -1) {
            const errorData = await response.json();
            throw new Error(errorData.error || `서버 오류: ${response.status}`);
        } else {
            // JSON이 아닌 다른 응답(HTML 등)이 왔을 경우
            const errorText = await response.text();
            console.error("서버 응답:", errorText); // 개발자 도구 콘솔에 전체 에러 내용을 출력
            throw new Error(`서버에서 예상치 못한 응답이 왔습니다. (상태: ${response.status})`);
        }
      }
       
      const blob = await response.blob();
      const downloadFilename = selectedFile.name.replace(/\.[^/.]+$/, "") + ".docx";
      downloadBlob(blob, downloadFilename);

    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : '변환 중 예상치 못한 문제 발생');
    } finally {
      setIsConverting(false);
    }
  };

  const triggerFileSelect = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="w-full bg-gray-50">
      {/* 상단 보라색 배경 섹션 */}
      <div className="relative bg-gradient-to-r from-purple-600 to-indigo-600 text-white py-20 px-4 text-center">
        <div className="container mx-auto">
            <div className="flex justify-center items-center gap-4 mb-4">
              <svg className="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
              <h1 className="text-4xl font-bold">PDF → DOCX 변환기</h1>
            </div>
            <p className="text-lg opacity-90 max-w-2xl mx-auto">AI 기반 PDF to DOCX 변환 서비스로 문서를 Word 파일로 쉽게 변환하세요.</p>
        </div>
      </div>

      {/* 메인 변환기 카드 섹션 */}
      {/* z-10과 relative를 추가하여 흰색 카드가 항상 위로 오도록 합니다. */}
      <div className="relative container mx-auto px-4 -mt-24 pb-16 z-10"> 
        <div className="bg-white p-8 rounded-xl shadow-lg max-w-2xl mx-auto">
          <div className="text-center mb-6">
            <h2 className="text-2xl font-semibold text-gray-800">PDF → DOCX 변환기</h2>
            <p className="text-gray-500">안정적인 텍스트 기반 변환</p>
          </div>
           
          <label htmlFor="file-upload" className="block border-2 border-dashed border-gray-300 rounded-lg p-10 text-center cursor-pointer hover:border-blue-500 hover:bg-gray-50 transition-colors">
            <input 
              id="file-upload"
              ref={fileInputRef}
              type="file" 
              accept=".pdf" 
              onChange={handleFileChange}
              className="hidden" 
            />
            <p className="font-semibold text-gray-700">파일을 선택하세요</p>
            <p className="text-sm text-gray-500 mt-1">PDF 파일을 클릭하여 선택 (최대 100MB)</p>
          </label>

          {selectedFile && <p className="mt-4 text-center text-gray-700">선택된 파일: {selectedFile.name}</p>}

          <div className="text-center mt-6">
            <button 
              onClick={handleConvert}
              disabled={!selectedFile || isConverting}
              className="w-full bg-blue-600 text-white px-8 py-3 rounded-lg text-lg font-semibold hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {isConverting ? '변환 중...' : '변환하기'}
            </button>
          </div>
           
          {errorMessage && <p className="mt-4 text-center text-red-500">{errorMessage}</p>}
        </div>
      </div>
    </div>
  );
};

export default PdfToDocPage;
