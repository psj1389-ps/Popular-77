// Vercel Serverless Function for PDF to TIFF conversion
// Dynamic proxy for all pdf-tiff routes
export default async function handler(req, res) {
  // CORS 헤더 설정
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  // OPTIONS 요청 처리 (CORS preflight)
  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  try {
    // URL 경로에서 /api/pdf-tiff/ 이후의 경로 추출
    const { path } = req.query;
    const targetPath = Array.isArray(path) ? path.join('/') : (path || '');
    
    console.log('[PDF-TIFF] Request method:', req.method);
    console.log('[PDF-TIFF] Target path:', targetPath);
    console.log('[PDF-TIFF] Content-Type:', req.headers['content-type']);
    console.log('[PDF-TIFF] Content-Length:', req.headers['content-length']);
    
    // Render 서비스 URL 구성
    const renderServiceUrl = `https://pdf-tiff.onrender.com/${targetPath}`;
    console.log('[PDF-TIFF] Target URL:', renderServiceUrl);
    
    let bodyBuffer = null;
    
    // POST 요청의 경우 본문 데이터 처리
    if (req.method === 'POST' || req.method === 'PUT') {
      const chunks = [];
      req.on('data', chunk => {
        chunks.push(chunk);
      });
      
      await new Promise((resolve, reject) => {
        req.on('end', resolve);
        req.on('error', reject);
      });
      
      bodyBuffer = Buffer.concat(chunks);
      console.log('[PDF-TIFF] Body size:', bodyBuffer.length);
    }

    // 헤더 준비 (필요한 헤더만 전달)
    const forwardHeaders = {
      'User-Agent': 'Vercel-Proxy/1.0'
    };
    
    // Content-Type과 Content-Length는 POST/PUT 요청에만 추가
    if (bodyBuffer && bodyBuffer.length > 0) {
      if (req.headers['content-type']) {
        forwardHeaders['Content-Type'] = req.headers['content-type'];
      }
      forwardHeaders['Content-Length'] = bodyBuffer.length.toString();
    }
    
    console.log('[PDF-TIFF] Forward headers:', forwardHeaders);
    console.log('[PDF-TIFF] Sending request to Render service...');
    
    // Render 서비스로 요청 전달
    const fetchOptions = {
      method: req.method,
      headers: forwardHeaders
    };
    
    if (bodyBuffer && bodyBuffer.length > 0) {
      fetchOptions.body = bodyBuffer;
    }
    
    const response = await fetch(renderServiceUrl, fetchOptions);
    
    console.log('[PDF-TIFF] Response status:', response.status);
    console.log('[PDF-TIFF] Response headers:', Object.fromEntries(response.headers.entries()));
    
    if (response.ok) {
      const contentType = response.headers.get('content-type') || '';
      console.log('[PDF-TIFF] Success! Content-Type:', contentType);
      
      // 응답 헤더 복사 (중요한 헤더들만)
      const headersToForward = [
        'content-type',
        'content-disposition',
        'content-length',
        'cache-control',
        'expires',
        'last-modified',
        'etag'
      ];
      
      headersToForward.forEach(headerName => {
        const headerValue = response.headers.get(headerName);
        if (headerValue) {
          res.setHeader(headerName, headerValue);
        }
      });
      
      // 응답 타입에 따른 처리
      if (contentType.includes('application/json')) {
        // JSON 응답
        const result = await response.json();
        console.log('[PDF-TIFF] Returning JSON response');
        res.status(response.status).json(result);
      } else if (contentType.includes('application/zip') || 
                 contentType.includes('image/') || 
                 contentType.includes('application/octet-stream')) {
        // 바이너리 응답 (ZIP, 이미지 등)
        const resultBuffer = await response.arrayBuffer();
        console.log('[PDF-TIFF] Returning binary response, size:', resultBuffer.byteLength);
        res.status(response.status).send(Buffer.from(resultBuffer));
      } else {
        // 텍스트 응답
        const result = await response.text();
        console.log('[PDF-TIFF] Returning text response');
        res.status(response.status).send(result);
      }
    } else {
      const errorText = await response.text();
      console.error('[PDF-TIFF] Render service error:', errorText);
      console.error('[PDF-TIFF] Response status:', response.status);
      console.error('[PDF-TIFF] Response headers:', Object.fromEntries(response.headers.entries()));
      
      res.status(response.status).json({ 
        error: 'Render service error', 
        details: errorText,
        status: response.status,
        url: renderServiceUrl
      });
    }
    
  } catch (error) {
    console.error('[PDF-TIFF] Proxy error:', error);
    console.error('[PDF-TIFF] Error stack:', error.stack);
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