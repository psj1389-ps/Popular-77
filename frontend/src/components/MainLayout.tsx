// src/components/MainLayout.tsx

import React from 'react';
import Navbar from '@/components/Navbar';
import Footer from '@/components/Footer';

interface MainLayoutProps {
  children: React.ReactNode;
}

const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  return (
    <div className="flex flex-col min-h-screen bg-gray-50"> {/* 전체 배경색을 연한 회색으로 */}
      <Navbar />
      {/* main 영역 자체는 배경 없이 자식 컴포넌트가 배경을 처리하도록 합니다. */}
      <main className="flex-grow">
        {children}
      </main>
      <Footer />
    </div>
  );
};

export default MainLayout;