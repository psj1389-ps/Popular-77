// Popular-77/frontend/src/pages/pdf-to-doc.tsx
import React, { useState, useRef } from 'react';
import { FileText, UploadCloud, Loader2, CheckCircle, Download } from 'lucide-react';
import { TOOLS } from '../data/constants';

// constants.ts에서 'pdf-to-doc' 도구 정보 가져오기
const toolInfo = TOOLS.find(tool => tool.id === 'pdf-to-doc');
const IconComponent = FileText;

const PdfToDocPage: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null); // 사용자가 선택한 파일 객체
  const [fileName, setFileName] = useState<string>('');               // 파일 이름
  const [isLoading, setIsLoading] = useState<boolean>(false);         // 로딩 상태
  const [error, setError] = useState<string | null>(null);            // 에러 메시지
  const [convertedFileUrl, setConvertedFileUrl] = useState<string | null>(null); // 변환된 파일의 URL
  const [convertedFileName, setConvertedFileName] = useState<string | null>(null); // 변환된 파일의 이름

  const fileInputRef = useRef<HTMLInputElement>(null); // 파일 입력 참조

  // 파일 선택 핸들러
  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file && file.type === 'application/pdf') {
      setSelectedFile(file);
      setFileName(file.name);
      setError(null);
      setConvertedFileUrl(null); // 새 파일 선택 시 이전 결과 초기화
      setConvertedFileName(null);
    } else {
      setSelectedFile(null);
      setFileName('');
      setError('PDF 파일만 업로드할 수 있습니다.');
      setConvertedFileUrl(null);
      setConvertedFileName(null);
    }
  };

  // PDF를 DOCX로 변환 요청 핸들러
  const handleConvertPdf = async () => {
    if (!selectedFile) {
      setError('PDF 파일을 먼저 선택해주세요.');
      return;
    }

    setIsLoading(true);
    setError(null);
    setConvertedFileUrl(null);
    setConvertedFileName(null);

    const formData = new FormData();
    formData.append('file', selectedFile); // 'file'은 백엔드에서 파일을 받을 때 사용할 키 이름입니다.

    try {
      // 백엔드 API 엔드포인트를 /api/pdf-doc로 변경 (Vercel 프록시 설정에 맞춤)
      const response = await fetch('/api/pdf-doc', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        // 백엔드에서 에러 응답을 보낼 경우
        try {
          const errorData = await response.json();
          throw new Error(errorData.error || 'PDF 변환 중 오류가 발생했습니다.');
        } catch (jsonError) {
          throw new Error('PDF 변환 중 오류가 발생했습니다.');
        }
      }

      // 백엔드가 변환된 파일을 직접 응답으로 보낼 경우
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      setConvertedFileUrl(url);

      // 백엔드에서 파일 이름을 헤더로 보내줄 경우 (예: Content-Disposition)
      const contentDisposition = response.headers.get('Content-Disposition');
      let suggestedFileName = 'converted.docx';
      if (contentDisposition) {
        const fileNameMatch = contentDisposition.match(/filename="([^"]+)"/);
        if (fileNameMatch && fileNameMatch[1]) {
          suggestedFileName = fileNameMatch[1];
        }
      } else {
        // Content-Disposition 헤더가 없으면 원본 파일명 기반으로 생성
        const baseName = fileName.split('.').slice(0, -1).join('.');
        suggestedFileName = `${baseName}.docx`;
      }
      setConvertedFileName(suggestedFileName);

    } catch (err: any) {
      console.error('PDF 변환 오류:', err);
      setError(err.message || 'PDF 변환에 실패했습니다. 다시 시도해주세요.');
    } finally {
      setIsLoading(false);
    }
  };

  // 변환된 파일 다운로드 핸들러
  const handleDownloadConvertedFile = () => {
    if (convertedFileUrl && convertedFileName) {
      const link = document.createElement('a');
      link.href = convertedFileUrl;
      link.download = convertedFileName;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(convertedFileUrl); // URL 해제
    }
  };

  return (
    <div className="p-8 bg-white rounded-lg shadow-md max-w-4xl mx-auto">
      {toolInfo && (
        <>
          <div className="text-green-600 mb-4">
            {IconComponent && <IconComponent size={48} className="mx-auto" />}
          </div>
          <h1 className="text-4xl font-bold mb-4 text-center">{toolInfo.name}</h1>
          <p className="text-xl text-gray-700 mb-8 text-center">{toolInfo.description}</p>
        </>
      )}

      {/* 파일 업로드 영역 */}
      <div
        className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center cursor-pointer hover:border-blue-500 transition-colors duration-200"
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          type="file"
          ref={fileInputRef}
          accept=".pdf" // PDF 파일만 허용
          onChange={handleFileChange}
          className="hidden"
        />
        {selectedFile ? (
          <p className="text-lg text-gray-700">
            <FileText size={24} className="inline-block mr-2 text-blue-500" />
            파일 선택됨: <span className="font-semibold">{fileName}</span>
          </p>
        ) : (
          <>
            <UploadCloud size={48} className="mx-auto mb-4 text-gray-400" />
            <p className="text-lg text-gray-700">여기를 클릭하거나 PDF 파일을 드래그하여 업로드하세요.</p>
            <p className="text-sm text-gray-500 mt-2">PDF 파일만 가능합니다.</p>
          </>
        )}
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mt-4" role="alert">
          <span className="block sm:inline">{error}</span>
        </div>
      )}

      {selectedFile && !convertedFileUrl && (
        <div className="mt-8">
          <button
            onClick={handleConvertPdf}
            disabled={isLoading || !selectedFile}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors duration-200 disabled:bg-blue-300 disabled:cursor-not-allowed flex items-center justify-center"
          >
            {isLoading && <Loader2 className="animate-spin mr-2" size={20} />}
            {isLoading ? '변환 중...' : 'PDF를 Word로 변환'}
          </button>
        </div>
      )}

      {convertedFileUrl && convertedFileName && (
        <div className="mt-8 text-center">
          <h2 className="text-2xl font-semibold mb-4">변환 완료!</h2>
          <p className="text-lg text-gray-700 mb-4">
            <CheckCircle size={24} className="inline-block mr-2 text-green-500" />
            파일이 성공적으로 변환되었습니다.
          </p>
          <button
            onClick={handleDownloadConvertedFile}
            className="w-full bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 transition-colors duration-200 flex items-center justify-center"
          >
            <Download size={20} className="inline-block mr-2" />
            {convertedFileName} 다운로드
          </button>
        </div>
      )}
    </div>
  );
};

export default PdfToDocPage;
