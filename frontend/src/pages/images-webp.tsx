import React, { useEffect } from 'react';
import PageTitle from '../shared/PageTitle';

const ImagesWebpPage: React.FC = () => {
  useEffect(() => {
    // Render 서비스로 리다이렉트
    window.location.href = 'https://images-webp.onrender.com/';
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <PageTitle suffix="- Image to WEBP Converter" />
        
        <div className="bg-white rounded-lg shadow-lg p-8 text-center">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">Image to WEBP Converter</h1>
          <p className="text-gray-600 mb-8">JPG, PNG, BMP, TIFF, GIF, SVG, PSD, HEIC, RAW 이미지를 고품질 WEBP로 변환합니다.</p>
          
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600 mb-4">WEBP 변환 도구로 이동 중...</p>
          <p className="text-sm text-gray-500">
            자동으로 이동되지 않는다면{' '}
            <a 
              href="https://images-webp.onrender.com/" 
              className="text-blue-600 hover:text-blue-800 underline"
              target="_blank"
              rel="noopener noreferrer"
            >
              여기를 클릭하세요
            </a>
          </p>
        </div>
      </div>
    </div>
  );
};

export default ImagesWebpPage;