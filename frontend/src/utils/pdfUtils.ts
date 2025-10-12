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
  const cd = res.headers.get("content-disposition") || "";
  const star = /filename\*\=UTF-8''([^;]+)/i.exec(cd);
  const normal = /filename="?([^\";]+)"?/i.exec(cd);
  const name = star?.[1] ? decodeURIComponent(star[1]) : (normal?.[1] || fallbackName);
  const blob = await res.blob();
  const href = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = href; a.download = name; a.style.display = "none";
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(href), 60_000);
  return name;
}