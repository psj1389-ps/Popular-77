import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { supabase } from '../utils/supabase';

const AuthCallback: React.FC = () => {
  const navigate = useNavigate();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const handleAuthCallback = async () => {
      try {
        // URL에서 인증 코드/오류 파라미터 확인
        const currentUrl = new URL(window.location.href);
        const codeParam = currentUrl.searchParams.get('code');
        const oauthError = currentUrl.searchParams.get('error_description') || currentUrl.searchParams.get('error');

        if (oauthError) {
          console.error('OAuth 오류:', oauthError);
          setError(oauthError);
          setStatus('error');
          return;
        }

        // 브라우저에서 코드가 전달된 경우, 안전하게 세션 교환 시도
        if (codeParam) {
          try {
            const { data: exchangeData, error: exchangeError } = await supabase.auth.exchangeCodeForSession(codeParam);
            if (exchangeError) {
              console.error('코드 교환 실패:', exchangeError);
              // 교환 실패 시 계속 진행하여 getSession으로 재확인
            } else if (exchangeData?.session) {
              // 교환으로 세션 확보된 경우 즉시 성공 처리
              setStatus('success');
              setTimeout(() => {
                // 프로필로 이동하여 인증 상태를 명확히 확인
                navigate('/profile', { replace: true });
              }, 1200);
              return;
            }
          } catch (ex) {
            console.error('코드 교환 중 예외:', ex);
            // 계속 진행하여 getSession으로 재확인
          }
        }

        // 세션 확인 (Supabase가 URL을 자동 처리한 후 세션을 반환)
        const { data, error } = await supabase.auth.getSession();
        
        if (error) {
          console.error('인증 콜백 오류:', error);
          setError(error.message);
          setStatus('error');
          return;
        }

        if (data.session) {
          console.log('로그인 성공:', data.session.user.email);
          setStatus('success');
          
          // 성공 메시지를 잠시 보여준 후 홈으로 리다이렉트
          setTimeout(() => {
            // 홈에서 예기치 않은 연결 문제가 있을 경우를 대비해 프로필로 이동
            navigate('/profile', { replace: true });
          }, 2000);
        } else {
          // 세션이 없는 경우 로그인 페이지로 리다이렉트
          console.log('세션이 없습니다. 로그인 페이지로 이동합니다.');
          navigate('/login', { replace: true });
        }
      } catch (err: any) {
        console.error('인증 처리 중 오류:', err);
        setError(err.message || '인증 처리 중 오류가 발생했습니다.');
        setStatus('error');
      }
    };

    handleAuthCallback();
  }, [navigate]);

  const handleRetry = () => {
    navigate('/login', { replace: true });
  };

  const handleGoHome = () => {
    navigate('/', { replace: true });
  };

  if (status === 'loading') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            로그인 처리 중...
          </h2>
          <p className="text-gray-600">
            잠시만 기다려주세요.
          </p>
        </div>
      </div>
    );
  }

  if (status === 'success') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-green-100 mb-4">
            <svg
              className="h-8 w-8 text-green-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M5 13l4 4L19 7"
              />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            로그인 성공!
          </h2>
          <p className="text-gray-600 mb-4">
            곧 홈페이지로 이동합니다...
          </p>
          <button
            onClick={handleGoHome}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            지금 이동하기
          </button>
        </div>
      </div>
    );
  }

  if (status === 'error') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center max-w-md mx-auto px-4">
          <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-red-100 mb-4">
            <svg
              className="h-8 w-8 text-red-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            로그인 실패
          </h2>
          <p className="text-gray-600 mb-4">
            {error || '로그인 처리 중 오류가 발생했습니다.'}
          </p>
          <div className="space-y-3">
            <button
              onClick={handleRetry}
              className="w-full inline-flex justify-center items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              다시 로그인하기
            </button>
            <button
              onClick={handleGoHome}
              className="w-full inline-flex justify-center items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              홈으로 돌아가기
            </button>
          </div>
        </div>
      </div>
    );
  }

  return null;
};

export default AuthCallback;