import React from 'react';
import Navbar from '@/components/Navbar'; // Navbar 컴포넌트 경로
import Footer from '@/components/Footer'; // Footer 컴포넌트 경로

interface MainLayoutProps {
  children: React.ReactNode;
}

const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  return (
    <div className="flex flex-col min-h-screen bg-gray-50">
      <Navbar />
      <main className="flex-grow container mx-auto px-4 py-8">
        {children}
      </main>
      <Footer />
    </div>
  );
};

export default MainLayout;