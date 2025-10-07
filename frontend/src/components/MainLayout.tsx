// src/components/MainLayout.tsx

import React from 'react';
import Navbar from '@/components/Navbar'; // 당신의 Navbar 컴포넌트 경로
import Footer from '@/components/Footer'; // 당신의 Footer 컴포넌트 경로

// 'children'은 이 레이아웃으로 감싸질 페이지 내용을 의미합니다.
interface MainLayoutProps {
  children: React.ReactNode;
}

const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  return (
    <div className="flex flex-col min-h-screen">
      <Navbar />
      <main className="flex-grow">
        {children} {/* 여기에 Home.tsx나 PdfConverterPage.tsx 같은 페이지 내용이 들어옵니다. */}
      </main>
      <Footer />
    </div>
  );
};

export default MainLayout;