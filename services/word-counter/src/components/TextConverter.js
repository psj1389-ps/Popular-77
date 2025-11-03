import { observer } from 'mobx-react-lite';
import { useStore } from '@/stores/StoreContext';
import { useState } from 'react';

const TextConverter = observer(() => {
  const store = useStore();
  const { textAnalyzer } = store;
  const [copied, setCopied] = useState('');

  // 영어 텍스트인지 확인하는 함수
  const isEnglishText = (text) => {
    if (!text || text.trim() === '') return false;
    // 영어 알파벳이 전체 문자의 50% 이상인 경우 영어로 판단
    const englishChars = text.match(/[a-zA-Z]/g) || [];
    const totalChars = text.replace(/\s/g, '').length;
    return totalChars > 0 && (englishChars.length / totalChars) >= 0.5;
  };

  const conversions = [
    {
      label: '대문자로 변환',
      icon: '🔤',
      convert: (text) => text.toUpperCase(),
      id: 'uppercase',
      requiresEnglish: true
    },
    {
      label: '소문자로 변환',
      icon: '🔡',
      convert: (text) => text.toLowerCase(),
      id: 'lowercase',
      requiresEnglish: true
    },
    {
      label: '각 단어 첫 글자 대문자',
      icon: '📝',
      convert: (text) => text.replace(/\b\w/g, l => l.toUpperCase()),
      id: 'title',
      requiresEnglish: true
    },
    {
      label: '공백 제거',
      icon: '🗜️',
      convert: (text) => text.replace(/\s+/g, ''),
      id: 'removeSpaces',
      requiresEnglish: false
    },
    {
      label: '여러 공백을 하나로',
      icon: '📏',
      convert: (text) => text.replace(/\s+/g, ' ').trim(),
      id: 'normalizeSpaces',
      requiresEnglish: false
    }
  ];

  const handleCopy = async (convertedText, id) => {
    try {
      await navigator.clipboard.writeText(convertedText);
      setCopied(id);
      setTimeout(() => setCopied(''), 2000);
    } catch (err) {
      console.error('복사 실패:', err);
    }
  };

  const handleApply = (convertedText) => {
    textAnalyzer.setText(convertedText);
  };

  if (!textAnalyzer.text.trim()) {
    return (
      <div className="w-full max-w-4xl mx-auto animate-fade-in">
        <div className="bg-white shadow-lg shadow-gray-400/30 rounded-xl p-8 text-left transform scale-70 origin-top-left">
          <h3 className="text-xl font-semibold text-black mb-2 flex items-center space-x-2">
            <span className="text-6xl">🔄</span>
            <span>텍스트 변환</span>
          </h3>
          <p className="text-black leading-relaxed">
            텍스트를 입력하면 대소문자 변환, 공백 제거 등 다양한 변환 기능을 사용할 수 있습니다.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full max-w-4xl mx-auto animate-fade-in">
      <div className="bg-white shadow-lg shadow-gray-400/30 rounded-xl p-8 hover:shadow-xl transition-all duration-300 transform scale-70 origin-top-left">
        <div className="mb-6 text-left">
          <h2 className="text-2xl font-bold text-black mb-2 flex items-center space-x-2">
            <span className="text-3xl">🔄</span>
            <span>텍스트 변환</span>
          </h2>
          <p className="text-black">다양한 형태로 텍스트를 변환해보세요.</p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {conversions.filter((conversion) => {
            // 영어가 필요한 변환은 영어 텍스트일 때만 표시
            if (conversion.requiresEnglish) {
              return isEnglishText(textAnalyzer.text);
            }
            return true;
          }).map((conversion) => {
            const convertedText = conversion.convert(textAnalyzer.text);
            const isCopied = copied === conversion.id;
            
            return (
              <div key={conversion.id} className="group bg-white shadow-lg shadow-gray-400/30 rounded-lg p-4 transition-all duration-300 hover:shadow-xl">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-semibold text-black flex items-center space-x-2">
                    <span className="text-lg group-hover:scale-110 transition-transform duration-200">{conversion.icon}</span>
                    <span>{conversion.label}</span>
                  </h3>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => handleCopy(convertedText, conversion.id)}
                      className={`px-3 py-1 text-xs rounded-lg transition-all duration-200 font-medium ${
                        isCopied 
                          ? 'bg-green-500 text-white' 
                          : 'bg-blue-500 hover:bg-blue-600 text-white'
                      }`}
                    >
                      {isCopied ? '✅ 복사됨!' : '📋 복사'}
                    </button>
                    <button
                      onClick={() => handleApply(convertedText)}
                      className="px-3 py-1 text-xs bg-purple-500 hover:bg-purple-600 text-white rounded-lg transition-all duration-200 font-medium"
                    >
                      ✨ 적용
                    </button>
                  </div>
                </div>
                <div className="bg-gray-50 p-3 rounded-lg text-sm text-black max-h-24 overflow-y-auto shadow-lg shadow-gray-400/30">
                  {convertedText || '(빈 텍스트)'}
                </div>
              </div>
            );
          })}
        </div>
        
        <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
          <p className="text-sm text-black flex items-center space-x-2">
            <span>💡</span>
            <span>
              <strong>변환 기능:</strong> 대소문자 변환, 공백 제거, 특수문자 제거 등 다양한 텍스트 변환을 지원합니다.
            </span>
          </p>
        </div>
      </div>
    </div>
  );
});

export default TextConverter;