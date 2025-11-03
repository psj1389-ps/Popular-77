const Footer = () => {
  return (
    <footer className="main-footer relative overflow-hidden mt-16">
      {/* Rainbow Border Animation */}
      <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 via-red-500 via-yellow-500 via-green-500 to-purple-500 bg-[length:300%_100%] animate-rainbow"></div>
      
      <div className="footer-content max-w-6xl mx-auto px-4 sm:px-6 py-12 sm:py-16">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {/* 서비스 섹션 */}
          <div className="footer-section">
            <h3 className="text-white text-lg font-semibold mb-4 relative">
              서비스
              <div className="absolute bottom-0 left-0 w-8 h-0.5 bg-white mt-1"></div>
            </h3>
            <ul className="space-y-2">
              <li><a href="#" className="text-white hover:text-gray-200 transition-colors duration-300">글자수 계산</a></li>
              <li><a href="#" className="text-white hover:text-gray-200 transition-colors duration-300">텍스트 변환</a></li>
              <li><a href="#" className="text-white hover:text-gray-200 transition-colors duration-300">텍스트 교정</a></li>
              <li><a href="#" className="text-white hover:text-gray-200 transition-colors duration-300">파일 처리</a></li>
            </ul>
          </div>
          
          {/* 지원 섹션 */}
          <div className="footer-section">
            <h3 className="text-white text-lg font-semibold mb-4 relative">
              지원
              <div className="absolute bottom-0 left-0 w-8 h-0.5 bg-white mt-1"></div>
            </h3>
            <ul className="space-y-2">
              <li><a href="#" className="text-white hover:text-gray-200 transition-colors duration-300">도움말</a></li>
              <li><a href="#" className="text-white hover:text-gray-200 transition-colors duration-300">문의하기</a></li>
              <li><a href="#" className="text-white hover:text-gray-200 transition-colors duration-300">FAQ</a></li>
              <li><a href="#" className="text-white hover:text-gray-200 transition-colors duration-300">기술 지원</a></li>
            </ul>
          </div>
          
          {/* 주요 기능 섹션 */}
          <div className="footer-section">
            <h3 className="text-white text-lg font-semibold mb-4 relative">
              주요 기능
              <div className="absolute bottom-0 left-0 w-8 h-0.5 bg-white mt-1"></div>
            </h3>
            <div className="footer-features flex flex-wrap gap-2">
              <span className="feature-tag bg-white bg-opacity-20 text-white px-3 py-1 rounded-full text-sm border border-white border-opacity-30">실시간 분석</span>
              <span className="feature-tag bg-white bg-opacity-20 text-white px-3 py-1 rounded-full text-sm border border-white border-opacity-30">한글 최적화</span>
              <span className="feature-tag bg-white bg-opacity-20 text-white px-3 py-1 rounded-full text-sm border border-white border-opacity-30">빠른 처리</span>
              <span className="feature-tag bg-white bg-opacity-20 text-white px-3 py-1 rounded-full text-sm border border-white border-opacity-30">고품질 변환</span>
              <span className="feature-tag bg-white bg-opacity-20 text-white px-3 py-1 rounded-full text-sm border border-white border-opacity-30">배치 처리</span>
              <span className="feature-tag bg-white bg-opacity-20 text-white px-3 py-1 rounded-full text-sm border border-white border-opacity-30">무료 사용</span>
            </div>
          </div>
          
          {/* 연락처 섹션 */}
          <div>
            <h3 className="text-white text-lg font-semibold mb-4">
              연락처
            </h3>
            <div className="space-y-2 text-gray-300">
              <p>📧 support@wordcounter.com</p>
              <p>📞 02-1234-5678</p>
              <p>🏢 서울시 강남구 테헤란로 123</p>
            </div>
          </div>
        </div>
        
        <div className="border-t border-gray-700 mt-8 pt-8 text-center">
          <p className="text-gray-400">
            © 2024 Word Counter. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;