import { observer } from 'mobx-react-lite';
import { useStore } from '@/stores/StoreContext';
import { useRef } from 'react';

const FileOperations = observer(() => {
  const store = useStore();
  const { textAnalyzer } = store;
  const fileInputRef = useRef(null);

  const handleFileImport = (event) => {
    const file = event.target.files[0];
    if (file && file.type === 'text/plain') {
      const reader = new FileReader();
      reader.onload = (e) => {
        textAnalyzer.setText(e.target.result);
      };
      reader.readAsText(file, 'UTF-8');
    } else {
      alert('텍스트 파일(.txt)만 지원됩니다.');
    }
    // Reset input
    event.target.value = '';
  };

  const handleFileExport = () => {
    if (!textAnalyzer.text.trim()) {
      alert('내보낼 텍스트가 없습니다.');
      return;
    }

    const blob = new Blob([textAnalyzer.text], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `text-analysis-${new Date().toISOString().slice(0, 10)}.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleStatsExport = () => {
    if (!textAnalyzer.text.trim()) {
      alert('분석할 텍스트가 없습니다.');
      return;
    }

    const stats = {
      '분석 일시': new Date().toLocaleString('ko-KR'),
      '글자 수 (공백 포함)': textAnalyzer.characterCount,
      '글자 수 (공백 제외)': textAnalyzer.characterCountNoSpaces,
      '단어 수': textAnalyzer.wordCount,
      '문장 수': textAnalyzer.sentenceCount,
      '문단 수': textAnalyzer.paragraphCount,
      '예상 읽기 시간': `${textAnalyzer.readingTime}분`,
      '평균 단어/문장': textAnalyzer.averageWordsPerSentence,
      '원본 텍스트': textAnalyzer.text
    };

    const statsText = Object.entries(stats)
      .map(([key, value]) => `${key}: ${value}`)
      .join('\n');

    const blob = new Blob([statsText], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `text-stats-${new Date().toISOString().slice(0, 10)}.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="w-full max-w-4xl mx-auto animate-fade-in">
      <div className="bg-white shadow-lg shadow-gray-400/30 rounded-xl p-8 transform scale-70 origin-top-left">
        <div className="mb-6 text-left">
          <h2 className="text-2xl font-bold text-black mb-2 flex items-center space-x-2">
            <span className="text-3xl">📁</span>
            <span>파일 작업</span>
          </h2>
          <p className="text-black">텍스트 파일을 가져오거나 분석 결과를 내보낼 수 있습니다.</p>
        </div>
      
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-7">
          <div className="p-6 rounded-lg shadow-lg shadow-gray-400/30 transition-all duration-200 bg-white hover:bg-gray-50">
            <label className="block text-base font-semibold text-black flex items-center space-x-2 mb-3">
              <span>📤</span>
              <span className="text-base font-medium text-black">텍스트 파일 가져오기</span>
            </label>
            <input
              ref={fileInputRef}
              type="file"
              accept=".txt"
              onChange={handleFileImport}
              className="block w-full text-base text-black file:mr-4 file:py-3 file:px-4 file:rounded-lg file:border-0 file:text-base file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 file:transition-all file:duration-200 file:shadow-sm hover:file:shadow-md mb-3"
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              className="w-full flex items-center justify-center space-x-2 cursor-pointer p-10 rounded-lg shadow-lg shadow-gray-400/30 transition-all duration-200 bg-white hover:bg-gray-50 font-medium text-black"
            >
              <span className="text-lg">📁</span>
              <span className="text-base font-medium text-black">텍스트 파일 열기</span>
            </button>
          </div>

          <div className="p-6 rounded-lg shadow-lg shadow-gray-400/30 transition-all duration-200 bg-white hover:bg-gray-50">
            <label className="block text-base font-semibold text-black flex items-center space-x-2 mb-3">
              <span>💾</span>
              <span className="text-base font-medium text-black">현재 텍스트 내보내기</span>
            </label>
            <button
              onClick={handleFileExport}
              disabled={!textAnalyzer.text.trim()}
              className="w-full flex items-center justify-center space-x-2 cursor-pointer p-10 rounded-lg shadow-lg shadow-gray-400/30 transition-all duration-200 bg-white hover:bg-gray-50 font-medium text-black disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <span className="text-lg">💾</span>
              <span className="text-base font-medium text-black">텍스트 저장</span>
            </button>
          </div>

          <div className="p-6 rounded-lg shadow-lg shadow-gray-400/30 transition-all duration-200 bg-white hover:bg-gray-50">
            <label className="block text-base font-semibold text-black flex items-center space-x-2 mb-3">
              <span>📊</span>
              <span className="text-base font-medium text-black">분석 결과 내보내기</span>
            </label>
            <button
              onClick={handleStatsExport}
              disabled={!textAnalyzer.text.trim()}
              className="w-full flex items-center justify-center space-x-2 cursor-pointer p-10 rounded-lg shadow-lg shadow-gray-400/30 transition-all duration-200 bg-white hover:bg-gray-50 font-medium text-black disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <span className="text-lg">📊</span>
              <span className="text-base font-medium text-black">분석 결과 저장</span>
            </button>
          </div>
        </div>

        <div className="mt-6 p-4 bg-gray-50 rounded-lg shadow-lg shadow-gray-400/30">
          <p className="text-sm text-black flex items-center space-x-2">
            <span>💡</span>
            <span>
              <strong>팁:</strong> 텍스트 파일(.txt)을 가져와서 분석하거나, 분석 결과를 파일로 저장할 수 있습니다.
            </span>
          </p>
        </div>
      </div>
    </div>
  );
});

export default FileOperations;