import React from 'react';
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

import Home from "@/pages/HomePage"; // 홈 페이지 파일 이름이 HomePage.tsx 라면 이렇게
import PdfToDocPage from "@/pages/pdf-to-doc"; // pdf-to-doc.tsx 파일 경로
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
      </Routes>
    </Router>
  )
}

export default App;
