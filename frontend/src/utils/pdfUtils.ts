import * as pdfjsLib from "pdfjs-dist";

// 1회 설정 가드
let workerReady = false;
function ensurePdfWorker() {
  if (workerReady) return;
  if (typeof window === "undefined") return; // 브라우저에서만

  try {
    // 1) CDN 워커(버전 고정)
    (pdfjsLib as any).GlobalWorkerOptions.workerSrc = 
      "https://unpkg.com/pdfjs-dist@5.4.296/build/pdf.worker.min.js";
    workerReady = true;
  } catch {
    // no-op
  }

  // 2) 폴백: 로컬 워커는 빌드 오류를 방지하기 위해 제거
  // CDN이 실패하면 콘솔 경고만 남기고 계속 진행
  if (!workerReady) {
    console.warn("[pdfjs] CDN worker setup failed, PDF functionality may be limited.");
  }
}

// RFC5987 Content-Disposition 헤더에서 파일명 추출 (개선된 버전)
export function safeGetFilename(res: Response, fallback: string): string {
  const disp = res.headers.get('Content-Disposition') || '';
  let fname = fallback;
  
  // filename*=UTF-8''... 형식 우선 파싱 (RFC5987)
  const m = disp.match(/filename\*?=([^;]+)/i);
  if (m) {
    let v = m[1].trim();
    if (v.startsWith("UTF-8''")) {
      v = decodeURIComponent(v.slice(7));
    }
    fname = v.replace(/^"+|"+$/g, '');
  }
  
  return fname || fallback;
}

// 직접 다운로드(직행 URL/프록시 URL 공통)
export function triggerDirectDownload(url: string, filename?: string) {
  try {
    const a = document.createElement("a");
    a.href = url;
    if (filename) a.download = filename;
    a.style.display = "none";
    document.body.appendChild(a);
    a.click();
    a.remove();
  } catch {}
  setTimeout(() => {
    const iframe = document.createElement("iframe");
    iframe.style.display = "none";
    iframe.src = url;
    document.body.appendChild(iframe);
    setTimeout(() => iframe.remove(), 60_000);
  }, 300);
}

// Blob 다운로드 함수 (개선된 파일명 처리)
export function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename; // 서버가 내려준 파일명 그대로 사용
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export async function getPdfPageCount(file: File): Promise<number> {
  ensurePdfWorker();
  const buf = await file.arrayBuffer();
  const doc = await pdfjsLib.getDocument({ data: buf }).promise;
  const n = doc.numPages;
  doc.destroy?.();
  return n;
}

export async function directPostAndDownload(url: string, form: FormData, fallbackName: string) {
  const res = await fetch(url, { method: "POST", body: form });
  if (!res.ok) {
    const ct = res.headers.get("content-type") || "";
    const msg = ct.includes("application/json")
      ? (await res.json().catch(() => null))?.error
      : await res.text().catch(() => "");
    throw new Error(msg || `요청 실패(${res.status})`);
  }
  
  // 개선된 파일명 추출 사용
  const name = safeGetFilename(res, fallbackName);
  const blob = await res.blob();
  
  // 개선된 다운로드 함수 사용
  downloadBlob(blob, name);
  
  return name;
}