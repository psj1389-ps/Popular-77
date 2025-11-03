import { observer } from 'mobx-react-lite';
import { useStore } from '@/stores/StoreContext';
import { useState } from 'react';

const SettingsPanel = observer(() => {
  const store = useStore();
  const { textAnalyzer } = store;
  const [isOpen, setIsOpen] = useState(false);

  const settings = [
    {
      label: '글자 수',
      checked: textAnalyzer.showCharacterCount,
      toggle: () => textAnalyzer.toggleCharacterCount()
    },
    {
      label: '단어 수',
      checked: textAnalyzer.showWordCount,
      toggle: () => textAnalyzer.toggleWordCount()
    },
    {
      label: '문장 수',
      checked: textAnalyzer.showSentenceCount,
      toggle: () => textAnalyzer.toggleSentenceCount()
    },
    {
      label: '문단 수',
      checked: textAnalyzer.showParagraphCount,
      toggle: () => textAnalyzer.toggleParagraphCount()
    },
    {
      label: '읽기 시간',
      checked: textAnalyzer.showReadingTime,
      toggle: () => textAnalyzer.toggleReadingTime()
    }
  ];

  return (
    <div className="w-full max-w-4xl mx-auto animate-fade-in">
      <div className="bg-white rounded-xl p-8 shadow-lg shadow-gray-400/30">
        <div className="mb-8 text-left">
          <h2 className="text-2xl font-bold text-black mb-4 flex items-center space-x-3">
            <span className="text-3xl">⚙️</span>
            <span>표시 설정</span>
          </h2>
          <p className="text-black leading-relaxed">원하는 통계 항목만 선택하여 표시할 수 있습니다.</p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-7">
          {settings.map((setting, index) => {
            const colors = ['blue', 'green', 'purple', 'orange', 'indigo'];
            const icons = ['📝', '📖', '📄', '📋', '⏱️'];
            const color = colors[index % colors.length];
            const icon = icons[index % icons.length];
            
            return (
              <label key={index} className={`flex items-center space-x-4 cursor-pointer p-6 rounded-lg shadow-lg shadow-gray-400/30 transition-all duration-200 bg-white hover:bg-gray-50`}>
                <input
                  type="checkbox"
                  checked={setting.checked}
                  onChange={setting.toggle}
                  className={`w-5 h-5 rounded border-gray-400 text-${color}-600 focus:ring-${color}-400 focus:ring-2 bg-white`}
                />
                <div className="flex items-center space-x-3">
                  <span className="text-base font-medium text-black">{icon}</span>
                  <span className="text-base font-medium text-black">{setting.label}</span>
                </div>
              </label>
            );
          })}
        </div>
        
        <div className="mt-8 p-6 bg-blue-50 rounded-lg border border-blue-200 transform scale-70 origin-top-left">
          <p className="text-base text-black flex items-center space-x-3 leading-relaxed">
            <span className="text-lg">💡</span>
            <span>
              <strong>팁:</strong> 필요한 통계만 선택하여 깔끔한 화면을 유지하세요. 실시간으로 변경사항이 반영됩니다.
            </span>
          </p>
        </div>
      </div>
    </div>
  );
});

export default SettingsPanel;