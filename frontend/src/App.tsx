// Popular-77/frontend/src/App.tsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

import Navbar from './components/Navbar';
import Footer from './components/Footer';

import HomePage from './pages/HomePage';
import PrivacyPage from './pages/PrivacyPage';
import TermsPage from './pages/TermsPage';

import { TOOLS } from './data/constants';

import './index.css';

// 도구 페이지 컴포넌트들 (lazy 로딩)
const ImageResizerPage = React.lazy(() => import('./pages/ImageResizerPage'));
const PdfToDocPage = React.lazy(() => import('./pages/pdf-to-doc'));
// 💡 pdf-to-jpg.tsx 컴포넌트 임포트 (lazy 로딩)
const PdfToJpgPage = React.lazy(() => import('./pages/pdf-to-jpg')); // 파일명에 맞게 변경

function App() {
  return (
    <Router>
      <div className="app-container">
        <Navbar /> {/* 헤더 유지 */}

        <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Routes>
            <Route path="/" element={<HomePage />} />

            {TOOLS.map((tool) => {
              let ToolPageComponent: React.ComponentType | null = null;
              switch (tool.id) {
                case 'image-resizer':
                  ToolPageComponent = ImageResizerPage;
                  break;
                case 'pdf-to-doc':
                  ToolPageComponent = PdfToDocPage;
                  break;
                case 'pdf-to-jpg': // 💡 2. pdf-to-jpg 라우트 케이스 추가 확인
                  ToolPageComponent = PdfToJpgPage;
                  break;  
                // TODO: 여기에 다른 도구 ID에 대한 case를 추가하세요.
                default:
                  ToolPageComponent = () => <div className="p-4 text-center text-red-500">개발 중인 도구입니다: {tool.name}</div>;
                  break;
              }

              return (
                <Route
                  key={tool.id}
                  path={tool.path}
                  element={
                    ToolPageComponent ? (
                      <React.Suspense fallback={<div>로딩 중...</div>}>
                        <ToolPageComponent />
                      </React.Suspense>
                    ) : (
                      <div className="p-4 text-center text-red-500">페이지를 찾을 수 없습니다.</div>
                    )
                  }
                />
              );
            })}

            <Route path="/privacy" element={<PrivacyPage />} />
            <Route path="/terms" element={<TermsPage />} />
            {/* TODO: Footer.tsx의 다른 링크들에 해당하는 라우트를 추가합니다. */}

            <Route path="*" element={<div className="p-4 text-center text-red-500 text-lg">페이지를 찾을 수 없습니다 (404)</div>} />
          </Routes>
        </main>

        <Footer />
      </div>
    </Router>
  );
}

export default App;
