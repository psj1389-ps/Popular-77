import { observer } from 'mobx-react-lite';
import { useStore } from '@/stores/StoreContext';
import StatCard from './StatCard';

const StatsDashboard = observer(() => {
  const store = useStore();
  const { textAnalyzer } = store;

  const stats = [
    {
      title: '글자 수',
      value: textAnalyzer.characterCount,
      subtitle: '공백 포함',
      icon: '📝',
      color: 'blue',
      show: textAnalyzer.showCharacterCount
    },
    {
      title: '단어 수',
      value: textAnalyzer.wordCount,
      subtitle: '단어 개수',
      icon: '📖',
      color: 'green',
      show: textAnalyzer.showWordCount
    },
    {
      title: '문장 수',
      value: textAnalyzer.sentenceCount,
      subtitle: '문장 개수',
      icon: '📄',
      color: 'purple',
      show: textAnalyzer.showSentenceCount
    },
    {
      title: '문단 수',
      value: textAnalyzer.paragraphCount,
      subtitle: '문단 개수',
      icon: '📋',
      color: 'orange',
      show: textAnalyzer.showParagraphCount
    },
    {
      title: '읽기 시간',
      value: textAnalyzer.readingTime,
      subtitle: '분 (평균)',
      icon: '⏱️',
      color: 'red',
      show: textAnalyzer.showReadingTime
    }
  ];

  const visibleStats = stats.filter(stat => stat.show);

  if (!textAnalyzer.text.trim()) {
    return (
      <div className="w-full animate-fade-in">
        <div className="bg-white shadow-lg shadow-black/30 rounded-xl p-8 lg:p-12 xl:p-16 text-left ml-8 border-l-4 border-gray-800 transform scale-70 origin-top-left">
          <h3 className="text-lg lg:text-xl font-semibold text-black mb-2 flex items-center space-x-2">
            <span className="text-5xl lg:text-6xl">📊</span>
            <span>분석 대기 중</span>
          </h3>
          <p className="text-sm lg:text-base text-black leading-relaxed">
            텍스트를 입력하면 실시간으로 분석 결과가 표시됩니다.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full">
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="text-center mb-6">
          <div className="inline-flex items-center gap-3 mb-4">
            <span className="text-4xl">📊</span>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            글자 수
          </h3>
          <p className="text-gray-600 text-sm">
            실시간 텍스트 분석 결과를 확인하세요
          </p>
        </div>

        <div className="space-y-4">
          {visibleStats.map((stat, index) => (
            <StatCard key={index} {...stat} />
          ))}
        </div>

        {textAnalyzer.text.trim() && (
          <div className="mt-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div className="text-center">
                <div className="font-semibold text-gray-900">평균 단어 길이</div>
                <div className="text-gray-600">{textAnalyzer.averageWordLength}자</div>
              </div>
              <div className="text-center">
                <div className="font-semibold text-gray-900">평균 문장 길이</div>
                <div className="text-gray-600">{textAnalyzer.averageSentenceLength}단어</div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
});

export default StatsDashboard;