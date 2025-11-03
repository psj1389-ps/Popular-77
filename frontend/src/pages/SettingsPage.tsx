import React, { useState } from 'react';
import { Settings, User, Bell, Shield, Palette, Globe, Save, Check } from 'lucide-react';

const SettingsPage: React.FC = () => {
  const [settings, setSettings] = useState({
    // 프로필 설정
    displayName: '사용자',
    email: 'user@example.com',
    
    // 알림 설정
    emailNotifications: true,
    pushNotifications: false,
    conversionComplete: true,
    weeklyReport: false,
    
    // 개인화 설정
    theme: 'light',
    language: 'ko',
    timezone: 'Asia/Seoul',
    
    // 파일 설정
    defaultQuality: 'high',
    autoDownload: false,
    keepOriginal: true,
    maxFileSize: '50'
  });

  const [saved, setSaved] = useState(false);

  const handleSettingChange = (key: string, value: any) => {
    setSettings(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const handleSave = () => {
    // 실제로는 Supabase에 저장
    console.log('Settings saved:', settings);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">설정</h1>
          <p className="mt-2 text-gray-600">개인 설정을 관리하고 사용자 경험을 개선하세요</p>
        </div>

        <div className="space-y-6">
          {/* 프로필 설정 */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <div className="flex items-center">
                <User className="h-5 w-5 text-gray-400 mr-2" />
                <h2 className="text-lg font-medium text-gray-900">프로필 설정</h2>
              </div>
            </div>
            <div className="px-6 py-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  표시 이름
                </label>
                <input
                  type="text"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  value={settings.displayName}
                  onChange={(e) => handleSettingChange('displayName', e.target.value)}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  이메일 주소
                </label>
                <input
                  type="email"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  value={settings.email}
                  onChange={(e) => handleSettingChange('email', e.target.value)}
                />
              </div>
            </div>
          </div>

          {/* 알림 설정 */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <div className="flex items-center">
                <Bell className="h-5 w-5 text-gray-400 mr-2" />
                <h2 className="text-lg font-medium text-gray-900">알림 설정</h2>
              </div>
            </div>
            <div className="px-6 py-4 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-medium text-gray-900">이메일 알림</h3>
                  <p className="text-sm text-gray-500">중요한 업데이트를 이메일로 받습니다</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    className="sr-only peer"
                    checked={settings.emailNotifications}
                    onChange={(e) => handleSettingChange('emailNotifications', e.target.checked)}
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                </label>
              </div>
              
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-medium text-gray-900">푸시 알림</h3>
                  <p className="text-sm text-gray-500">브라우저 푸시 알림을 받습니다</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    className="sr-only peer"
                    checked={settings.pushNotifications}
                    onChange={(e) => handleSettingChange('pushNotifications', e.target.checked)}
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                </label>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-medium text-gray-900">변환 완료 알림</h3>
                  <p className="text-sm text-gray-500">파일 변환이 완료되면 알림을 받습니다</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    className="sr-only peer"
                    checked={settings.conversionComplete}
                    onChange={(e) => handleSettingChange('conversionComplete', e.target.checked)}
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                </label>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-medium text-gray-900">주간 리포트</h3>
                  <p className="text-sm text-gray-500">주간 사용 통계를 받습니다</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    className="sr-only peer"
                    checked={settings.weeklyReport}
                    onChange={(e) => handleSettingChange('weeklyReport', e.target.checked)}
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                </label>
              </div>
            </div>
          </div>

          {/* 개인화 설정 */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <div className="flex items-center">
                <Palette className="h-5 w-5 text-gray-400 mr-2" />
                <h2 className="text-lg font-medium text-gray-900">개인화 설정</h2>
              </div>
            </div>
            <div className="px-6 py-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  테마
                </label>
                <select
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  value={settings.theme}
                  onChange={(e) => handleSettingChange('theme', e.target.value)}
                >
                  <option value="light">라이트 모드</option>
                  <option value="dark">다크 모드</option>
                  <option value="auto">시스템 설정 따름</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  언어
                </label>
                <select
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  value={settings.language}
                  onChange={(e) => handleSettingChange('language', e.target.value)}
                >
                  <option value="ko">한국어</option>
                  <option value="en">English</option>
                  <option value="ja">日本語</option>
                  <option value="zh">中文</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  시간대
                </label>
                <select
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  value={settings.timezone}
                  onChange={(e) => handleSettingChange('timezone', e.target.value)}
                >
                  <option value="Asia/Seoul">서울 (UTC+9)</option>
                  <option value="America/New_York">뉴욕 (UTC-5)</option>
                  <option value="Europe/London">런던 (UTC+0)</option>
                  <option value="Asia/Tokyo">도쿄 (UTC+9)</option>
                </select>
              </div>
            </div>
          </div>

          {/* 파일 설정 */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <div className="flex items-center">
                <Settings className="h-5 w-5 text-gray-400 mr-2" />
                <h2 className="text-lg font-medium text-gray-900">파일 설정</h2>
              </div>
            </div>
            <div className="px-6 py-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  기본 품질
                </label>
                <select
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  value={settings.defaultQuality}
                  onChange={(e) => handleSettingChange('defaultQuality', e.target.value)}
                >
                  <option value="low">낮음 (빠른 처리)</option>
                  <option value="medium">보통 (균형)</option>
                  <option value="high">높음 (최고 품질)</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  최대 파일 크기 (MB)
                </label>
                <input
                  type="number"
                  min="1"
                  max="100"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  value={settings.maxFileSize}
                  onChange={(e) => handleSettingChange('maxFileSize', e.target.value)}
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-medium text-gray-900">자동 다운로드</h3>
                  <p className="text-sm text-gray-500">변환 완료 후 자동으로 파일을 다운로드합니다</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    className="sr-only peer"
                    checked={settings.autoDownload}
                    onChange={(e) => handleSettingChange('autoDownload', e.target.checked)}
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                </label>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-medium text-gray-900">원본 파일 보관</h3>
                  <p className="text-sm text-gray-500">변환 후에도 원본 파일을 보관합니다</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    className="sr-only peer"
                    checked={settings.keepOriginal}
                    onChange={(e) => handleSettingChange('keepOriginal', e.target.checked)}
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                </label>
              </div>
            </div>
          </div>

          {/* 저장 버튼 */}
          <div className="flex justify-end">
            <button
              onClick={handleSave}
              className={`flex items-center px-6 py-3 rounded-md text-sm font-medium transition-colors ${
                saved
                  ? 'bg-green-600 text-white'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}
            >
              {saved ? (
                <>
                  <Check className="h-4 w-4 mr-2" />
                  저장됨
                </>
              ) : (
                <>
                  <Save className="h-4 w-4 mr-2" />
                  설정 저장
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;