const Header = () => {
  return (
    <header className="bg-gradient-to-r from-purple-500 to-indigo-600 text-white py-8">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 text-center">
        <div className="flex items-center justify-center gap-3 mb-2">
          <span className="text-3xl">📝</span>
          <h1 className="text-2xl sm:text-3xl font-bold">
            Word Counter - 글자수 세기
          </h1>
        </div>
        <p className="text-sm sm:text-base text-white/90">
          텍스트를 입력하여 글자수, 단어수, 문장수를 실시간으로 분석하고 다양한 형식으로 변환하세요.
        </p>
      </div>
    </header>
  );
};

export default Header;