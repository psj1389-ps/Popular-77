// Popular-77/frontend/src/pages/Home.tsx (또는 HomePage.tsx)
import React, { useRef } from 'react';
import Hero from '../components/Hero';               // Hero 섹션 컴포넌트
import PopularTools from '../components/PopularTools'; // 인기 도구 섹션 컴포넌트
import ToolsPreview from '../components/ToolsPreview'; // 전체 도구 미리보기 섹션 컴포넌트

// 💡 constants.ts에서 TOOLS 배열 임포트
import { TOOLS } from '../data/constants';

const Home: React.FC = () => {
  // 각 섹션을 가리킬 ref들을 만듭니다.
  const allToolsRef = useRef<HTMLDivElement>(null);
  const pdfToolsRef = useRef<HTMLDivElement>(null);
  const imageToolsRef = useRef<HTMLDivElement>(null);
  const aiToolsRef = useRef<HTMLDivElement>(null);
  const imageConvertRef = useRef<HTMLDivElement>(null);
  const documentToolsRef = useRef<HTMLDivElement>(null);
  const youtubeToolsRef = useRef<HTMLDivElement>(null);
  const videoToolsRef = useRef<HTMLDivElement>(null);

  // 클릭 시 스크롤을 실행하는 함수
  const scrollToSection = (ref: React.RefObject<HTMLDivElement>) => {
    ref.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // 💡 featured: true 인 도구들만 필터링하여 인기 도구 섹션에 전달
  const featuredTools = TOOLS.filter(tool => tool.featured);

  return (
    // 💡 Navbar와 Footer는 App.tsx에서 전역으로 관리하므로 여기서는 제거합니다.
    //    main 태그만 남기고, 필요한 레이아웃 스타일은 App.tsx의 main 태그나
    //    각 섹션 컴포넌트 내부에서 처리하는 것이 좋습니다.
    <main>
      {/* 1. 히어로 섹션 */}
      <Hero />

      {/* 2. 인기 도구 섹션 */}
      {/* 💡 featuredTools를 prop으로 전달 */}
      <PopularTools 
        tools={featuredTools} 
        refs={{
          allToolsRef,
          pdfToolsRef,
          imageToolsRef,
          aiToolsRef,
          imageConvertRef,
          documentToolsRef,
          youtubeToolsRef,
          videoToolsRef
        }}
        scrollToSection={scrollToSection}
      />

      {/* 3. 도구 미리보기 섹션 (모든 도구 목록) */}
      {/* 💡 TOOLS 전체를 prop으로 전달 */}
      <ToolsPreview tools={TOOLS} />

      {/* TODO: 필요하다면 여기에 다른 섹션들을 추가할 수 있습니다. */}
      {/* 예: 사용 후기, 왜 우리 도구를 사용해야 하는지 등 */}
    </main>
  );
};

export default Home;
