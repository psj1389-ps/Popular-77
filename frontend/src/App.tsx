import React from 'react';
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

import Home from "@/pages/HomePage"; // 홈 페이지 파일 이름이 HomePage.tsx 라면 이렇게
import PdfToDocPage from "@/pages/pdf-to-doc"; // pdf-to-doc.tsx 파일 경로
import PdfToJpgPage from "@/pages/pdf-to-jpg"; // pdf-to-jpg.tsx 파일 경로
import PdfToAiPage from "@/pages/pdf-to-ai";
import PdfToBmpPage from "@/pages/pdf-to-bmp";
import PdfToGifPage from "@/pages/pdf-to-gif";
import PdfToPptxPage from "@/pages/pdf-to-pptx";
import PdfToSvgPage from "@/pages/pdf-to-svg";
import PdfToTiffPage from "@/pages/pdf-to-tiff";
import PdfToXlsPage from "@/pages/pdf-to-xls";
import MainLayout from '@/components/MainLayout';

function App() {
  return (
    <Router>
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
      </Routes>
    </Router>
  )
}

export default App;
