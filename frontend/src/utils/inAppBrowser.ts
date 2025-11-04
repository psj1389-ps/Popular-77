// 인앱 브라우저 감지 및 외부 브라우저로 열기 유틸
export function isAndroid() {
  return /Android/i.test(navigator.userAgent);
}

export function isIOS() {
  return /iPhone|iPad|iPod/i.test(navigator.userAgent);
}

// 일반적인 인앱/웹뷰 UA 패턴 감지
export function isInAppBrowser() {
  const ua = navigator.userAgent || '';

  // Android WebView: ; wv;
  const isAndroidWebView = /; wv;/.test(ua) || /Android.*Version\//i.test(ua);
  // iOS WebView: AppleWebKit(?!.*Safari)
  const isIOSWebView = /(iPhone|iPad|iPod).*AppleWebKit(?!.*Safari)/i.test(ua);

  // 대표적인 인앱 브라우저들
  const inAppVendors = [
    'FBAN', 'FBAV', 'FB_IAB', // Facebook/Instagram
    'Instagram',
    'Line',
    'KAKAOTALK',
    'NAVER', 'NAVER(inapp)',
    'DaumApp',
    'Twitter', 'Twitter for iPhone', 'Twitter for Android',
    'WeChat', 'WhatsApp', 'Messenger',
    'GSA' // Google Search App
  ];
  const matchesVendor = inAppVendors.some(v => ua.includes(v));

  return isAndroidWebView || isIOSWebView || matchesVendor;
}

// 외부 브라우저로 현재 URL 열기 (Android는 Chrome 인텐트 시도)
export function openInExternalBrowser(targetUrl?: string) {
  const url = targetUrl || window.location.href;
  if (isAndroid()) {
    try {
      const intentUrl = `intent://${url.replace(/^https?:\/\//, '')}#Intent;scheme=https;package=com.android.chrome;end`;
      // Chrome 인텐트 우선 시도
      window.location.href = intentUrl;
      // 실패 폴백
      setTimeout(() => { window.location.href = url; }, 600);
      return;
    } catch {
      window.location.href = url;
      return;
    }
  }

  // iOS/기타: 새 탭으로 열기 (일부 인앱에서는 동일 WebView일 수 있어 안내 병행)
  window.open(url, '_blank', 'noopener');
}