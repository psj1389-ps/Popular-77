import { ArrowRight, Grid3X3, FileText, Image, Brain, RefreshCw, FileType, Youtube, Video } from 'lucide-react';
import { Tool } from '../types';

interface PopularToolsProps {
  tools: Tool[];
  refs?: {
    allToolsRef: React.RefObject<HTMLDivElement>;
    pdfToolsRef: React.RefObject<HTMLDivElement>;
    imageToolsRef: React.RefObject<HTMLDivElement>;
    aiToolsRef: React.RefObject<HTMLDivElement>;
    imageConvertRef: React.RefObject<HTMLDivElement>;
    documentToolsRef: React.RefObject<HTMLDivElement>;
    youtubeToolsRef: React.RefObject<HTMLDivElement>;
    videoToolsRef: React.RefObject<HTMLDivElement>;
  };
  scrollToSection?: (ref: React.RefObject<HTMLDivElement>) => void;
}

const PopularTools: React.FC<PopularToolsProps> = ({ tools, refs, scrollToSection }) => {
  const categories = [
    { name: '모든 도구', targetId: 'all-tools', icon: Grid3X3, ref: refs?.allToolsRef },
    { name: 'PDF변환도구', targetId: 'pdf-tools', icon: FileText, ref: refs?.pdfToolsRef },
    { name: '이미지도구', targetId: 'image-tools', icon: Image, ref: refs?.imageToolsRef },
    { name: 'AI도구', featured: true, targetId: 'ai-tools', icon: Brain, ref: refs?.aiToolsRef },
    { name: '이미지변환도구', targetId: 'image-conversion-tools', icon: RefreshCw, ref: refs?.imageConvertRef },
    { name: '문서도구', targetId: 'document-tools', icon: FileType, ref: refs?.documentToolsRef },
    { name: 'YOUTUBE도구', targetId: 'youtube-tools', icon: Youtube, ref: refs?.youtubeToolsRef },
    { name: '동영상도구', targetId: 'video-tools', icon: Video, ref: refs?.videoToolsRef },
  ];

  const scrollToSectionFallback = (targetId: string) => {
    const element = document.getElementById(targetId);
    if (element) {
      const elementPosition = element.offsetTop;
      const offsetPosition = elementPosition - 30; // 30px 오프셋 추가
      
      window.scrollTo({
        top: offsetPosition,
        behavior: 'smooth'
      });
    }
  };

  const handleCategoryClick = (category: any) => {
    if (scrollToSection && category.ref) {
      scrollToSection(category.ref);
    } else {
      scrollToSectionFallback(category.targetId);
    }
  };

  return (
    <section className="py-20 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-gray-900">인기 도구들</h2>
          <p className="mt-4 text-xl text-gray-600 font-bold">가장 많이 사용되는 필수 온라인 도구들을 만나보세요.</p>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {categories.map((category) => {
            const IconComponent = category.icon;
            return (
              <div
                key={category.name}
                onClick={() => handleCategoryClick(category)}
                className="px-6 py-4 rounded-lg font-semibold text-center transition-all duration-200 bg-blue-100 text-blue-800 hover:bg-blue-200 hover:shadow-md cursor-pointer flex flex-col items-center gap-2"
              >
                <IconComponent className="w-6 h-6" />
                <span className="text-sm">{category.name}</span>
              </div>
            );
          })}
        </div>
        <div className="text-center mt-12">
          <div 
            onClick={() => window.open('https://popular-77-deoe.vercel.app/tools/pdf-doc', '_blank')}
            className="text-blue-600 hover:text-blue-800 font-semibold inline-flex items-center text-xl cursor-pointer"
          >
            77개 이상의 인기 도구가 제공하는 강력한 기능을 확인해보세요.
            <ArrowRight className="ml-2 w-4 h-4" />
          </div>
        </div>
      </div>

      {/* 각 카테고리별 섹션 */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-16">
        {/* 모든 도구 섹션 */}
        <div ref={refs?.allToolsRef} id="all-tools" className="mb-16 scroll-mt-20">
          <h3 className="text-2xl font-bold text-gray-900 mb-6">
            모든 도구
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-1 gap-6">
            <div className="bg-gray-50 p-6 rounded-lg hover:shadow-lg transition-all duration-200 transform hover:scale-105">
              <h4 className="font-semibold text-lg mb-2">전체 도구 모음</h4>
              <p className="text-gray-600">모든 변환 도구를 한 곳에서 이용하세요.</p>
            </div>
          </div>
        </div>

        {/* PDF변환도구 섹션 */}
        <div ref={refs?.pdfToolsRef} id="pdf-tools" className="mb-16 scroll-mt-20">
          <h3 className="text-2xl font-bold text-gray-900 mb-6">
            PDF변환도구
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-blue-50 p-6 rounded-lg hover:bg-blue-100 hover:shadow-lg transition-all duration-200 transform hover:scale-105">
              <h4 className="font-semibold text-lg mb-2">PDF to DOCX</h4>
              <p className="text-gray-600">PDF 파일을 DOCX로 변환합니다.</p>
            </div>
            <div className="bg-blue-50 p-6 rounded-lg hover:bg-blue-100 hover:shadow-lg transition-all duration-200 transform hover:scale-105">
              <h4 className="font-semibold text-lg mb-2">PDF 병합</h4>
              <p className="text-gray-600">여러 PDF 파일을 하나로 병합합니다.</p>
            </div>
            <div className="bg-blue-50 p-6 rounded-lg hover:bg-blue-100 hover:shadow-lg transition-all duration-200 transform hover:scale-105">
              <h4 className="font-semibold text-lg mb-2">PDF 분할</h4>
              <p className="text-gray-600">PDF 파일을 여러 개로 분할합니다.</p>
            </div>
          </div>
        </div>

        {/* 이미지도구 섹션 */}
        <div ref={refs?.imageToolsRef} id="image-tools" className="mb-16 scroll-mt-20">
          <h3 className="text-2xl font-bold text-gray-900 mb-6">
            이미지도구
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-green-50 p-6 rounded-lg hover:bg-green-100 hover:shadow-lg transition-all duration-200 transform hover:scale-105">
              <h4 className="font-semibold text-lg mb-2">이미지 리사이저</h4>
              <p className="text-gray-600">이미지 크기를 조정하고 최적화합니다.</p>
            </div>
            <div className="bg-green-50 p-6 rounded-lg hover:bg-green-100 hover:shadow-lg transition-all duration-200 transform hover:scale-105">
              <h4 className="font-semibold text-lg mb-2">이미지 압축</h4>
              <p className="text-gray-600">이미지 파일 크기를 줄여 최적화합니다.</p>
            </div>
            <div className="bg-green-50 p-6 rounded-lg hover:bg-green-100 hover:shadow-lg transition-all duration-200 transform hover:scale-105">
              <h4 className="font-semibold text-lg mb-2">이미지 변환</h4>
              <p className="text-gray-600">다양한 이미지 형식 간 변환을 지원합니다.</p>
            </div>
          </div>
        </div>

        {/* AI도구 섹션 */}
        <div ref={refs?.aiToolsRef} id="ai-tools" className="mb-16 scroll-mt-20">
          <h3 className="text-2xl font-bold text-gray-900 mb-6">
            AI도구
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-purple-50 p-6 rounded-lg hover:bg-purple-100 hover:shadow-lg transition-all duration-200 transform hover:scale-105">
              <h4 className="font-semibold text-lg mb-2">AI 텍스트 생성</h4>
              <p className="text-gray-600">인공지능을 활용한 텍스트 생성 도구입니다.</p>
            </div>
            <div className="bg-purple-50 p-6 rounded-lg hover:bg-purple-100 hover:shadow-lg transition-all duration-200 transform hover:scale-105">
              <h4 className="font-semibold text-lg mb-2">AI 이미지 생성</h4>
              <p className="text-gray-600">텍스트 설명으로 이미지를 생성합니다.</p>
            </div>
            <div className="bg-purple-50 p-6 rounded-lg hover:bg-purple-100 hover:shadow-lg transition-all duration-200 transform hover:scale-105">
              <h4 className="font-semibold text-lg mb-2">AI 번역</h4>
              <p className="text-gray-600">고품질 AI 번역 서비스를 제공합니다.</p>
            </div>
          </div>
        </div>

        {/* 이미지변환도구 섹션 */}
        <div ref={refs?.imageConvertRef} id="image-conversion-tools" className="mb-16 scroll-mt-20">
          <h3 className="text-2xl font-bold text-gray-900 mb-6">
            이미지변환도구
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="bg-indigo-50 p-6 rounded-lg hover:bg-indigo-100 hover:shadow-lg transition-all duration-200 transform hover:scale-105">
              <h4 className="font-semibold text-lg mb-2">JPG 변환</h4>
              <p className="text-gray-600">다양한 형식을 JPG로 변환합니다.</p>
            </div>
            <div className="bg-indigo-50 p-6 rounded-lg hover:bg-indigo-100 hover:shadow-lg transition-all duration-200 transform hover:scale-105">
              <h4 className="font-semibold text-lg mb-2">PNG 변환</h4>
              <p className="text-gray-600">이미지를 PNG 형식으로 변환합니다.</p>
            </div>
            <div className="bg-indigo-50 p-6 rounded-lg hover:bg-indigo-100 hover:shadow-lg transition-all duration-200 transform hover:scale-105">
              <h4 className="font-semibold text-lg mb-2">WebP 변환</h4>
              <p className="text-gray-600">최신 WebP 형식으로 변환합니다.</p>
            </div>
            <div className="bg-indigo-50 p-6 rounded-lg hover:bg-indigo-100 hover:shadow-lg transition-all duration-200 transform hover:scale-105">
              <h4 className="font-semibold text-lg mb-2">GIF 변환</h4>
              <p className="text-gray-600">애니메이션 GIF로 변환합니다.</p>
            </div>
          </div>
        </div>

        {/* 문서도구 섹션 */}
        <div ref={refs?.documentToolsRef} id="document-tools" className="mb-16 scroll-mt-20">
          <h3 className="text-2xl font-bold text-gray-900 mb-6">
            문서도구
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-orange-50 p-6 rounded-lg hover:bg-orange-100 hover:shadow-lg transition-all duration-200 transform hover:scale-105">
              <h4 className="font-semibold text-lg mb-2">워드 변환</h4>
              <p className="text-gray-600">다양한 문서를 워드 형식으로 변환합니다.</p>
            </div>
            <div className="bg-orange-50 p-6 rounded-lg hover:bg-orange-100 hover:shadow-lg transition-all duration-200 transform hover:scale-105">
              <h4 className="font-semibold text-lg mb-2">엑셀 변환</h4>
              <p className="text-gray-600">데이터를 엑셀 형식으로 변환합니다.</p>
            </div>
            <div className="bg-orange-50 p-6 rounded-lg hover:bg-orange-100 hover:shadow-lg transition-all duration-200 transform hover:scale-105">
              <h4 className="font-semibold text-lg mb-2">파워포인트 변환</h4>
              <p className="text-gray-600">프레젠테이션을 PPT로 변환합니다.</p>
            </div>
          </div>
        </div>

        {/* YOUTUBE도구 섹션 */}
        <div ref={refs?.youtubeToolsRef} id="youtube-tools" className="mb-16 scroll-mt-20">
          <h3 className="text-2xl font-bold text-gray-900 mb-6">
            YOUTUBE도구
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-red-50 p-6 rounded-lg hover:bg-red-100 hover:shadow-lg transition-all duration-200 transform hover:scale-105">
              <h4 className="font-semibold text-lg mb-2">유튜브 다운로더</h4>
              <p className="text-gray-600">유튜브 영상을 다운로드합니다.</p>
            </div>
            <div className="bg-red-50 p-6 rounded-lg hover:bg-red-100 hover:shadow-lg transition-all duration-200 transform hover:scale-105">
              <h4 className="font-semibold text-lg mb-2">썸네일 추출</h4>
              <p className="text-gray-600">유튜브 영상의 썸네일을 추출합니다.</p>
            </div>
            <div className="bg-red-50 p-6 rounded-lg hover:bg-red-100 hover:shadow-lg transition-all duration-200 transform hover:scale-105">
              <h4 className="font-semibold text-lg mb-2">자막 추출</h4>
              <p className="text-gray-600">유튜브 영상의 자막을 추출합니다.</p>
            </div>
          </div>
        </div>

        {/* 동영상도구 섹션 */}
        <div ref={refs?.videoToolsRef} id="video-tools" className="mb-16 scroll-mt-20">
          <h3 className="text-2xl font-bold text-gray-900 mb-6">
            동영상도구
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-blue-50 p-6 rounded-lg hover:bg-blue-100 hover:shadow-lg transition-all duration-200 transform hover:scale-105">
              <h4 className="font-semibold text-lg mb-2">동영상 압축</h4>
              <p className="text-gray-600">동영상 파일 크기를 줄여 최적화합니다.</p>
            </div>
            <div className="bg-blue-50 p-6 rounded-lg hover:bg-blue-100 hover:shadow-lg transition-all duration-200 transform hover:scale-105">
              <h4 className="font-semibold text-lg mb-2">동영상 변환</h4>
              <p className="text-gray-600">다양한 동영상 형식 간 변환을 지원합니다.</p>
            </div>
            <div className="bg-blue-50 p-6 rounded-lg hover:bg-blue-100 hover:shadow-lg transition-all duration-200 transform hover:scale-105">
              <h4 className="font-semibold text-lg mb-2">동영상 자르기</h4>
              <p className="text-gray-600">원하는 길이로 동영상을 자릅니다.</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default PopularTools;