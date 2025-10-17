// Vercel Serverless Function for PDF to Image conversion
// Proxy to Render service
export default async function handler(req, res) {
  // CORS 헤더 설정
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

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
    console.log('[PDF-Image] Proxying request to Render service');
    
    // Render 서비스 URL
    const renderServiceUrl = 'https://pdf-image-00tt.onrender.com/api/pdf-to-images';
    
    // FormData를 그대로 전달하기 위해 fetch 사용
    const response = await fetch(renderServiceUrl, {
      method: 'POST',
      body: req.body,
      headers: {
        // Content-Type은 자동으로 설정되도록 제거
        ...req.headers,
        host: undefined, // host 헤더 제거
        'x-forwarded-for': undefined,
        'x-forwarded-proto': undefined,
        'x-vercel-id': undefined
      }
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

    // 응답 데이터 스트리밍
    const buffer = await response.arrayBuffer();
    res.send(Buffer.from(buffer));

  } catch (error) {
    console.error('[PDF-Image] Proxy error:', error);
    res.status(500).json({ 
      error: 'Internal server error',
      message: 'Failed to proxy request to PDF conversion service'
    });
  }
}

// Vercel 설정
export const config = {
  api: {
    bodyParser: {
      sizeLimit: '100mb',
    },
  },
}