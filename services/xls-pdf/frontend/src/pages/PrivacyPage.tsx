import React from 'react';
import { Shield, Lock, Eye, Database, Mail, Phone } from 'lucide-react';

const PrivacyPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* 헤더 */}
        <div className="text-center mb-12">
          <div className="flex justify-center mb-4">
            <Shield className="w-16 h-16 text-blue-600" />
          </div>
          <h1 className="text-4xl font-bold text-gray-900 mb-4">개인정보처리방침</h1>
          <p className="text-lg text-gray-600">
            Popular-77은 사용자의 개인정보를 소중히 여기며, 안전하게 보호하기 위해 최선을 다하고 있습니다.
          </p>
          <p className="text-sm text-gray-500 mt-2">최종 업데이트: 2024년 1월 1일</p>
        </div>

        {/* 주요 원칙 */}
        <div className="bg-white rounded-lg shadow-md p-8 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
            <Lock className="w-6 h-6 mr-2 text-blue-600" />
            개인정보 보호 원칙
          </h2>
          <div className="grid md:grid-cols-2 gap-6">
            <div className="flex items-start space-x-3">
              <Eye className="w-5 h-5 text-green-600 mt-1" />
              <div>
                <h3 className="font-semibold text-gray-900">투명성</h3>
                <p className="text-gray-600 text-sm">개인정보 수집 및 이용 목적을 명확히 고지합니다.</p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <Database className="w-5 h-5 text-blue-600 mt-1" />
              <div>
                <h3 className="font-semibold text-gray-900">최소 수집</h3>
                <p className="text-gray-600 text-sm">서비스 제공에 필요한 최소한의 정보만 수집합니다.</p>
              </div>
            </div>
          </div>
        </div>

        {/* 수집하는 개인정보 */}
        <div className="bg-white rounded-lg shadow-md p-8 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">수집하는 개인정보</h2>
          
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">자동 수집 정보</h3>
              <ul className="list-disc list-inside space-y-2 text-gray-600">
                <li>IP 주소, 브라우저 정보, 운영체제 정보</li>
                <li>서비스 이용 기록, 접속 로그, 쿠키</li>
                <li>기기 정보 (모바일 기기 식별정보 등)</li>
              </ul>
            </div>

            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">파일 처리 정보</h3>
              <ul className="list-disc list-inside space-y-2 text-gray-600">
                <li>업로드된 파일은 처리 후 즉시 삭제됩니다</li>
                <li>파일 내용은 서버에 저장되지 않습니다</li>
                <li>가능한 경우 브라우저에서 로컬 처리됩니다</li>
              </ul>
            </div>
          </div>
        </div>

        {/* 개인정보 이용 목적 */}
        <div className="bg-white rounded-lg shadow-md p-8 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">개인정보 이용 목적</h2>
          
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">서비스 제공</h3>
              <ul className="list-disc list-inside space-y-1 text-gray-600">
                <li>파일 변환 및 처리 서비스 제공</li>
                <li>서비스 이용 통계 분석</li>
                <li>서비스 개선 및 최적화</li>
              </ul>
            </div>
            
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">보안 및 운영</h3>
              <ul className="list-disc list-inside space-y-1 text-gray-600">
                <li>부정 이용 방지 및 보안 강화</li>
                <li>서비스 장애 대응</li>
                <li>법적 의무 이행</li>
              </ul>
            </div>
          </div>
        </div>

        {/* 개인정보 보관 및 삭제 */}
        <div className="bg-white rounded-lg shadow-md p-8 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">개인정보 보관 및 삭제</h2>
          
          <div className="space-y-4">
            <div className="bg-blue-50 p-4 rounded-lg">
              <h3 className="font-semibold text-blue-900 mb-2">파일 처리 정보</h3>
              <p className="text-blue-800">업로드된 파일은 처리 완료 즉시 자동 삭제됩니다.</p>
            </div>
            
            <div className="bg-green-50 p-4 rounded-lg">
              <h3 className="font-semibold text-green-900 mb-2">로그 정보</h3>
              <p className="text-green-800">서비스 이용 로그는 최대 1년간 보관 후 자동 삭제됩니다.</p>
            </div>
          </div>
        </div>

        {/* 개인정보 제3자 제공 */}
        <div className="bg-white rounded-lg shadow-md p-8 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">개인정보 제3자 제공</h2>
          
          <div className="bg-red-50 border border-red-200 p-6 rounded-lg">
            <h3 className="font-semibold text-red-900 mb-2">원칙적 금지</h3>
            <p className="text-red-800 mb-4">
              Popular-77은 사용자의 개인정보를 제3자에게 제공하지 않습니다.
            </p>
            
            <h4 className="font-semibold text-red-900 mb-2">예외 사항</h4>
            <ul className="list-disc list-inside space-y-1 text-red-800">
              <li>사용자의 사전 동의가 있는 경우</li>
              <li>법령에 의해 요구되는 경우</li>
              <li>수사기관의 수사목적으로 법령에 정해진 절차에 따라 요구되는 경우</li>
            </ul>
          </div>
        </div>

        {/* 사용자 권리 */}
        <div className="bg-white rounded-lg shadow-md p-8 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">사용자의 권리</h2>
          
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">열람 및 정정</h3>
              <p className="text-gray-600">
                개인정보 처리 현황에 대한 열람을 요구하거나 오류에 대한 정정을 요구할 수 있습니다.
              </p>
            </div>
            
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">삭제 및 처리정지</h3>
              <p className="text-gray-600">
                개인정보 삭제 또는 처리정지를 요구할 수 있으며, 즉시 조치하겠습니다.
              </p>
            </div>
          </div>
        </div>

        {/* 연락처 */}
        <div className="bg-white rounded-lg shadow-md p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">개인정보보호 문의</h2>
          
          <div className="space-y-4">
            <p className="text-gray-600">
              개인정보 처리에 관한 문의사항이나 불만처리, 피해구제 등에 관한 사항은 아래로 연락해 주시기 바랍니다.
            </p>
            
            <div className="flex items-center space-x-3">
              <Mail className="w-5 h-5 text-blue-600" />
              <span className="text-gray-900">이메일: privacy@popular-77.com</span>
            </div>
            
            <div className="flex items-center space-x-3">
              <Phone className="w-5 h-5 text-blue-600" />
              <span className="text-gray-900">전화: 1588-0000</span>
            </div>
          </div>
        </div>

        {/* 하단 안내 */}
        <div className="text-center mt-12 p-6 bg-gray-100 rounded-lg">
          <p className="text-gray-600">
            본 개인정보처리방침은 2024년 1월 1일부터 적용됩니다.
          </p>
          <p className="text-gray-600 mt-2">
            개정 시에는 웹사이트를 통해 공지하겠습니다.
          </p>
        </div>
      </div>
    </div>
  );
};

export default PrivacyPage;