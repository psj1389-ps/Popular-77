'use client';

import Header from '@/components/Header';
import Footer from '@/components/Footer';
import TextInput from '@/components/TextInput';
import StatsDashboard from '@/components/StatsDashboard';
import SettingsPanel from '@/components/SettingsPanel';
import TextConverter from '@/components/TextConverter';
import TextCorrector from '@/components/TextCorrector';
import FileOperations from '@/components/FileOperations';
import { StoreProvider } from '@/stores/StoreContext';

export default function Home() {
  return (
    <StoreProvider>
      <div className="min-h-screen bg-gray-100">
        <Header />
        
        <div className="py-8">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
            {/* 메인 카드 컨테이너 */}
            <div className="bg-white rounded-lg shadow-lg p-6 sm:p-8 mb-8">
              <div className="text-center mb-8">
                <div className="inline-flex items-center gap-3 mb-4">
                  <span className="text-4xl">📊</span>
                </div>
                <h2 className="text-xl sm:text-2xl font-bold text-gray-900 mb-2">
                  Word Counter - 글자수 세기
                </h2>
                <p className="text-gray-600 text-sm sm:text-base">
                  다양한 텍스트 형식을 고품질로 분석 (글자수, 단어수, 문장수 → 실시간 분석, 변환, 교정)
                </p>
              </div>

              <div className="flex justify-center mb-6 sm:mb-8">
                <SettingsPanel />
              </div>
              
              <div className="grid grid-cols-1 xl:grid-cols-5 gap-6 sm:gap-8 lg:gap-10 mb-6 sm:mb-8">
                <div className="xl:col-span-3">
                  <TextInput />
                </div>
                <div className="xl:col-span-2">
                  <StatsDashboard />
                </div>
              </div>
              
              <div className="space-y-6 sm:space-y-8 lg:space-y-10">
                <TextConverter />
                <TextCorrector />
                <FileOperations />
              </div>
            </div>
          </div>
        </div>
        
        <Footer />
      </div>
    </StoreProvider>
  );
}
