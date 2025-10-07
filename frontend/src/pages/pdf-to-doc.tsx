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

const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const PdfToDocPage: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [quality, setQuality] = useState('fast'); // 'fast' 또는 'standard'
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

  const handleReset = () => {
    setSelectedFile(null);
    setErrorMessage('');
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
    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('quality', quality); // 선택된 품질 값을 백엔드로 보냅니다.
    try {
      const response = await fetch('/api/pdf-doc/convert', { method: 'POST', body: formData });
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: '알 수 없는 서버 오류' }));
        throw new Error(errorData.error || `서버 오류: ${response.status}`);
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

  return (
    <div className="w-full bg-white">
      {/* 상단 보라색 배경 섹션 */}
      <div className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white py-20 px-4 text-center">
        <div className="container mx-auto">
            <div className="flex justify-center items-center gap-4 mb-4">
              <svg className="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
              <h1 className="text-4xl font-bold">PDF → DOCX 변환기</h1>
            </div>
            <p className="text-lg opacity-90 max-w-2xl mx-auto">AI 기반 PDF to DOCX 변환 서비스로 문서를 Word 파일로 쉽게 변환하세요.</p>
        </div>
      </div>

      <div className="container mx-auto px-4 py-16">
        <div className="bg-white p-8 rounded-xl shadow-lg max-w-2xl mx-auto">
          <div className="text-center mb-6">
            <h2 className="text-2xl font-semibold text-gray-800">PDF → DOCX 변환기</h2>
            <p className="text-gray-500">안정적인 텍스트 기반 변환</p>
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
                <div className="flex gap-4">
                  <label className="flex items-center">
                    <input type="radio" name="quality" value="fast" checked={quality === 'fast'} onChange={(e) => setQuality(e.target.value)} className="w-4 h-4 text-blue-600" />
                    <span className="ml-2 text-gray-700">빠른 변환 (권장)</span>
                  </label>
                  <label className="flex items-center">
                    <input type="radio" name="quality" value="standard" checked={quality === 'standard'} onChange={(e) => setQuality(e.target.value)} className="w-4 h-4 text-blue-600" />
                    <span className="ml-2 text-gray-700">표준 변환</span>
                  </label>
                </div>
              </div>

              <div className="flex gap-4">
                <button onClick={handleConvert} disabled={isConverting} className="flex-1 bg-blue-600 text-white px-6 py-3 rounded-lg text-lg font-semibold hover:bg-blue-700 disabled:bg-gray-400">
                  {isConverting ? '변환 중...' : '변환하기'}
                </button>
                <button onClick={handleReset} className="flex-1 bg-gray-600 text-white px-6 py-3 rounded-lg text-lg font-semibold hover:bg-gray-700">
                  파일 초기화
                </button>
              </div>
            </div>
          )}
          
          {errorMessage && <p className="mt-4 text-center text-red-500">{errorMessage}</p>}
        </div>
      </div>
    </div>
  );
};

export default PdfToDocPage;
