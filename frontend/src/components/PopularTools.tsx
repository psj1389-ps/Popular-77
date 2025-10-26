import { ArrowRight, Grid3X3, FileText, Image, Brain, RefreshCw, FileType, Youtube, Video, FileSpreadsheet, Presentation, FileTextIcon, ImageIcon, Shapes, Camera, Monitor, Film, Palette, Images, Zap, Expand, Minimize2, Type, Sparkles, Languages, FileImage, Play, Download, Subtitles, Minimize, Scissors, Settings, Wand2 } from 'lucide-react';
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
    { name: '베스트인기도구', targetId: 'best-tools', icon: Grid3X3, ref: refs?.allToolsRef },
    { name: 'PDF변환도구', targetId: 'pdf-tools', icon: FileText, ref: refs?.pdfToolsRef },
    { name: '편집&최적화도구', targetId: 'image-tools', icon: Image, ref: refs?.imageToolsRef },
    { name: 'AI도구', featured: true, targetId: 'ai-tools', icon: Brain, ref: refs?.aiToolsRef },
    { name: '이미지&동영상변환도구', targetId: 'image-conversion-tools', icon: RefreshCw, ref: refs?.imageConvertRef },
    { name: '문서변환도구', targetId: 'document-tools', icon: FileType, ref: refs?.documentToolsRef },
    { name: '컨텐츠추출도구', targetId: 'youtube-tools', icon: Youtube, ref: refs?.youtubeToolsRef },
    { name: '유틸리티도구', targetId: 'video-tools', icon: Settings, ref: refs?.videoToolsRef },
  ];

  const scrollToSectionFallback = (targetId: string) => {
    const element = document.getElementById(targetId);
    if (element) {
      const elementPosition = element.offsetTop;
      const offsetPosition = elementPosition - 200; // 200px 오프셋으로 조정하여 h3 제목이 화면 중간에 절대 위치하도록 개선
      
      window.scrollTo({
        top: offsetPosition,
        behavior: 'smooth'
      });
    }
  };

  const handleCategoryClick = (category: any) => {
    // 베스트인기도구 클릭시 ToolsPreview 섹션으로 스크롤
    if (category.name === '베스트인기도구') {
      const toolsPreviewSection = document.querySelector('section.py-20.bg-gray-50');
      if (toolsPreviewSection) {
        const elementPosition = toolsPreviewSection.getBoundingClientRect().top + window.pageYOffset;
        const offsetPosition = elementPosition - 100; // 100px 오프셋
        
        window.scrollTo({
          top: offsetPosition,
          behavior: 'smooth'
        });
        return;
      }
    }
    
    if (scrollToSection && category.ref) {
      scrollToSection(category.ref);
    } else {
      scrollToSectionFallback(category.targetId);
    }
  };

  return (
    <section className="py-20 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
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

      {/* 전체 카테고리 섹션 */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-16">
        {/* 모든 도구 섹션 */}
        <div ref={refs?.allToolsRef} id="all-tools" className="mb-16 scroll-mt-20">
          <h3 className="text-2xl font-bold text-gray-900 mb-6">
            모든 도구
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-1 gap-6">
            <div className="bg-gray-50 p-6 rounded-lg hover:shadow-lg transition-all duration-200 transform hover:scale-105 h-40 flex flex-col">
              <h4 className="font-semibold text-lg mb-2">전체 도구 모음</h4>
              <p className="text-gray-600 flex-grow">모든 변환 도구를 한 곳에서 사용하세요</p>
            </div>
          </div>
        </div>

        {/* PDF변환도구 섹션 */}
        <div ref={refs?.pdfToolsRef} id="pdf-tools" className="mb-16 scroll-mt-20">
          <h3 className="text-2xl font-bold text-gray-900 mb-6">
            PDF변환도구
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div 
              onClick={() => window.open('https://popular-77.vercel.app/tools/pdf-doc', '_blank')}
              className="bg-blue-50 p-6 rounded-lg hover:bg-blue-100 hover:shadow-lg transition-all duration-200 cursor-pointer transform hover:scale-105 h-40 flex flex-col"
            >
              <div className="flex items-center mb-2">
                <FileText className="w-6 h-6 text-blue-600 mr-2" />
                <h4 className="font-semibold text-lg">PDF to DOCX</h4>
              </div>
              <p className="text-gray-600 flex-grow">PDF 파일을 DOCX로 변환합니다.</p>
            </div>

            <div 
              onClick={() => window.location.href = '/tools/pdf-pptx'}
              className="bg-blue-50 p-6 rounded-lg hover:bg-blue-100 hover:shadow-lg transition-all duration-200 cursor-pointer transform hover:scale-105 h-40 flex flex-col"
            >
              <div className="flex items-center mb-2">
                <Presentation className="w-6 h-6 text-orange-600 mr-2" />
                <h4 className="font-semibold text-lg">PDF to PPTX</h4>
              </div>
              <p className="text-gray-600 flex-grow">PDF 파일을 PPTX로 변환합니다.</p>
            </div>
            <div 
              onClick={() => window.location.href = '/tools/pdf-xls'}
              className="bg-blue-50 p-6 rounded-lg hover:bg-blue-100 hover:shadow-lg transition-all duration-200 cursor-pointer transform hover:scale-105 h-40 flex flex-col"
            >
              <div className="flex items-center mb-2">
                <FileSpreadsheet className="w-6 h-6 text-green-600 mr-2" />
                <h4 className="font-semibold text-lg">PDF to Excel</h4>
              </div>
              <p className="text-gray-600 flex-grow">PDF 파일을 Excel 스프레드시트로 변환합니다.</p>
            </div>
            <div 
              onClick={() => window.location.href = '/tools/pdf-jpg'}
              className="bg-blue-50 p-6 rounded-lg hover:bg-blue-100 hover:shadow-lg transition-all duration-200 cursor-pointer transform hover:scale-105 h-40 flex flex-col"
            >
              <div className="flex items-center mb-2">
                <Image className="w-6 h-6 text-red-600 mr-2" />
                <h4 className="font-semibold text-lg">PDF to JPG</h4>
              </div>
              <p className="text-gray-600 flex-grow">PDF 파일을 JPG 이미지로 변환합니다.</p>
            </div>
            <div 
              onClick={() => window.location.href = '/tools/pdf-png'}
              className="bg-blue-50 p-6 rounded-lg hover:bg-blue-100 hover:shadow-lg transition-all duration-200 cursor-pointer transform hover:scale-105 h-40 flex flex-col"
            >
              <div className="flex items-center mb-2">
                <ImageIcon className="w-6 h-6 text-purple-600 mr-2" />
                <h4 className="font-semibold text-lg">PDF to PNG</h4>
              </div>
              <p className="text-gray-600 flex-grow">PDF 파일을 PNG 이미지로 변환합니다.</p>
            </div>
            <div 
              onClick={() => window.location.href = '/tools/pdf-svg'}
              className="bg-blue-50 p-6 rounded-lg hover:bg-blue-100 hover:shadow-lg transition-all duration-200 cursor-pointer transform hover:scale-105 h-40 flex flex-col"
            >
              <div className="flex items-center mb-2">
                <Shapes className="w-6 h-6 text-teal-600 mr-2" />
                <h4 className="font-semibold text-lg">PDF to SVG</h4>
              </div>
              <p className="text-gray-600 flex-grow">PDF 파일을 SVG 벡터 방식으로 변환합니다.</p>
            </div>
            <div 
              onClick={() => window.location.href = '/tools/pdf-tiff'}
              className="bg-blue-50 p-6 rounded-lg hover:bg-blue-100 hover:shadow-lg transition-all duration-200 cursor-pointer transform hover:scale-105 h-40 flex flex-col"
            >
              <div className="flex items-center mb-2">
                <Camera className="w-6 h-6 text-amber-600 mr-2" />
                <h4 className="font-semibold text-lg">PDF to TIFF</h4>
              </div>
              <p className="text-gray-600 flex-grow">PDF 파일을 TIFF 이미지로 변환합니다.</p>
            </div>
            <div 
              onClick={() => window.location.href = '/tools/pdf-bmp'}
              className="bg-blue-50 p-6 rounded-lg hover:bg-blue-100 hover:shadow-lg transition-all duration-200 cursor-pointer transform hover:scale-105 h-40 flex flex-col"
            >
              <div className="flex items-center mb-2">
                <Monitor className="w-6 h-6 text-gray-600 mr-2" />
                <h4 className="font-semibold text-lg">PDF to BMP</h4>
              </div>
              <p className="text-gray-600 flex-grow">PDF 파일을 BMP 이미지로 변환합니다.</p>
            </div>
            <div 
              onClick={() => window.location.href = '/tools/pdf-gif'}
              className="bg-blue-50 p-6 rounded-lg hover:bg-blue-100 hover:shadow-lg transition-all duration-200 cursor-pointer transform hover:scale-105 h-40 flex flex-col"
            >
              <div className="flex items-center mb-2">
                <Film className="w-6 h-6 text-pink-600 mr-2" />
                <h4 className="font-semibold text-lg">PDF to GIF</h4>
              </div>
              <p className="text-gray-600 flex-grow">PDF 파일을 GIF 애니메이션으로 변환합니다.</p>
            </div>
            <div 
              onClick={() => window.location.href = '/tools/pdf-ai'}
              className="bg-blue-50 p-6 rounded-lg hover:bg-blue-100 hover:shadow-lg transition-all duration-200 cursor-pointer transform hover:scale-105 h-40 flex flex-col"
            >
              <div className="flex items-center mb-2">
                <Palette className="w-6 h-6 text-yellow-600 mr-2" />
                <h4 className="font-semibold text-lg">PDF to AI</h4>
              </div>
              <p className="text-gray-600 flex-grow">PDF 파일을 AI(일러스트레이터) 형식으로 변환합니다.</p>
            </div>
            <div 
              onClick={() => window.location.href = '/tools/pdf-image'}
              className="bg-blue-50 p-6 rounded-lg hover:bg-blue-100 hover:shadow-lg transition-all duration-200 cursor-pointer transform hover:scale-105 h-40 flex flex-col"
            >
              <div className="flex items-center mb-2">
                <Images className="w-6 h-6 text-lime-600 mr-2" />
                <h4 className="font-semibold text-lg">PDF to Image</h4>
              </div>
              <p className="text-gray-600 flex-grow">PDF 파일을 다양한 Image로 변환합니다.</p>
            </div>
            <div 
              onClick={() => window.location.href = '/tools/pdf-vector'}
              className="bg-blue-50 p-6 rounded-lg hover:bg-blue-100 hover:shadow-lg transition-all duration-200 cursor-pointer transform hover:scale-105 h-40 flex flex-col"
            >
              <div className="flex items-center mb-2">
                <Zap className="w-6 h-6 text-indigo-600 mr-2" />
                <h4 className="font-semibold text-lg">PDF to Vector</h4>
              </div>
              <p className="text-gray-600 flex-grow">PDF 파일을 다양한 Vector방식으로 변환합니다.</p>
            </div>
          </div>
        </div>

        {/* 문서변환도구 섹션 */}
        <div ref={refs?.documentToolsRef} id="document-tools" className="mb-16 scroll-mt-20">
          <h3 className="text-2xl font-bold mb-6 text-gray-800 flex items-center">
            문서변환도구          </h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div 
              onClick={() => window.open('https://77-tools.xyz/tools/docx-pdf', '_blank')}
              className="bg-orange-50 p-6 rounded-lg hover:bg-orange-100 hover:shadow-lg transition-all duration-200 cursor-pointer transform hover:scale-105 h-40 flex flex-col"
            >
              <div className="flex items-center mb-2">
                <FileText className="w-6 h-6 text-blue-600 mr-2" />
                <h4 className="font-semibold text-lg">DOCX to PDF (Word)</h4>
              </div>
              <p className="text-gray-600 flex-grow">워드 형식의 문서를 PDF로 변환합니다.</p>
            </div>
            <div 
              onClick={() => window.open('https://77-tools.xyz/tools/xls-pdf', '_blank')}
              className="bg-orange-50 p-6 rounded-lg hover:bg-orange-100 hover:shadow-lg transition-all duration-200 cursor-pointer transform hover:scale-105 h-40 flex flex-col"
            >
              <div className="flex items-center mb-2">
                <FileSpreadsheet className="w-6 h-6 text-green-600 mr-2" />
                <h4 className="font-semibold text-lg">XLS to PDF (Excel)</h4>
              </div>
              <p className="text-gray-600 flex-grow">Excel 파일 형식의 문서를 PDF로 변환합니다.</p>
            </div>
            <div 
              onClick={() => window.open('https://77-tools.xyz/tools/pptx-pdf', '_blank')}
              className="bg-orange-50 p-6 rounded-lg hover:bg-orange-100 hover:shadow-lg transition-all duration-200 cursor-pointer transform hover:scale-105 h-40 flex flex-col"
            >
              <div className="flex items-center mb-2">
                <Presentation className="w-6 h-6 text-orange-600 mr-2" />
                <h4 className="font-semibold text-lg">PPTX to PDF (PowerPoint)</h4>
              </div>
              <p className="text-gray-600 flex-grow">프레젠테이션을 PDF로 변환합니다.</p>
            </div>
          </div>
        </div>

        {/* 이미지&동영상변환도구 섹션 */}
        <div ref={refs?.imageConvertRef} id="image-conversion-tools" className="mb-16 scroll-mt-20">
          <h3 className="text-2xl font-bold mb-6 text-gray-800 flex items-center">
            이미지&동영상변환도구          </h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {/* JPG 변??카드 */}
            <div className="bg-yellow-50 p-6 rounded-lg hover:bg-yellow-100 hover:shadow-lg transition-all duration-200 transform hover:scale-105 h-40 flex flex-col">
              <div className="flex items-center mb-2">
                <Image className="w-6 h-6 text-yellow-600 mr-2" />
                <h4 className="font-semibold text-lg">JPG 변환</h4>
              </div>
              <p className="text-gray-600 flex-grow">다양한 이미지 형식을 JPG로 쉽게 변환합니다.</p>
            </div>

            {/* PNG 변??카드 */}
            <div 
              onClick={() => window.location.href = '/tools/png-converter'}
              className="bg-yellow-50 p-6 rounded-lg hover:bg-yellow-100 hover:shadow-lg transition-all duration-200 cursor-pointer transform hover:scale-105 h-40 flex flex-col"
            >
              <div className="flex items-center mb-2">
                <Image className="w-6 h-6 text-yellow-600 mr-2" />
                <h4 className="font-semibold text-lg">PNG 변환</h4>
              </div>
              <p className="text-gray-600 flex-grow">이미지를 PNG 형식으로 변환하여 품질을 유지합니다.</p>
            </div>

            {/* WEBP 변??카드 */}
            <div 
              onClick={() => window.location.href = '/tools/webp-converter'}
              className="bg-yellow-50 p-6 rounded-lg hover:bg-yellow-100 hover:shadow-lg transition-all duration-200 cursor-pointer transform hover:scale-105 h-40 flex flex-col"
            >
              <div className="flex items-center mb-2">
                <Image className="w-6 h-6 text-yellow-600 mr-2" />
                <h4 className="font-semibold text-lg">WEBP 변환</h4>
              </div>
              <p className="text-gray-600 flex-grow">웹 최적화에 적합한 WEBP로 이미지 파일을 변환합니다.</p>
            </div>

            {/* GIF 변??카드 */}
            <div 
              onClick={() => window.location.href = '/tools/gif-converter'}
              className="bg-yellow-50 p-6 rounded-lg hover:bg-yellow-100 hover:shadow-lg transition-all duration-200 cursor-pointer transform hover:scale-105 h-40 flex flex-col"
            >
              <div className="flex items-center mb-2">
                <Image className="w-6 h-6 text-yellow-600 mr-2" />
                <h4 className="font-semibold text-lg">GIF 변환</h4>
              </div>
              <p className="text-gray-600 flex-grow">이미지를 GIF 형식으로 변환하여 애니메이션 효과를 제공합니다.</p>
            </div>
          </div>

          {/* 이미지 변환 & 동영상 변환 통합 카드 (4번 카드박스) */}
          <div className="mt-8 grid grid-cols-1 md:grid-cols-4 gap-6">
            <div 
              onClick={() => window.location.href = '/tools/image-converter'}
              className="bg-yellow-50 p-6 rounded-lg hover:bg-yellow-100 hover:shadow-lg transition-all duration-200 cursor-pointer transform hover:scale-105 h-40 flex flex-col"
            >
              <div className="flex items-center mb-2">
                <RefreshCw className="w-6 h-6 text-yellow-600 mr-2" />
                <h4 className="font-semibold text-lg">이미지 변환</h4>
              </div>
              <p className="text-gray-600 flex-grow">다양한 이미지 형식 간 변환을 지원합니다.</p>
            </div>
            <div 
              onClick={() => window.location.href = '/tools/video-converter'}
              className="bg-yellow-50 p-6 rounded-lg hover:bg-yellow-100 hover:shadow-lg transition-all duration-200 cursor-pointer transform hover:scale-105 h-40 flex flex-col"
            >
              <div className="flex items-center mb-2">
                <Video className="w-6 h-6 text-yellow-600 mr-2" />
                <h4 className="font-semibold text-lg">동영상 변환</h4>
              </div>
              <p className="text-gray-600 flex-grow">다양한 동영상 형식 간 변환을 지원합니다.</p>
            </div>
          </div>
        </div>

        {/* 편집&최적화도구 섹션 */}
        <div ref={refs?.imageToolsRef} id="image-tools" className="mb-16 scroll-mt-20">
          <h3 className="text-2xl font-bold text-gray-900 mb-6">
            편집&최적화도구
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {/* 동영상 압축 카드 */}
            <div 
              onClick={() => window.location.href = '/tools/video-compressor'}
              className="bg-blue-50 p-6 rounded-lg hover:bg-blue-100 hover:shadow-lg transition-all duration-200 cursor-pointer transform hover:scale-105 h-40 flex flex-col"
            >
              <div className="flex items-center mb-2">
                <Minimize className="w-6 h-6 text-blue-600 mr-2" />
                <h4 className="font-semibold text-lg">동영상 압축</h4>
              </div>
              <p className="text-gray-600 flex-grow">동영상 파일 크기를 줄여 최적화합니다.</p>
            </div>

            {/* 동영상 자르기 카드 */}
            <div 
              onClick={() => window.location.href = '/tools/video-cutter'}
              className="bg-green-50 p-6 rounded-lg hover:bg-green-100 hover:shadow-lg transition-all duration-200 cursor-pointer transform hover:scale-105 h-40 flex flex-col"
            >
              <div className="flex items-center mb-2">
                <Scissors className="w-6 h-6 text-green-600 mr-2" />
                <h4 className="font-semibold text-lg">동영상 자르기</h4>
              </div>
              <p className="text-gray-600 flex-grow">원하는 길이로 동영상을 자릅니다.</p>
            </div>

            {/* 이미지 리사이저 카드 */}
            <div 
              onClick={() => window.location.href = '/tools/image-resizer'}
              className="bg-purple-50 p-6 rounded-lg hover:bg-purple-100 hover:shadow-lg transition-all duration-200 cursor-pointer transform hover:scale-105 h-40 flex flex-col"
            >
              <div className="flex items-center mb-2">
                <Expand className="w-6 h-6 text-purple-600 mr-2" />
                <h4 className="font-semibold text-lg">이미지 리사이저</h4>
              </div>
              <p className="text-gray-600 flex-grow">이미지 크기를 조정하고 최적화합니다.</p>
            </div>

            {/* 이미지 압축 카드 */}
            <div 
              onClick={() => window.location.href = '/tools/image-compressor'}
              className="bg-orange-50 p-6 rounded-lg hover:bg-orange-100 hover:shadow-lg transition-all duration-200 cursor-pointer transform hover:scale-105 h-40 flex flex-col"
            >
              <div className="flex items-center mb-2">
                <Minimize2 className="w-6 h-6 text-orange-600 mr-2" />
                <h4 className="font-semibold text-lg">이미지 압축</h4>
              </div>
              <p className="text-gray-600 flex-grow">이미지 파일 크기를 줄여 최적화합니다.</p>
            </div>
          </div>
        </div>

        {/* AI도구 섹션 */}
        <div ref={refs?.aiToolsRef} id="ai-tools" className="mb-16 scroll-mt-20">
          <h3 className="text-2xl font-bold text-gray-900 mb-6">
            AI도구
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="bg-purple-50 p-6 rounded-lg hover:bg-purple-100 hover:shadow-lg transition-all duration-200 transform hover:scale-105 h-40 flex flex-col">
              <div className="flex items-center mb-2">
                <Type className="w-6 h-6 text-purple-600 mr-2" />
                <h4 className="font-semibold text-lg">AI 텍스트 생성</h4>
              </div>
              <p className="text-gray-600 flex-grow">인공지능을 활용한 텍스트 생성 도구입니다.</p>
            </div>
            <div className="bg-purple-50 p-6 rounded-lg hover:bg-purple-100 hover:shadow-lg transition-all duration-200 transform hover:scale-105 h-40 flex flex-col">
              <div className="flex items-center mb-2">
                <Sparkles className="w-6 h-6 text-purple-600 mr-2" />
                <h4 className="font-semibold text-lg">AI 이미지 생성</h4>
              </div>
              <p className="text-gray-600 flex-grow">텍스트 설명으로 이미지를 생성합니다.</p>
            </div>
            <div className="bg-purple-50 p-6 rounded-lg hover:bg-purple-100 hover:shadow-lg transition-all duration-200 transform hover:scale-105 h-40 flex flex-col">
              <div className="flex items-center mb-2">
                <Languages className="w-6 h-6 text-purple-600 mr-2" />
                <h4 className="font-semibold text-lg">AI 번역</h4>
              </div>
              <p className="text-gray-600 flex-grow">고품질 AI 번역 서비스를 제공합니다.</p>
            </div>
            <div 
              onClick={() => window.location.href = '/tools/prompt-generator'}
              className="bg-purple-50 p-6 rounded-lg hover:bg-purple-100 hover:shadow-lg transition-all duration-200 cursor-pointer transform hover:scale-105 h-40 flex flex-col"
            >
              <div className="flex items-center mb-2">
                <Wand2 className="w-6 h-6 text-purple-600 mr-2" />
                <h4 className="font-semibold text-lg">프롬프트 생성기</h4>
              </div>
              <p className="text-gray-600 flex-grow">고품질 프롬프트 서비스를 제공합니다.</p>
            </div>
          </div>
        </div>

        {/* 문서변환도구 섹션과 이미지도구 섹션 위로 이동되었습니다 */}

        {/* YOUTUBE컨텐츠추출도구 섹션 */}
        <div ref={refs?.youtubeToolsRef} id="youtube-tools" className="mb-16 scroll-mt-20">
          <h3 className="text-2xl font-bold text-gray-900 mb-6">
            컨텐츠추출도구
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="bg-red-50 p-6 rounded-lg hover:bg-red-100 hover:shadow-lg transition-all duration-200 transform hover:scale-105 h-40 flex flex-col">
              <div className="flex items-center mb-2">
                <Subtitles className="w-6 h-6 text-red-600 mr-2" />
                <h4 className="font-semibold text-lg">자막 추출</h4>
              </div>
              <p className="text-gray-600 flex-grow">유튜브 영상의 자막을 추출합니다.</p>
            </div>
            <div className="bg-red-50 p-6 rounded-lg hover:bg-red-100 hover:shadow-lg transition-all duration-200 transform hover:scale-105 h-40 flex flex-col">
              <div className="flex items-center mb-2">
                <Youtube className="w-6 h-6 text-red-600 mr-2" />
                <h4 className="font-semibold text-lg">유튜브 썸네일 추출기</h4>
              </div>
              <p className="text-gray-600 flex-grow">유튜브 영상의 고화질 썸네일을 추출합니다.</p>
            </div>
            <div className="bg-red-50 p-6 rounded-lg hover:bg-red-100 hover:shadow-lg transition-all duration-200 transform hover:scale-105 h-40 flex flex-col">
              <div className="flex items-center mb-2">
                <ImageIcon className="w-6 h-6 text-red-600 mr-2" />
                <h4 className="font-semibold text-lg">인스타그램 썸네일 추출기</h4>
              </div>
              <p className="text-gray-600 flex-grow">인스타그램 게시물의 썸네일을 추출합니다.</p>
            </div>
            <div className="bg-red-50 p-6 rounded-lg hover:bg-red-100 hover:shadow-lg transition-all duration-200 transform hover:scale-105 h-40 flex flex-col">
              <div className="flex items-center mb-2">
                <Video className="w-6 h-6 text-red-600 mr-2" />
                <h4 className="font-semibold text-lg">틱톡 썸네일 추출기</h4>
              </div>
              <p className="text-gray-600 flex-grow">틱톡 영상의 썸네일을 추출합니다.</p>
            </div>
            <div className="bg-red-50 p-6 rounded-lg hover:bg-red-100 hover:shadow-lg transition-all duration-200 transform hover:scale-105 h-40 flex flex-col">
              <div className="flex items-center mb-2">
                <Palette className="w-6 h-6 text-red-600 mr-2" />
                <h4 className="font-semibold text-lg">썸네일 편집기</h4>
              </div>
              <p className="text-gray-600 flex-grow">썸네일 이미지를 편집하고 수정합니다.</p>
            </div>
            <div className="bg-red-50 p-6 rounded-lg hover:bg-red-100 hover:shadow-lg transition-all duration-200 transform hover:scale-105 h-40 flex flex-col">
              <div className="flex items-center mb-2">
                <Sparkles className="w-6 h-6 text-red-600 mr-2" />
                <h4 className="font-semibold text-lg">썸네일 생성기</h4>
              </div>
              <p className="text-gray-600 flex-grow">AI를 활용하여 매력적인 썸네일을 생성합니다.</p>
            </div>
          </div>
        </div>


      </div>
    </section>
  );
};

export default PopularTools;