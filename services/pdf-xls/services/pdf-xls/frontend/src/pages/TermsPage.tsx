import React from 'react';
import { FileText, Users, AlertTriangle, Scale, Clock, Shield } from 'lucide-react';

const TermsPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* 헤더 */}
        <div className="text-center mb-12">
          <div className="flex justify-center mb-4">
            <FileText className="w-16 h-16 text-blue-600" />
          </div>
          <h1 className="text-4xl font-bold text-gray-900 mb-4">이용약관</h1>
          <p className="text-lg text-gray-600">
            Popular-77 서비스를 이용하기 전에 다음 약관을 반드시 읽어보시기 바랍니다.
          </p>
          <p className="text-sm text-gray-500 mt-2">최종 업데이트: 2024년 1월 1일</p>
        </div>

        {/* 제1조 목적 */}
        <div className="bg-white rounded-lg shadow-md p-8 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
            <Scale className="w-6 h-6 mr-2 text-blue-600" />
            제1조 (목적)
          </h2>
          <p className="text-gray-700 leading-relaxed">
            이 약관은 Popular-77(이하 "회사")이 제공하는 온라인 파일 변환 및 처리 서비스(이하 "서비스")의 
            이용과 관련하여 회사와 이용자 간의 권리, 의무 및 책임사항, 기타 필요한 사항을 규정함을 목적으로 합니다.
          </p>
        </div>

        {/* 제2조 정의 */}
        <div className="bg-white rounded-lg shadow-md p-8 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
            <Users className="w-6 h-6 mr-2 text-blue-600" />
            제2조 (정의)
          </h2>
          <div className="space-y-4">
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">1. "서비스"</h3>
              <p className="text-gray-700 pl-4">
                회사가 제공하는 PDF 변환, 이미지 처리, 텍스트 변환 등의 온라인 파일 처리 도구를 의미합니다.
              </p>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">2. "이용자"</h3>
              <p className="text-gray-700 pl-4">
                본 약관에 따라 회사가 제공하는 서비스를 받는 개인 또는 법인을 의미합니다.
              </p>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">3. "콘텐츠"</h3>
              <p className="text-gray-700 pl-4">
                이용자가 서비스를 이용하면서 업로드하는 파일, 문서, 이미지 등의 정보를 의미합니다.
              </p>
            </div>
          </div>
        </div>

        {/* 제3조 서비스 제공 */}
        <div className="bg-white rounded-lg shadow-md p-8 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
            <Shield className="w-6 h-6 mr-2 text-blue-600" />
            제3조 (서비스의 제공)
          </h2>
          
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">1. 제공 서비스</h3>
              <ul className="list-disc list-inside space-y-2 text-gray-700 pl-4">
                <li>PDF 파일 변환 서비스 (PDF ↔ DOC, PPT, 이미지 등)</li>
                <li>이미지 편집 및 변환 서비스</li>
                <li>텍스트 처리 및 변환 서비스</li>
                <li>기타 파일 처리 관련 유틸리티 서비스</li>
              </ul>
            </div>

            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">2. 서비스 특징</h3>
              <div className="grid md:grid-cols-2 gap-4">
                <div className="bg-blue-50 p-4 rounded-lg">
                  <h4 className="font-semibold text-blue-900 mb-2">무료 제공</h4>
                  <p className="text-blue-800 text-sm">기본 서비스는 무료로 제공됩니다.</p>
                </div>
                <div className="bg-green-50 p-4 rounded-lg">
                  <h4 className="font-semibold text-green-900 mb-2">로컬 처리</h4>
                  <p className="text-green-800 text-sm">가능한 경우 브라우저에서 로컬 처리됩니다.</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 제4조 이용자의 의무 */}
        <div className="bg-white rounded-lg shadow-md p-8 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
            <AlertTriangle className="w-6 h-6 mr-2 text-orange-600" />
            제4조 (이용자의 의무)
          </h2>
          
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">금지 행위</h3>
              <div className="bg-red-50 border border-red-200 p-4 rounded-lg">
                <ul className="list-disc list-inside space-y-2 text-red-800">
                  <li>저작권, 상표권 등 타인의 지적재산권을 침해하는 파일 업로드</li>
                  <li>음란물, 폭력적 내용 등 불법적인 콘텐츠 처리</li>
                  <li>악성코드, 바이러스가 포함된 파일 업로드</li>
                  <li>서비스의 정상적인 운영을 방해하는 행위</li>
                  <li>타인의 개인정보를 무단으로 수집, 이용하는 행위</li>
                  <li>서비스를 상업적 목적으로 무단 이용하는 행위</li>
                </ul>
              </div>
            </div>

            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">준수 사항</h3>
              <ul className="list-disc list-inside space-y-2 text-gray-700 pl-4">
                <li>관련 법령 및 본 약관을 준수할 의무</li>
                <li>업로드하는 파일에 대한 적법한 권한 보유</li>
                <li>서비스 이용 시 타인에게 피해를 주지 않을 의무</li>
              </ul>
            </div>
          </div>
        </div>

        {/* 제5조 서비스 이용 제한 */}
        <div className="bg-white rounded-lg shadow-md p-8 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
            <Clock className="w-6 h-6 mr-2 text-purple-600" />
            제5조 (서비스 이용 제한)
          </h2>
          
          <div className="space-y-4">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">파일 크기 제한</h3>
              <div className="bg-yellow-50 p-4 rounded-lg">
                <ul className="list-disc list-inside space-y-1 text-yellow-800">
                  <li>단일 파일 최대 크기: 100MB</li>
                  <li>동시 처리 파일 수: 최대 5개</li>
                  <li>일일 처리 한도: 개인당 50회</li>
                </ul>
              </div>
            </div>

            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">지원 파일 형식</h3>
              <div className="grid md:grid-cols-3 gap-4">
                <div>
                  <h4 className="font-semibold text-gray-900 mb-2">문서</h4>
                  <p className="text-gray-600 text-sm">PDF, DOC, DOCX, PPT, PPTX, XLS, XLSX</p>
                </div>
                <div>
                  <h4 className="font-semibold text-gray-900 mb-2">이미지</h4>
                  <p className="text-gray-600 text-sm">JPG, PNG, GIF, BMP, TIFF, SVG</p>
                </div>
                <div>
                  <h4 className="font-semibold text-gray-900 mb-2">기타</h4>
                  <p className="text-gray-600 text-sm">TXT, CSV, JSON, XML</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 제6조 책임의 제한 */}
        <div className="bg-white rounded-lg shadow-md p-8 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">제6조 (책임의 제한)</h2>
          
          <div className="space-y-4">
            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="font-semibold text-gray-900 mb-2">1. 서비스 제공 책임</h3>
              <p className="text-gray-700">
                회사는 천재지변, 전쟁, 기간통신사업자의 서비스 중지, 정전 등 불가항력적 사유로 
                서비스를 제공할 수 없는 경우 책임이 면제됩니다.
              </p>
            </div>

            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="font-semibold text-gray-900 mb-2">2. 콘텐츠 책임</h3>
              <p className="text-gray-700">
                이용자가 업로드한 파일의 내용에 대해서는 이용자가 모든 책임을 지며, 
                회사는 이에 대한 책임을 지지 않습니다.
              </p>
            </div>

            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="font-semibold text-gray-900 mb-2">3. 손해배상 제한</h3>
              <p className="text-gray-700">
                회사의 고의 또는 중대한 과실이 없는 한, 서비스 이용과 관련하여 발생한 
                손해에 대해 배상책임을 지지 않습니다.
              </p>
            </div>
          </div>
        </div>

        {/* 제7조 개인정보보호 */}
        <div className="bg-white rounded-lg shadow-md p-8 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">제7조 (개인정보보호)</h2>
          
          <div className="space-y-4">
            <p className="text-gray-700">
              회사는 이용자의 개인정보를 보호하기 위해 개인정보처리방침을 수립하여 시행하고 있습니다.
            </p>
            
            <div className="bg-blue-50 p-4 rounded-lg">
              <h3 className="font-semibold text-blue-900 mb-2">파일 처리 원칙</h3>
              <ul className="list-disc list-inside space-y-1 text-blue-800">
                <li>업로드된 파일은 처리 완료 즉시 자동 삭제됩니다</li>
                <li>파일 내용은 서버에 저장되지 않습니다</li>
                <li>가능한 경우 브라우저에서 로컬 처리됩니다</li>
              </ul>
            </div>
          </div>
        </div>

        {/* 제8조 약관의 변경 */}
        <div className="bg-white rounded-lg shadow-md p-8 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">제8조 (약관의 변경)</h2>
          
          <div className="space-y-4">
            <p className="text-gray-700">
              회사는 필요에 따라 본 약관을 변경할 수 있으며, 변경된 약관은 웹사이트에 
              공지함으로써 효력이 발생합니다.
            </p>
            
            <div className="bg-yellow-50 p-4 rounded-lg">
              <h3 className="font-semibold text-yellow-900 mb-2">변경 절차</h3>
              <ul className="list-disc list-inside space-y-1 text-yellow-800">
                <li>변경 사유 및 내용을 웹사이트에 7일 전 공지</li>
                <li>중요한 변경사항의 경우 30일 전 공지</li>
                <li>변경된 약관에 동의하지 않는 경우 서비스 이용 중단 가능</li>
              </ul>
            </div>
          </div>
        </div>

        {/* 제9조 준거법 및 관할법원 */}
        <div className="bg-white rounded-lg shadow-md p-8 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">제9조 (준거법 및 관할법원)</h2>
          
          <div className="space-y-4">
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">1. 준거법</h3>
              <p className="text-gray-700">본 약관은 대한민국 법률에 따라 해석됩니다.</p>
            </div>
            
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">2. 관할법원</h3>
              <p className="text-gray-700">
                서비스 이용과 관련하여 발생한 분쟁에 대해서는 서울중앙지방법원을 
                제1심 관할법원으로 합니다.
              </p>
            </div>
          </div>
        </div>

        {/* 부칙 */}
        <div className="bg-white rounded-lg shadow-md p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">부칙</h2>
          
          <div className="space-y-4">
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">시행일</h3>
              <p className="text-gray-700">본 약관은 2024년 1월 1일부터 시행됩니다.</p>
            </div>
            
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">문의처</h3>
              <div className="bg-gray-50 p-4 rounded-lg">
                <p className="text-gray-700">이메일: support@popular-77.com</p>
                <p className="text-gray-700">전화: 1588-0000</p>
                <p className="text-gray-700">운영시간: 평일 09:00 ~ 18:00</p>
              </div>
            </div>
          </div>
        </div>

        {/* 하단 안내 */}
        <div className="text-center mt-12 p-6 bg-gray-100 rounded-lg">
          <p className="text-gray-600">
            본 이용약관은 2024년 1월 1일부터 적용됩니다.
          </p>
          <p className="text-gray-600 mt-2">
            서비스를 이용함으로써 본 약관에 동의한 것으로 간주됩니다.
          </p>
        </div>
      </div>
    </div>
  );
};

export default TermsPage;