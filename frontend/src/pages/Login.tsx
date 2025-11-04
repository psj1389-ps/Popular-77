import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthContext } from '../contexts/AuthContext';
import { isInAppBrowser, openInExternalBrowser, isAndroid, isIOS } from '@/utils/inAppBrowser';

const Login: React.FC = () => {
  const navigate = useNavigate();
  const { user, loading, error, signInWithGoogle } = useAuthContext();
  const [isLoading, setIsLoading] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);
  const [inApp, setInApp] = useState(false);

  // 이미 로그인된 사용자는 홈으로 리다이렉트
  useEffect(() => {
    if (user && !loading) {
      navigate('/', { replace: true });
    }
  }, [user, loading, navigate]);

  // 인앱(WebView) 브라우저 감지: Google이 disallowed_useragent로 차단하는 환경
  useEffect(() => {
    try {
      setInApp(isInAppBrowser());
    } catch {}
  }, []);

  const handleGoogleLogin = async () => {
    // 인앱(WebView)에서는 Google이 로그인을 차단(disallowed_useragent)
    if (inApp) {
      setAuthError('현재 앱 내 브라우저에서는 Google 로그인이 차단됩니다. 외부 브라우저에서 다시 시도해주세요.');
      // 현재 페이지를 외부 브라우저로 열기 시도
      openInExternalBrowser(window.location.href);
      return;
    }

    setIsLoading(true);
    setAuthError(null);

    try {
      const { error } = await signInWithGoogle();
      if (error) {
        setAuthError(error);
      }
    } catch (err) {
      setAuthError('Google 로그인 중 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
  };



  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <div className="mx-auto h-12 w-12 flex items-center justify-center rounded-full bg-blue-100">
            <svg
              className="h-6 w-6 text-blue-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
              />
            </svg>
          </div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            77 Tools에 로그인
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            소셜 계정으로 간편하게 로그인하세요
          </p>
        </div>

        <div className="mt-8 space-y-4">
          {/* 인앱 브라우저 경고 및 외부 브라우저로 열기 가이드 */}
          {inApp && (
            <div className="rounded-md bg-yellow-50 p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg
                    className="h-5 w-5 text-yellow-400"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                  >
                    <path
                      fillRule="evenodd"
                      d="M18 10A8 8 0 11.001 10 8 8 0 0118 10zM9 5a1 1 0 112 0v4a1 1 0 11-2 0V5zm1 8a1 1 0 100 2 1 1 0 000-2z"
                      clipRule="evenodd"
                    />
                  </svg>
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-yellow-800">앱 내 브라우저에서 Google 로그인이 차단됩니다</h3>
                  <div className="mt-1 text-sm text-yellow-700">
                    disallowed_useragent 오류를 피하려면 외부 브라우저(Chrome/Safari)에서 다시 시도해주세요.
                  </div>
                  <div className="mt-3">
                    <button
                      onClick={() => openInExternalBrowser(window.location.href)}
                      className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    >
                      {isAndroid() ? 'Chrome에서 열기' : isIOS() ? 'Safari에서 열기' : '브라우저에서 열기'}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
          {/* 에러 메시지 */}
          {(error || authError) && (
            <div className="rounded-md bg-red-50 p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg
                    className="h-5 w-5 text-red-400"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                  >
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                      clipRule="evenodd"
                    />
                  </svg>
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-red-800">
                    로그인 오류
                  </h3>
                  <div className="mt-2 text-sm text-red-700">
                    {error || authError}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Google 로그인 버튼 */}
          <button
            onClick={handleGoogleLogin}
            disabled={isLoading}
            className="group relative w-full flex justify-center py-3 px-4 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
            style={{ fontSize: '115%' }}
          >
            <span className="absolute left-0 inset-y-0 flex items-center pl-3">
              <svg className="h-5 w-5" viewBox="0 0 24 24">
                <path
                  fill="#4285F4"
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                />
                <path
                  fill="#34A853"
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                />
                <path
                  fill="#FBBC05"
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                />
                <path
                  fill="#EA4335"
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                />
              </svg>
            </span>
          {isLoading ? '로그인 중...' : 'Google로 로그인'}
          </button>

          {/* KakaoTalk 로그인 버튼 제거 */}

          {/* 홈으로 돌아가기 링크 제거 */}
        </div>

        {/* 추가 정보 */}
        <div className="mt-6">
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-300" />
            </div>
            {/* 홈으로 돌아가기 링크 (구글 로그인 글자크기와 동일, 파란색) */}
            <div className="relative flex justify-center text-sm mb-2">
              <a
                href="https://77-tools.xyz/"
                className="px-2 bg-gray-50 text-blue-600 hover:text-blue-500 font-medium"
                style={{ fontSize: '115%' }}
                title="홈으로 돌아가기"
              >
                홈으로 돌아가기
              </a>
            </div>
            <div className="relative flex justify-center text-sm">
              <span
                role="button"
                className="px-2 bg-gray-50 text-gray-500 cursor-pointer"
                title="Google 로그인"
                onClick={(e) => { e.preventDefault(); handleGoogleLogin(); }}
              >
                로그인하면 서비스 이용약관에 동의하게 됩니다
              </span>
            </div>
            {/* 구글 로그인 링크 안내: div 버튼화 */}
            <div className="mt-3 text-center text-sm text-gray-600">
              이미 계정이 있으신가요? (
              <div
                role="button"
                tabIndex={0}
                className="inline text-blue-600 hover:text-blue-500 font-medium cursor-pointer"
                title="Google 로그인"
                onClick={() => { handleGoogleLogin(); }}
                onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { handleGoogleLogin(); } }}
              >
                로그인
              </div>
              )
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;