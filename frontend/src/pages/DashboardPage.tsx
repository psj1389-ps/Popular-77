import React from 'react';
import { BarChart3, FileText, Clock, Users, TrendingUp, Download } from 'lucide-react';

const DashboardPage: React.FC = () => {
  // Mock data - 실제로는 Supabase에서 가져올 데이터
  const stats = {
    totalConversions: 1247,
    filesProcessed: 3456,
    activeUsers: 89,
    successRate: 98.5
  };

  const recentActivity = [
    { id: 1, type: 'PDF to JPG', filename: 'document.pdf', time: '2분 전', status: 'completed' },
    { id: 2, type: 'DOCX to PDF', filename: 'report.docx', time: '5분 전', status: 'completed' },
    { id: 3, type: 'Image Resize', filename: 'photo.jpg', time: '10분 전', status: 'processing' },
    { id: 4, type: 'PDF to DOCX', filename: 'manual.pdf', time: '15분 전', status: 'completed' }
  ];

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">대시보드</h1>
          <p className="mt-2 text-gray-600">사용 통계 및 최근 활동을 확인하세요</p>
        </div>

        {/* 통계 카드 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <BarChart3 className="h-8 w-8 text-blue-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">총 변환 수</p>
                <p className="text-2xl font-semibold text-gray-900">{stats.totalConversions.toLocaleString()}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <FileText className="h-8 w-8 text-green-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">처리된 파일</p>
                <p className="text-2xl font-semibold text-gray-900">{stats.filesProcessed.toLocaleString()}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Users className="h-8 w-8 text-purple-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">활성 사용자</p>
                <p className="text-2xl font-semibold text-gray-900">{stats.activeUsers}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <TrendingUp className="h-8 w-8 text-orange-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">성공률</p>
                <p className="text-2xl font-semibold text-gray-900">{stats.successRate}%</p>
              </div>
            </div>
          </div>
        </div>

        {/* 최근 활동 */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">최근 활동</h2>
          </div>
          <div className="divide-y divide-gray-200">
            {recentActivity.map((activity) => (
              <div key={activity.id} className="px-6 py-4 flex items-center justify-between">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <Clock className="h-5 w-5 text-gray-400" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-900">{activity.type}</p>
                    <p className="text-sm text-gray-500">{activity.filename}</p>
                  </div>
                </div>
                <div className="flex items-center">
                  <span className="text-sm text-gray-500 mr-4">{activity.time}</span>
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    activity.status === 'completed' 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-yellow-100 text-yellow-800'
                  }`}>
                    {activity.status === 'completed' ? '완료' : '처리중'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 빠른 액션 */}
        <div className="mt-8 bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">빠른 액션</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <button className="flex items-center justify-center px-4 py-3 border border-gray-300 rounded-md shadow-sm bg-white text-sm font-medium text-gray-700 hover:bg-gray-50">
              <FileText className="h-5 w-5 mr-2" />
              새 변환 시작
            </button>
            <button className="flex items-center justify-center px-4 py-3 border border-gray-300 rounded-md shadow-sm bg-white text-sm font-medium text-gray-700 hover:bg-gray-50">
              <Download className="h-5 w-5 mr-2" />
              변환 기록 다운로드
            </button>
            <button className="flex items-center justify-center px-4 py-3 border border-gray-300 rounded-md shadow-sm bg-white text-sm font-medium text-gray-700 hover:bg-gray-50">
              <BarChart3 className="h-5 w-5 mr-2" />
              상세 분석 보기
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;