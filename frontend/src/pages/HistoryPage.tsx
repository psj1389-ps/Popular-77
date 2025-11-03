import React, { useState } from 'react';
import { History, Download, Search, Filter, Calendar, FileText, Image, Video } from 'lucide-react';

const HistoryPage: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');

  // Mock data - 실제로는 Supabase에서 가져올 데이터
  const conversionHistory = [
    {
      id: 1,
      originalFilename: 'presentation.pptx',
      convertedFilename: 'presentation.pdf',
      conversionType: 'PPTX to PDF',
      fileSize: '2.4 MB',
      status: 'completed',
      createdAt: '2024-01-15 14:30:00',
      downloadUrl: '#'
    },
    {
      id: 2,
      originalFilename: 'document.docx',
      convertedFilename: 'document.pdf',
      conversionType: 'DOCX to PDF',
      fileSize: '1.8 MB',
      status: 'completed',
      createdAt: '2024-01-15 13:45:00',
      downloadUrl: '#'
    },
    {
      id: 3,
      originalFilename: 'image.png',
      convertedFilename: 'image.jpg',
      conversionType: 'PNG to JPG',
      fileSize: '856 KB',
      status: 'completed',
      createdAt: '2024-01-15 12:20:00',
      downloadUrl: '#'
    },
    {
      id: 4,
      originalFilename: 'report.pdf',
      convertedFilename: 'report.docx',
      conversionType: 'PDF to DOCX',
      fileSize: '3.2 MB',
      status: 'failed',
      createdAt: '2024-01-15 11:15:00',
      downloadUrl: null
    },
    {
      id: 5,
      originalFilename: 'video.mp4',
      convertedFilename: 'video.avi',
      conversionType: 'MP4 to AVI',
      fileSize: '45.6 MB',
      status: 'processing',
      createdAt: '2024-01-15 10:30:00',
      downloadUrl: null
    }
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'processing':
        return 'bg-yellow-100 text-yellow-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed':
        return '완료';
      case 'processing':
        return '처리중';
      case 'failed':
        return '실패';
      default:
        return '알 수 없음';
    }
  };

  const getFileIcon = (conversionType: string) => {
    if (conversionType.includes('PDF')) return <FileText className="h-5 w-5" />;
    if (conversionType.includes('JPG') || conversionType.includes('PNG')) return <Image className="h-5 w-5" />;
    if (conversionType.includes('MP4') || conversionType.includes('AVI')) return <Video className="h-5 w-5" />;
    return <FileText className="h-5 w-5" />;
  };

  const filteredHistory = conversionHistory.filter(item => {
    const matchesSearch = item.originalFilename.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         item.conversionType.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = filterType === 'all' || item.status === filterType;
    return matchesSearch && matchesFilter;
  });

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">변환 기록</h1>
          <p className="mt-2 text-gray-600">파일 변환 기록을 확인하고 다운로드하세요</p>
        </div>

        {/* 검색 및 필터 */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="파일명 또는 변환 유형으로 검색..."
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>
            </div>
            <div className="sm:w-48">
              <select
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
              >
                <option value="all">모든 상태</option>
                <option value="completed">완료</option>
                <option value="processing">처리중</option>
                <option value="failed">실패</option>
              </select>
            </div>
          </div>
        </div>

        {/* 변환 기록 테이블 */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">변환 기록 ({filteredHistory.length}개)</h2>
          </div>
          
          {filteredHistory.length === 0 ? (
            <div className="text-center py-12">
              <History className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">변환 기록이 없습니다</h3>
              <p className="mt-1 text-sm text-gray-500">파일을 변환하면 여기에 기록이 표시됩니다.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      파일
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      변환 유형
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      크기
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      상태
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      생성일
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      액션
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredHistory.map((item) => (
                    <tr key={item.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="flex-shrink-0 text-gray-400">
                            {getFileIcon(item.conversionType)}
                          </div>
                          <div className="ml-4">
                            <div className="text-sm font-medium text-gray-900">{item.originalFilename}</div>
                            <div className="text-sm text-gray-500">→ {item.convertedFilename}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{item.conversionType}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{item.fileSize}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(item.status)}`}>
                          {getStatusText(item.status)}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {new Date(item.createdAt).toLocaleDateString('ko-KR')}
                        </div>
                        <div className="text-sm text-gray-500">
                          {new Date(item.createdAt).toLocaleTimeString('ko-KR')}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        {item.status === 'completed' && item.downloadUrl ? (
                          <button className="text-blue-600 hover:text-blue-900 flex items-center">
                            <Download className="h-4 w-4 mr-1" />
                            다운로드
                          </button>
                        ) : (
                          <span className="text-gray-400">-</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* 페이지네이션 (추후 구현) */}
        <div className="mt-6 flex justify-center">
          <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
            <button className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50">
              이전
            </button>
            <button className="relative inline-flex items-center px-4 py-2 border border-gray-300 bg-white text-sm font-medium text-gray-700 hover:bg-gray-50">
              1
            </button>
            <button className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50">
              다음
            </button>
          </nav>
        </div>
      </div>
    </div>
  );
};

export default HistoryPage;