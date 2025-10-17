// Vercel Serverless Function for PDF to Image conversion
// Enhanced proxy with multipart parsing for transparent background support
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
    console.log('[PDF-Image] Enhanced proxy with multipart parsing');
    console.log('[PDF-Image] Content-Type:', req.headers['content-type']);
    console.log('[PDF-Image] Content-Length:', req.headers['content-length']);
    
    // Render 서비스 URL
    const renderServiceUrl = 'https://pdf-image-00tt.onrender.com/api/pdf-to-images';
    
    // 요청 본문을 버퍼로 읽기
    const chunks = [];
    req.on('data', chunk => {
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

    // multipart/form-data 파싱을 위한 간단한 파서
    const contentType = req.headers['content-type'] || '';
    let parsedData = null;
    
    if (contentType.includes('multipart/form-data')) {
      console.log('[PDF-Image] Parsing multipart data for transparent parameter');
      parsedData = parseMultipartData(bodyBuffer, contentType);
      
      if (parsedData) {
        console.log('[PDF-Image] Parsed fields:', Object.keys(parsedData.fields));
        console.log('[PDF-Image] Transparent value:', parsedData.fields.transparent);
        console.log('[PDF-Image] Scale value:', parsedData.fields.scale);
        console.log('[PDF-Image] Format value:', parsedData.fields.format);
        console.log('[PDF-Image] File found:', !!parsedData.file);
      }
    }

    // 헤더 준비
    const forwardHeaders = {
      'Content-Type': req.headers['content-type'],
      'Content-Length': bodyBuffer.length.toString(),
      'User-Agent': 'Vercel-Proxy/1.0'
    };
    
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
      
      // 응답 헤더 복사 (파일명 포함)
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

// 간단한 multipart/form-data 파서
function parseMultipartData(buffer, contentType) {
  try {
    const boundaryMatch = contentType.match(/boundary=([^;]+)/);
    if (!boundaryMatch) return null;
    
    const boundary = '--' + boundaryMatch[1];
    const textData = buffer.toString('binary');
    const parts = textData.split(boundary);
    
    const fields = {};
    let file = null;
    
    for (const part of parts) {
      if (part.includes('Content-Disposition: form-data')) {
        const nameMatch = part.match(/name="([^"]+)"/);
        if (!nameMatch) continue;
        
        const fieldName = nameMatch[1];
        const contentStart = part.indexOf('\r\n\r\n') + 4;
        const contentEnd = part.lastIndexOf('\r\n');
        
        if (contentStart > 3 && contentEnd > contentStart) {
          const content = part.substring(contentStart, contentEnd);
          
          if (part.includes('filename=')) {
            // 파일 필드
            file = {
              name: fieldName,
              filename: part.match(/filename="([^"]*)"/)?.[1] || 'unknown',
              content: content
            };
          } else {
            // 일반 필드
            fields[fieldName] = content;
          }
        }
      }
    }
    
    return { fields, file };
  } catch (error) {
    console.error('[PDF-Image] Multipart parsing error:', error);
    return null;
  }
}

export const config = {
  api: {
    bodyParser: false, // 원본 요청 본문을 그대로 사용
    sizeLimit: '100mb', // 파일 크기 제한
  },
}