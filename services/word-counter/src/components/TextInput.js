import { observer } from 'mobx-react-lite';
import { useStore } from '@/stores/StoreContext';
import { useRef, useEffect } from 'react';

const TextInput = observer(() => {
  const store = useStore();
  const { textAnalyzer } = store;
  const textareaRef = useRef(null);

  const handleClear = () => {
    textAnalyzer.clearText();
  };

  // 자동 높이 조절 함수
  const adjustTextareaHeight = () => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = '300px'; // 기본 높이로 리셋
      const scrollHeight = textarea.scrollHeight;
      const minHeight = 300; // 최소 높이 300px (50% 감소)
      const maxHeight = 800; // 최대 높이 제한
      
      if (scrollHeight > minHeight) {
        textarea.style.height = Math.min(scrollHeight, maxHeight) + 'px';
      }
    }
  };

  // 텍스트 변경 시 높이 조절
  useEffect(() => {
    adjustTextareaHeight();
  }, [textAnalyzer.text]);

  const handleTextChange = (e) => {
    textAnalyzer.setText(e.target.value);
  };

  return (
    <div className="w-full">
      <div className="bg-white rounded-lg shadow-lg shadow-gray-400/30 p-8">
        {/* 텍스트 입력 영역 제목 */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-4 mb-5">
            <span className="text-5xl">📝</span>
          </div>
          <h3 className="text-2xl font-semibold text-gray-900 mb-3">
            텍스트 파일을 업로드하세요
          </h3>
          <p className="text-gray-600 text-lg">
            파일을 드래그하거나 클릭하여 선택하세요 (최대 {textAnalyzer.characterLimit}자 파일, 총 5000MB)
          </p>
        </div>

        {/* 1줄 2칸 레이아웃 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-6">
          {/* 텍스트 입력 영역 */}
          <div className="relative">
            <textarea
              ref={textareaRef}
              value={textAnalyzer.text}
              onChange={handleTextChange}
              placeholder="여기에 텍스트를 입력하세요..."
              className="w-full h-[300px] p-5 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-purple-500 text-gray-900 placeholder-gray-400 text-xl shadow-lg shadow-gray-400/20 hover:shadow-xl transition-all duration-300"
              style={{
                lineHeight: '1.7'
              }}
            />
            {textAnalyzer.text.length > 0 && (
              <div className={`absolute bottom-3 right-3 px-4 py-2 rounded-full text-base font-medium shadow-lg ${
                textAnalyzer.text.length >= textAnalyzer.characterLimit 
                  ? 'bg-red-500 text-white' 
                  : 'bg-purple-500 text-white'
              }`}>
                {textAnalyzer.text.length} / {textAnalyzer.characterLimit}
              </div>
            )}
          </div>

          {/* 컨트롤 및 안내 영역 */}
          <div className="bg-gray-50 rounded-lg shadow-lg shadow-gray-400/20 p-6">
            <h4 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-3">
              <span className="text-2xl">⚙️</span>
              <span>설정 및 컨트롤</span>
            </h4>
            
            {/* 컨트롤 버튼들 */}
            <div className="flex flex-col gap-4 mb-6">
              <div className="relative group">
                <button className="w-full px-5 py-3 bg-white hover:bg-gray-50 text-gray-700 rounded-lg transition-all duration-200 flex items-center justify-center space-x-3 text-xl shadow-lg shadow-gray-400/20 hover:shadow-xl">
                  <span>📝</span>
                  <span>{textAnalyzer.characterLimit}자</span>
                  <span>▼</span>
                </button>
                <div className="absolute top-full left-0 mt-2 w-full bg-white rounded-lg shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-10">
                  <button
                    onClick={() => textAnalyzer.setCharacterLimit(5000)}
                    className="w-full px-5 py-3 text-left hover:bg-gray-50 text-xl first:rounded-t-lg"
                  >
                    5000자
                  </button>
                  <button
                    onClick={() => textAnalyzer.setCharacterLimit(10000)}
                    className="w-full px-5 py-3 text-left hover:bg-gray-50 text-xl last:rounded-b-lg"
                  >
                    10000자
                  </button>
                </div>
              </div>
              
              <button
                onClick={handleClear}
                disabled={!textAnalyzer.text.trim()}
                className="w-full px-5 py-3 bg-red-500 hover:bg-red-600 disabled:bg-gray-300 text-white rounded-lg transition-all duration-200 flex items-center justify-center space-x-3 text-xl shadow-lg shadow-gray-400/20 hover:shadow-xl"
              >
                <span>🗑️</span>
                <span>지우기</span>
              </button>
            </div>

            {textAnalyzer.text.trim() && (
              <div className="p-4 bg-purple-50 rounded-lg shadow-lg shadow-gray-400/20">
                <p className="text-lg text-purple-700 flex items-center space-x-3">
                  <span>💡</span>
                  <span>아래에서 텍스트 분석 결과, 변환 옵션, 교정 기능을 확인하세요!</span>
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
});

export default TextInput;