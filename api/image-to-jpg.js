// Vercel Serverless Function: Proxy for /api/image-to-jpg
// 목적: 프론트엔드가 동일 도메인(/api/image-to-jpg)으로 호출하면
// 여기서 images-jpg 서비스로 안전하게 전달합니다. 리라이트가 실패해도 동작합니다.

const TARGET_URL = 'https://images-jpg-service.onrender.com/api/image-to-jpg';

export default async function handler(req, res) {
  try {
    // 허용 메서드
    if (req.method === 'OPTIONS') {
      res.setHeader('Access-Control-Allow-Origin', '*');
      res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
      res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
      // CORS에서 다운로드 파일명을 읽을 수 있도록 노출 헤더 추가
      res.setHeader('Access-Control-Expose-Headers', 'Content-Disposition');
      return res.status(200).end();
    }
    if (req.method !== 'POST') {
      return res.status(405).json({ error: 'Method not allowed' });
    }

    // 원본 요청의 Content-Type 유지
    const contentType = req.headers['content-type'] || 'application/octet-stream';

    // 스트림을 그대로 전달하여 대용량 업로드 대응
    const upstream = await fetch(TARGET_URL, {
      method: 'POST',
      headers: {
        'Content-Type': contentType,
      },
      body: req,
    });

    // 업스트림 응답 헤더 전달 (파일 다운로드를 위해 Content-Disposition 유지)
    const passthroughHeaders = [
      'content-type',
      'content-length',
      'content-disposition',
      'cache-control',
      'pragma',
      'expires',
    ];
    for (const h of passthroughHeaders) {
      const v = upstream.headers.get(h);
      if (v) res.setHeader(h, v);
    }

    // CORS 허용 및 파일명 헤더 노출
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Expose-Headers', 'Content-Disposition');

    // 상태코드 그대로 전달
    res.status(upstream.status);

    // 바이너리/텍스트 모두 대응
    if (upstream.body && typeof upstream.body.pipe === 'function') {
      // Node 18의 ReadableStream을 파이프할 수 없는 경우가 있어 버퍼로 대체
      const buf = Buffer.from(await upstream.arrayBuffer());
      return res.end(buf);
    } else {
      const buf = Buffer.from(await upstream.arrayBuffer());
      return res.end(buf);
    }
  } catch (err) {
    // 오류를 JSON으로 반환하여 프론트의 getErrorMessage가 파싱 가능
    console.error('[image-to-jpg proxy] error:', err);
    return res.status(502).json({ error: '이미지 변환 서비스 연결 실패', detail: String(err?.message || err) });
  }
}