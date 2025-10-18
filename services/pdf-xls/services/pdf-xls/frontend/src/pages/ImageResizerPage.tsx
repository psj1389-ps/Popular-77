import React, { useState, useRef } from 'react';
import { Upload, Download, Image as ImageIcon, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import { TOOLS } from '../data/constants';

// constants.ts에서 'image-resizer' 도구 정보 가져오기
const toolInfo = TOOLS.find(tool => tool.id === 'image-resizer');

const ImageResizerPage: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [fileName, setFileName] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [resizedImageUrl, setResizedImageUrl] = useState<string | null>(null);
  const [resizedFileName, setResizedFileName] = useState<string | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  
  // 리사이징 옵션
  const [width, setWidth] = useState<number>(800);
  const [height, setHeight] = useState<number>(600);
  const [maintainAspectRatio, setMaintainAspectRatio] = useState<boolean>(true);
  const [quality, setQuality] = useState<number>(90);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // 파일 선택 핸들러
  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file && file.type.startsWith('image/')) {
      setSelectedFile(file);
      setFileName(file.name);
      setError(null);
      setResizedImageUrl(null);
      setResizedFileName(null);
      
      // 미리보기 URL 생성
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
      
      // 이미지 로드하여 원본 크기 가져오기
      const img = new Image();
      img.onload = () => {
        setWidth(img.width);
        setHeight(img.height);
      };
      img.src = url;
    } else {
      setSelectedFile(null);
      setFileName('');
      setError('이미지 파일만 업로드할 수 있습니다.');
      setResizedImageUrl(null);
      setResizedFileName(null);
      setPreviewUrl(null);
    }
  };

  // 종횡비 유지 핸들러
  const handleWidthChange = (newWidth: number) => {
    setWidth(newWidth);
    if (maintainAspectRatio && selectedFile && previewUrl) {
      const img = new Image();
      img.onload = () => {
        const aspectRatio = img.height / img.width;
        setHeight(Math.round(newWidth * aspectRatio));
      };
      img.src = previewUrl;
    }
  };

  const handleHeightChange = (newHeight: number) => {
    setHeight(newHeight);
    if (maintainAspectRatio && selectedFile && previewUrl) {
      const img = new Image();
      img.onload = () => {
        const aspectRatio = img.width / img.height;
        setWidth(Math.round(newHeight * aspectRatio));
      };
      img.src = previewUrl;
    }
  };

  // 이미지 리사이징 핸들러
  const handleResizeImage = async () => {
    if (!selectedFile || !previewUrl) {
      setError('이미지 파일을 먼저 선택해주세요.');
      return;
    }

    setIsLoading(true);
    setError(null);
    setResizedImageUrl(null);
    setResizedFileName(null);

    try {
      const img = new Image();
      img.onload = () => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        // 캔버스 크기 설정
        canvas.width = width;
        canvas.height = height;

        // 이미지 리사이징
        ctx.drawImage(img, 0, 0, width, height);

        // 리사이징된 이미지를 Blob으로 변환
        canvas.toBlob(
          (blob) => {
            if (blob) {
              const url = URL.createObjectURL(blob);
              setResizedImageUrl(url);
              
              // 파일명 생성
              const baseName = fileName.split('.').slice(0, -1).join('.');
              const extension = fileName.split('.').pop();
              setResizedFileName(`${baseName}_resized_${width}x${height}.${extension}`);
            }
            setIsLoading(false);
          },
          selectedFile.type,
          quality / 100
        );
      };

      img.onerror = () => {
        setError('이미지를 로드할 수 없습니다.');
        setIsLoading(false);
      };

      img.src = previewUrl;
    } catch (err: any) {
      console.error('이미지 리사이징 오류:', err);
      setError('이미지 리사이징에 실패했습니다. 다시 시도해주세요.');
      setIsLoading(false);
    }
  };

  // 리사이징된 이미지 다운로드 핸들러
  const handleDownloadResizedImage = () => {
    if (resizedImageUrl && resizedFileName) {
      const link = document.createElement('a');
      link.href = resizedImageUrl;
      link.download = resizedFileName;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  return (
    <div className="p-8 bg-white rounded-lg shadow-md max-w-6xl mx-auto">
      {toolInfo && (
        <>
          <div className="text-green-600 mb-4 flex justify-center">
            <ImageIcon size={48} />
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
          accept="image/*"
          onChange={handleFileChange}
          className="hidden"
        />
        {selectedFile ? (
          <p className="text-lg text-gray-700">
            <ImageIcon size={24} className="inline-block mr-2 text-blue-500" />
            파일 선택됨: <span className="font-semibold">{fileName}</span>
          </p>
        ) : (
          <>
            <Upload size={48} className="mx-auto mb-4 text-gray-400" />
            <p className="text-lg text-gray-700">여기를 클릭하거나 이미지 파일을 드래그하여 업로드하세요.</p>
            <p className="text-sm text-gray-500 mt-2">JPG, PNG, GIF, WebP 등 모든 이미지 형식을 지원합니다.</p>
          </>
        )}
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mt-4 flex items-center" role="alert">
          <AlertCircle size={20} className="mr-2" />
          <span>{error}</span>
        </div>
      )}

      {/* 미리보기 및 리사이징 옵션 */}
      {selectedFile && previewUrl && (
        <div className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* 미리보기 */}
          <div>
            <h3 className="text-xl font-semibold mb-4">원본 이미지 미리보기</h3>
            <div className="border rounded-lg p-4 bg-gray-50">
              <img
                src={previewUrl}
                alt="미리보기"
                className="max-w-full max-h-64 mx-auto rounded"
              />
            </div>
          </div>

          {/* 리사이징 옵션 */}
          <div>
            <h3 className="text-xl font-semibold mb-4">리사이징 옵션</h3>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">너비 (px)</label>
                  <input
                    type="number"
                    value={width}
                    onChange={(e) => handleWidthChange(Number(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    min="1"
                    max="5000"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">높이 (px)</label>
                  <input
                    type="number"
                    value={height}
                    onChange={(e) => handleHeightChange(Number(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    min="1"
                    max="5000"
                  />
                </div>
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="aspectRatio"
                  checked={maintainAspectRatio}
                  onChange={(e) => setMaintainAspectRatio(e.target.checked)}
                  className="mr-2"
                />
                <label htmlFor="aspectRatio" className="text-sm text-gray-700">
                  종횡비 유지
                </label>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  품질: {quality}%
                </label>
                <input
                  type="range"
                  min="10"
                  max="100"
                  value={quality}
                  onChange={(e) => setQuality(Number(e.target.value))}
                  className="w-full"
                />
              </div>

              <button
                onClick={handleResizeImage}
                disabled={isLoading || !selectedFile}
                className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors duration-200 disabled:bg-blue-300 disabled:cursor-not-allowed flex items-center justify-center"
              >
                {isLoading && <Loader2 className="animate-spin mr-2" size={20} />}
                {isLoading ? '리사이징 중...' : '이미지 리사이징'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 리사이징 결과 */}
      {resizedImageUrl && resizedFileName && (
        <div className="mt-8">
          <h3 className="text-xl font-semibold mb-4 flex items-center">
            <CheckCircle size={24} className="mr-2 text-green-500" />
            리사이징 완료!
          </h3>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div>
              <h4 className="text-lg font-medium mb-2">리사이징된 이미지</h4>
              <div className="border rounded-lg p-4 bg-gray-50">
                <img
                  src={resizedImageUrl}
                  alt="리사이징된 이미지"
                  className="max-w-full max-h-64 mx-auto rounded"
                />
              </div>
            </div>
            <div className="flex flex-col justify-center">
              <p className="text-lg text-gray-700 mb-4">
                새로운 크기: {width} × {height} 픽셀
              </p>
              <button
                onClick={handleDownloadResizedImage}
                className="bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 transition-colors duration-200 flex items-center justify-center"
              >
                <Download size={20} className="mr-2" />
                {resizedFileName} 다운로드
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 숨겨진 캔버스 */}
      <canvas ref={canvasRef} className="hidden" />
    </div>
  );
};

export default ImageResizerPage;