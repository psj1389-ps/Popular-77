// Vercel Serverless Function: Proxy for /api/image-to-jpg
// 목적: 프론트엔드가 동일 도메인(/api/image-to-jpg)으로 호출하면
// 백엔드 서비스(https://popular-77-srwb.onrender.com)로 프록시

const TARGET_URL = 'https://popular-77-srwb.onrender.com/api/image-to-jpg';

export default async function handler(req, res) {
  // CORS 헤더 설정
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  res.setHeader('Access-Control-Expose-Headers', 'Content-Disposition');

  // OPTIONS 요청 처리 (CORS preflight)
  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  // POST 요청만 허용
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed' });
    return;
  }

  try {
    // 원본 Content-Type 유지 (multipart/form-data 포함)
    const contentType = req.headers['content-type'] || 'application/octet-stream';

    // 백엔드 서비스로 원본 바디를 스트리밍으로 전달 (Node.js fetch streaming)
    const response = await fetch(TARGET_URL, {
      method: 'POST',
      headers: {
        'Content-Type': contentType,
        'Accept': '*/*',
      },
      body: req,
      duplex: 'half',
    });

    // 413 처리: 친절한 JSON 메시지로 반환
    if (response.status === 413) {
      res.setHeader('Content-Type', 'application/json; charset=utf-8');
      res.status(413).json({
        error: '업로드 파일이 너무 큽니다 (413). GIF는 용량이 클 수 있어, 크기/품질을 낮추거나 JPG로 압축 후 다시 시도해 주세요.',
      });
      return;
    }

    // 응답 헤더 복사 (파일 다운로드용 헤더 유지)
    const ct = response.headers.get('content-type');
    const cd = response.headers.get('content-disposition');
    if (ct) res.setHeader('Content-Type', ct);
    if (cd) res.setHeader('Content-Disposition', cd);

    // 응답 상태 코드 설정
    res.status(response.status);

    // 응답 처리 (JSON vs 바이너리)
    if (ct && ct.includes('application/json')) {
      const data = await response.json();
      res.json(data);
    } else {
      const arrayBuffer = await response.arrayBuffer();
      res.send(Buffer.from(arrayBuffer));
    }

  } catch (err) {
    console.error('[image-to-jpg proxy] error:', err);
    res.status(502).json({ 
      error: '이미지 변환 서비스에 연결할 수 없습니다.',
      details: err instanceof Error ? err.message : String(err)
    });
  }
}