import { observer } from 'mobx-react-lite';
import { useStore } from '@/stores/StoreContext';
import { useState } from 'react';

const TextCorrector = observer(() => {
  const store = useStore();
  const { textAnalyzer } = store;
  const [correctedText, setCorrectedText] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [copied, setCopied] = useState(false);

  // 기본적인 텍스트 교정 함수들
  const corrections = {
    // 띄어쓰기 교정
    fixSpacing: (text) => {
      return text
        // 문장부호 앞 공백 제거
        .replace(/\s+([,.!?;:])/g, '$1')
        // 문장부호 뒤 공백 추가 (이미 있으면 하나로 정리)
        .replace(/([,.!?;:])(?!\s|$)/g, '$1 ')
        // 여러 공백을 하나로
        .replace(/\s+/g, ' ')
        // 괄호 안팎 공백 정리
        .replace(/\(\s+/g, '(')
        .replace(/\s+\)/g, ')')
        .replace(/\[\s+/g, '[')
        .replace(/\s+\]/g, ']')
        // 따옴표 안팎 공백 정리
        .replace(/"\s+/g, '"')
        .replace(/\s+"/g, '"')
        .replace(/'\s+/g, "'")
        .replace(/\s+'/g, "'")
        .trim();
    },

    // 기본적인 오타 교정
    fixTypos: (text) => {
      const typoMap = {
        // 자주 발생하는 한글 오타
        '됬다': '됐다',
        '되다': '된다',
        '안됬다': '안됐다',
        '했다': '했다',
        '갔다': '갔다',
        '왔다': '왔다',
        '봤다': '봤다',
        '했었다': '했었다',
        '갔었다': '갔었다',
        '왔었다': '왔었다',
        '봤었다': '봤었다',
        // 영어 오타
        'teh': 'the',
        'adn': 'and',
        'taht': 'that',
        'thier': 'their',
        'recieve': 'receive',
        'seperate': 'separate',
        'definately': 'definitely',
        'occured': 'occurred',
        'begining': 'beginning',
        'accomodate': 'accommodate',
        // 숫자와 단위 사이 공백
        '(\\d+)(kg|g|cm|mm|km|m)': '$1 $2',
        '(\\d+)(원|달러|엔)': '$1$2'
      };

      let corrected = text;
      Object.entries(typoMap).forEach(([wrong, right]) => {
        const regex = new RegExp(wrong, 'gi');
        corrected = corrected.replace(regex, right);
      });
      return corrected;
    },

    // 문장 구조 교정
    fixSentenceStructure: (text) => {
      return text
        // 문장 시작 대문자 (영어)
        .replace(/(^|[.!?]\s+)([a-z])/g, (match, p1, p2) => p1 + p2.toUpperCase())
        // 연속된 문장부호 정리
        .replace(/[.]{2,}/g, '...')
        .replace(/[!]{2,}/g, '!!')
        .replace(/[?]{2,}/g, '??')
        // 문장 끝 공백 정리
        .replace(/\s+([.!?])\s*$/gm, '$1')
        // 줄바꿈 정리
        .replace(/\n{3,}/g, '\n\n')
        .trim();
    }
  };

  const performCorrection = () => {
    if (!textAnalyzer.text.trim()) {
      alert('교정할 텍스트를 입력해주세요.');
      return;
    }

    setIsProcessing(true);
    
    // 단계별 교정 적용
    let result = textAnalyzer.text;
    result = corrections.fixSpacing(result);
    result = corrections.fixTypos(result);
    result = corrections.fixSentenceStructure(result);
    
    setTimeout(() => {
      setCorrectedText(result);
      setIsProcessing(false);
    }, 500); // 처리 중 효과를 위한 지연
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(correctedText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('복사 실패:', err);
    }
  };

  const handleApply = () => {
    textAnalyzer.setText(correctedText);
    setCorrectedText('');
  };

  const getDifferences = () => {
    if (!correctedText || !textAnalyzer.text) return [];
    
    const original = textAnalyzer.text.split(' ');
    const corrected = correctedText.split(' ');
    const differences = [];
    
    // 간단한 차이점 감지
    const maxLength = Math.max(original.length, corrected.length);
    for (let i = 0; i < maxLength; i++) {
      if (original[i] !== corrected[i]) {
        differences.push({
          original: original[i] || '',
          corrected: corrected[i] || '',
          index: i
        });
      }
    }
    
    return differences.slice(0, 10); // 최대 10개까지만 표시
  };

  if (!textAnalyzer.text.trim()) {
    return (
      <div className="w-full max-w-4xl mx-auto animate-fade-in">
        <div className="bg-white shadow-lg shadow-gray-400/30 rounded-xl p-8 text-left transform scale-70 origin-top-left">
          <h3 className="text-xl font-semibold text-black mb-2 flex items-center space-x-2">
            <span className="text-6xl">✏️</span>
            <span>텍스트 교정</span>
          </h3>
          <p className="text-black leading-relaxed">
            텍스트를 입력하면 띄어쓰기, 오타, 문장 구조를 자동으로 교정해드립니다.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full max-w-4xl mx-auto animate-fade-in">
      <div className="bg-white shadow-lg shadow-gray-400/30 rounded-xl p-8 transform scale-70 origin-top-left">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-black mb-2 flex items-center space-x-2">
              <span className="text-3xl">✏️</span>
              <span>텍스트 교정</span>
            </h2>
            <p className="text-black">AI가 띄어쓰기, 오타, 문장 구조를 자동으로 교정합니다.</p>
          </div>
          <button
            onClick={performCorrection}
            disabled={isProcessing}
            className="bg-blue-500 hover:bg-blue-600 disabled:bg-gray-400 text-white px-6 py-3 rounded-lg transition-all duration-200 flex items-center space-x-2 font-medium shadow-sm hover:shadow-md disabled:shadow-none"
          >
            {isProcessing ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent"></div>
                <span>교정 중...</span>
              </>
            ) : (
              <>
                <span className="text-lg">🔧</span>
                <span>교정 시작</span>
              </>
            )}
          </button>
        </div>

        {correctedText && (
          <div className="space-y-6 animate-scale-in">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-7">
              <div>
                <h3 className="text-sm font-semibold text-black mb-3 flex items-center space-x-2">
                  <span>📝</span>
                  <span>원본 텍스트</span>
                </h3>
                <div className="bg-red-50 border-2 border-red-200 rounded-lg p-4 max-h-48 overflow-y-auto text-sm leading-relaxed text-black">
                  {textAnalyzer.text}
                </div>
              </div>
              <div>
                <h3 className="text-sm font-semibold text-black mb-3 flex items-center space-x-2">
                  <span>✨</span>
                  <span>교정된 텍스트</span>
                </h3>
                <div className="bg-green-50 border-2 border-green-200 rounded-lg p-4 max-h-48 overflow-y-auto text-sm leading-relaxed text-black">
                  {correctedText}
                </div>
              </div>
            </div>

            <div className="flex justify-center space-x-4">
              <button
                onClick={handleCopy}
                className={`px-6 py-3 rounded-lg transition-all duration-200 flex items-center space-x-2 font-medium ${
                   copied 
                     ? 'bg-green-500 text-white shadow-lg shadow-green-400/30' 
                     : 'bg-gray-100 hover:bg-gray-200 text-black shadow-lg shadow-gray-400/30'
                 }`}
              >
                <span className="text-lg">{copied ? '✅' : '📋'}</span>
                <span>{copied ? '복사됨!' : '복사하기'}</span>
              </button>
              <button
                onClick={handleApply}
                className="bg-blue-500 hover:bg-blue-600 text-white px-6 py-3 rounded-lg transition-all duration-200 flex items-center space-x-2 font-medium border-2 border-blue-200 hover:border-blue-300"
              >
                <span className="text-lg">✨</span>
                <span>교정된 텍스트 적용</span>
              </button>
            </div>

            {getDifferences().length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-black mb-3 flex items-center space-x-2">
                  <span>🔍</span>
                  <span>주요 변경사항</span>
                </h3>
                <div className="bg-yellow-50 border-2 border-yellow-200 rounded-lg p-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                    {getDifferences().map((diff, index) => (
                      <div key={index} className="flex items-center space-x-3 p-2 bg-white bg-opacity-50 rounded-lg">
                        <span className="text-red-600 line-through font-medium">{diff.original}</span>
                        <span className="text-gray-400">→</span>
                        <span className="text-green-600 font-semibold">{diff.corrected}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
        </div>
      )}

        <div className="mt-6 p-4 bg-indigo-50 rounded-lg border border-indigo-200">
          <p className="text-sm text-black flex items-center space-x-2">
            <span>💡</span>
            <span>
              <strong>교정 기능:</strong> 띄어쓰기 정리, 자주 발생하는 오타 수정, 문장부호 정리, 문장 구조 개선을 자동으로 수행합니다.
            </span>
          </p>
        </div>
      </div>
    </div>
  );
});

export default TextCorrector;