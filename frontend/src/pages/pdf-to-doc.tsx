// frontend/src/pages/pdf-to-doc.tsx

import React, { useState, useRef } from 'react';

// 브라우저에서 파일을 다운로드하게 해주는 도우미 함수
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

const PdfToDocPage: React.FC = () => { // 컴포넌트 이름도 파일명에 맞게 변경 (선택사항)
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
      const response = await fetch('/api/pdf-doc/convert', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: '알 수 없는 서버 오류가 발생했습니다.' }));
        throw new Error(errorData.error || `서버 오류: ${response.status}`);
      }
       
      const blob = await response.blob();
      const downloadFilename = selectedFile.name.replace(/\.[^/.]+$/, "") + ".docx";
      downloadBlob(blob, downloadFilename);

    } catch (error) {
      if (error instanceof Error) {
        setErrorMessage(error.message);
      } else {
        setErrorMessage('변환 중 예상치 못한 문제가 발생했습니다.');
      }
    } finally {
      setIsConverting(false);
    }
  };
   
  const triggerFileSelect = () => {
    fileInputRef.current?.click();
  };

  return (
    <>
      <div className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white py-12 px-4 text-center">
          <div className="flex justify-center items-center gap-4 mb-4">
              <svg className="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
              <h1 className="text-4xl font-bold">PDF → DOCX 변환기</h1>
          </div>
          <p className="text-lg opacity-90">AI 기반 PDF to DOCX 변환 서비스로 문서를 Word 파일로 쉽게 변환하세요.</p>
      </div>

      <div className="container mx-auto px-4 -mt-16 mb-16">
          <div className="bg-white p-8 rounded-xl shadow-lg max-w-2xl mx-auto">
              <div className="text-center mb-6">
                  <h2 className="text-2xl font-semibold text-gray-800">PDF → DOCX 변환기</h2>
                  <p className="text-gray-500">안정적인 텍스트 기반 변환</p>
              </div>
               
              <div 
                onClick={triggerFileSelect}
                className="border-2 border-dashed border-gray-300 rounded-lg p-10 text-center cursor-pointer hover:border-blue-500 hover:bg-gray-50 transition-colors"
              >
                  <input 
                      ref={fileInputRef}
                      type="file" 
                      accept=".pdf" 
                      onChange={handleFileChange}
                      className="hidden" 
                  />
                  <p className="font-semibold text-gray-700">파일을 선택하세요</p>
                  <p className="text-sm text-gray-500 mt-1">PDF 파일을 클릭하여 선택 (최대 100MB)</p>
              </div>

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
    </>
  );
};

export default PdfToDocPage; // 컴포넌트 이름도 파일명에 맞게 변경 (선택사항)
