// src/App.tsx

import React from 'react';
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

// 페이지들을 가져옵니다.
import Home from "@/pages/Home";
import PdfConverterPage from "@/pages/PdfConverterPage";

// 방금 만든 MainLayout 컴포넌트를 가져옵니다.
import MainLayout from '@/components/MainLayout';

function App() {
  return (
    <Router>
      {/* Routes 전체를 MainLayout으로 감싸지 않고,
          각 Route의 element를 MainLayout으로 감싸서 페이지를 전달합니다. */}
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
              <PdfConverterPage />
            </MainLayout>
          }
        />
        {/* 앞으로 추가될 모든 페이지도 이런 방식으로 MainLayout으로 감싸줍니다. */}
      </Routes>
    </Router>
  )
}

export default App;
