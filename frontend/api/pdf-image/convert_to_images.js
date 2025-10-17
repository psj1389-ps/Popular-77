// Vercel Serverless Function for PDF to Image conversion
// Simple binary proxy approach - forward raw request directly
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
    console.log('[PDF-Image] Binary proxy approach - forwarding raw request');
    console.log('[PDF-Image] Content-Type:', req.headers['content-type']);
    console.log('[PDF-Image] Content-Length:', req.headers['content-length']);
    console.log('[PDF-Image] Request method:', req.method);
    console.log('[PDF-Image] Request URL:', req.url);
    
    // Render 서비스 URL
    const renderServiceUrl = 'https://pdf-image-00tt.onrender.com/api/pdf-to-images';
    
    // 요청 본문을 버퍼로 읽기
    const chunks = [];
    req.on('data', chunk => {
      console.log('[PDF-Image] Received chunk of size:', chunk.length);
      chunks.push(chunk);
    });
    
    await new Promise((resolve, reject) => {
      req.on('end', resolve);
      req.on('error', reject);
    });
    
    const bodyBuffer = Buffer.concat(chunks);
    console.log('[PDF-Image] Total body size:', bodyBuffer.length);
    
    if (bodyBuffer.length === 0) {
      console.error('[PDF-Image] Empty request body');
      res.status(400).json({ error: 'Empty request body' });
      return;
    }
    
    // Debug: Show first 200 characters of body
    console.log('[PDF-Image] Body preview (first 200 chars):', bodyBuffer.toString('utf8', 0, Math.min(200, bodyBuffer.length)));
    
    // 헤더 준비 - 원본 Content-Type과 Content-Length 유지
    const forwardHeaders = {
      'Content-Type': req.headers['content-type'],
      'Content-Length': bodyBuffer.length.toString(),
      'User-Agent': 'Vercel-Proxy/1.0'
    };
    
    console.log('[PDF-Image] Forwarding headers:', forwardHeaders);
    console.log('[PDF-Image] Sending request to Render service...');
    
    // Render 서비스로 원본 요청 그대로 전달
    const response = await fetch(renderServiceUrl, {
      method: 'POST',
      body: bodyBuffer,
      headers: forwardHeaders
    });
    
    console.log('[PDF-Image] Response status:', response.status);
    console.log('[PDF-Image] Response headers:', Object.fromEntries(response.headers.entries()));
    
    if (response.ok) {
      const contentType = response.headers.get('content-type');
      console.log('[PDF-Image] Success! Content-Type:', contentType);
      
      // 응답 헤더 복사
      response.headers.forEach((value, key) => {
        if (key.toLowerCase() !== 'content-encoding' && key.toLowerCase() !== 'transfer-encoding') {
          res.setHeader(key, value);
        }
      });
      
      if (contentType && contentType.startsWith('image/')) {
        // 이미지 응답 - 바이너리 데이터
        const resultBuffer = await response.arrayBuffer();
        console.log('[PDF-Image] Returning image, size:', resultBuffer.byteLength);
        res.status(200).send(Buffer.from(resultBuffer));
      } else {
        // JSON 응답
        const result = await response.text();
        console.log('[PDF-Image] Returning JSON response');
        res.status(200).send(result);
      }
    } else {
      const errorText = await response.text();
      console.error('[PDF-Image] Render service error:', errorText);
      console.error('[PDF-Image] Response status:', response.status);
      console.error('[PDF-Image] Response headers:', Object.fromEntries(response.headers.entries()));
      
      res.status(response.status).json({ 
        error: 'Render service error', 
        details: errorText,
        status: response.status
      });
    }
    
  } catch (error) {
    console.error('[PDF-Image] Proxy error:', error);
    console.error('[PDF-Image] Error stack:', error.stack);
    res.status(500).json({ 
      error: 'Internal server error',
      message: error.message,
      stack: process.env.NODE_ENV === 'development' ? error.stack : undefined
    });
  }
}

export const config = {
  api: {
    bodyParser: false, // 원본 요청 본문을 그대로 사용
    sizeLimit: '100mb', // 파일 크기 제한
  },
}