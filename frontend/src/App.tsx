import React, { Suspense, lazy } from 'react';
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import MainLayout from '@/components/MainLayout';
import { AuthProvider } from '@/contexts/AuthContext';

// 로딩 컴포넌트
const LoadingSpinner = () => (
  <div className="flex items-center justify-center min-h-screen">
    <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
  </div>
);

// 동적 import를 사용한 코드 분할
const Home = lazy(() => import("@/pages/HomePage"));
const PdfToDocPage = lazy(() => import("@/pages/pdf-to-doc"));
const PdfToJpgPage = lazy(() => import("@/pages/pdf-to-jpg"));
const PdfToAiPage = lazy(() => import("@/pages/pdf-to-ai"));
const PdfToBmpPage = lazy(() => import("@/pages/pdf-to-bmp"));
const PdfToGifPage = lazy(() => import("@/pages/pdf-to-gif"));
const PdfToPngPage = lazy(() => import("@/pages/pdf-to-png"));
const PdfToPptxPage = lazy(() => import("@/pages/pdf-to-pptx"));
const PdfToSvgPage = lazy(() => import("@/pages/pdf-to-svg"));
const PdfToTiffPage = lazy(() => import("@/pages/pdf-to-tiff"));
const PdfToXlsPage = lazy(() => import("@/pages/pdf-to-xls"));
const PdfVectorPage = lazy(() => import("@/pages/pdf-vector"));
const PdfImagePage = lazy(() => import("@/pages/pdf-image"));
const DocxPdfPage = lazy(() => import("@/pages/docx-pdf"));
const PptxPdfPage = lazy(() => import("@/pages/pptx-pdf"));
const XlsPdfPage = lazy(() => import("@/pages/xls-pdf"));
const ImageJpgPage = lazy(() => import("@/pages/image-jpg"));
const ImagesWebpPage = lazy(() => import("@/pages/images-webp"));
const ImagesPngPage = lazy(() => import("@/pages/images-png"));
const ImagesGifPage = lazy(() => import("@/pages/images-gif"));
const ImagesAllPage = lazy(() => import("@/pages/images-all"));

// 인증 관련 컴포넌트
const Login = lazy(() => import('@/pages/Login'));
const Profile = lazy(() => import('@/pages/Profile'));
const AuthCallback = lazy(() => import('@/pages/AuthCallback'));

function App() {
  return (
    <Router>
      <AuthProvider>
        <Suspense fallback={<LoadingSpinner />}>
          <Routes>
        <Route
          path="/"
          element={
            <MainLayout>
              <Home />
            </MainLayout>
          }
        />
        <Route
          path="/tools/pdf-doc"
          element={
            <MainLayout>
              <PdfToDocPage />
            </MainLayout>
          }
        />
        <Route
          path="/tools/pdf-jpg"
          element={
            <MainLayout>
              <PdfToJpgPage />
            </MainLayout>
          }
        />
        <Route
          path="/tools/pdf-ai"
          element={
            <MainLayout>
              <PdfToAiPage />
            </MainLayout>
          }
        />
        <Route
          path="/tools/pdf-bmp"
          element={
            <MainLayout>
              <PdfToBmpPage />
            </MainLayout>
          }
        />
        <Route
          path="/tools/pdf-gif"
          element={
            <MainLayout>
              <PdfToGifPage />
            </MainLayout>
          }
        />
        <Route
          path="/tools/pdf-png"
          element={
            <MainLayout>
              <PdfToPngPage />
            </MainLayout>
          }
        />
        <Route
          path="/tools/pdf-pptx"
          element={
            <MainLayout>
              <PdfToPptxPage />
            </MainLayout>
          }
        />
        <Route
          path="/tools/pdf-svg"
          element={
            <MainLayout>
              <PdfToSvgPage />
            </MainLayout>
          }
        />
        <Route
          path="/tools/pdf-tiff"
          element={
            <MainLayout>
              <PdfToTiffPage />
            </MainLayout>
          }
        />
        <Route
          path="/tools/pdf-xls"
          element={
            <MainLayout>
              <PdfToXlsPage />
            </MainLayout>
          }
        />
        <Route
          path="/tools/pdf-vector"
          element={
            <MainLayout>
              <PdfVectorPage />
            </MainLayout>
          }
        />
        <Route
          path="/tools/pdf-image"
          element={
            <MainLayout>
              <PdfImagePage />
            </MainLayout>
          }
        />
        <Route
          path="/tools/docx-pdf"
          element={
            <MainLayout>
              <DocxPdfPage />
            </MainLayout>
          }
        />
        <Route
          path="/tools/pptx-pdf"
          element={
            <MainLayout>
              <PptxPdfPage />
            </MainLayout>
          }
        />
        <Route
          path="/tools/xls-pdf"
          element={
            <MainLayout>
              <XlsPdfPage />
            </MainLayout>
          }
        />
        <Route
          path="/tools/image-jpg"
          element={
            <MainLayout>
              <ImageJpgPage />
            </MainLayout>
          }
        />
        <Route
          path="/tools/images-webp"
          element={
            <MainLayout>
              <ImagesWebpPage />
            </MainLayout>
          }
        />
        <Route
          path="/tools/images-png"
          element={
            <MainLayout>
              <ImagesPngPage />
            </MainLayout>
          }
        />
        <Route
          path="/tools/images-gif"
          element={
            <MainLayout>
              <ImagesGifPage />
            </MainLayout>
          }
        />
        <Route
          path="/tools/images-all"
          element={
            <MainLayout>
              <ImagesAllPage />
            </MainLayout>
          }
        />
        
        {/* 인증 관련 라우트 */}
        <Route path="/login" element={<Login />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="/auth/callback" element={<AuthCallback />} />
          </Routes>
        </Suspense>
      </AuthProvider>
    </Router>
  )
}

export default App;
