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
    // 요청 본문을 그대로 전달
    const body = req.body;
    
    // 백엔드 서비스로 요청 전달
    const response = await fetch(TARGET_URL, {
      method: 'POST',
      headers: {
        'Content-Type': req.headers['content-type'] || 'application/json',
      },
      body: typeof body === 'string' ? body : JSON.stringify(body),
    });

    // 응답 헤더 복사
    const contentType = response.headers.get('content-type');
    const contentDisposition = response.headers.get('content-disposition');
    
    if (contentType) {
      res.setHeader('Content-Type', contentType);
    }
    if (contentDisposition) {
      res.setHeader('Content-Disposition', contentDisposition);
    }

    // 응답 상태 코드 설정
    res.status(response.status);

    // 응답이 JSON인지 확인
    if (contentType && contentType.includes('application/json')) {
      const data = await response.json();
      res.json(data);
    } else {
      // 바이너리 데이터 (이미지 파일 등) 처리
      const buffer = await response.arrayBuffer();
      res.send(Buffer.from(buffer));
    }

  } catch (err) {
    console.error('[image-to-jpg proxy] error:', err);
    res.status(502).json({ 
      error: '이미지 변환 서비스에 연결할 수 없습니다.',
      details: err.message 
    });
  }
}