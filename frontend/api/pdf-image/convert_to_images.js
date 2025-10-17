// Vercel Serverless Function for PDF to Image conversion
// Proxy to Render service - Native multipart parsing approach
import FormData from 'form-data';

// Native multipart parser without formidable
function parseMultipartData(buffer, boundary) {
  const boundaryBuffer = Buffer.from(`--${boundary}`);
  const parts = [];
  let start = 0;
  
  while (true) {
    const boundaryIndex = buffer.indexOf(boundaryBuffer, start);
    if (boundaryIndex === -1) break;
    
    if (start > 0) {
      const partData = buffer.slice(start, boundaryIndex);
      const headerEndIndex = partData.indexOf('\r\n\r\n');
      
      if (headerEndIndex !== -1) {
        const headers = partData.slice(0, headerEndIndex).toString();
        const content = partData.slice(headerEndIndex + 4, partData.length - 2); // Remove trailing \r\n
        
        const nameMatch = headers.match(/name="([^"]+)"/);
        const filenameMatch = headers.match(/filename="([^"]+)"/);
        
        if (nameMatch) {
          parts.push({
            name: nameMatch[1],
            filename: filenameMatch ? filenameMatch[1] : null,
            content: content,
            headers: headers
          });
        }
      }
    }
    
    start = boundaryIndex + boundaryBuffer.length;
  }
  
  return parts;
}

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
    console.log('[PDF-Image] Starting native multipart processing');
    console.log('[PDF-Image] Content-Type:', req.headers['content-type']);
    console.log('[PDF-Image] Request method:', req.method);
    console.log('[PDF-Image] Request URL:', req.url);
    
    // Render 서비스 URL
    const renderServiceUrl = 'https://pdf-image-00tt.onrender.com/api/pdf-to-images';
    
    // Content-Type에서 boundary 추출
    const contentType = req.headers['content-type'];
    if (!contentType || !contentType.includes('multipart/form-data')) {
      console.error('[PDF-Image] Invalid content type:', contentType);
      res.status(400).json({ error: 'Content-Type must be multipart/form-data' });
      return;
    }
    
    const boundaryMatch = contentType.match(/boundary=([^;]+)/);
    if (!boundaryMatch) {
      console.error('[PDF-Image] No boundary found in content-type');
      res.status(400).json({ error: 'No boundary found in Content-Type' });
      return;
    }
    
    const boundary = boundaryMatch[1];
    console.log('[PDF-Image] Extracted boundary:', boundary);
    
    // 요청 본문 읽기
    const chunks = [];
    req.on('data', chunk => {
      console.log('[PDF-Image] Received chunk of size:', chunk.length);
      chunks.push(chunk);
    });
    
    await new Promise((resolve, reject) => {
      req.on('end', resolve);
      req.on('error', reject);
    });
    
    const buffer = Buffer.concat(chunks);
    console.log('[PDF-Image] Total buffer size:', buffer.length);
    
    if (buffer.length === 0) {
      console.error('[PDF-Image] Empty request body');
      res.status(400).json({ error: 'Empty request body' });
      return;
    }
    
    // Native multipart 파싱
    console.log('[PDF-Image] Parsing multipart data...');
    const parts = parseMultipartData(buffer, boundary);
    console.log('[PDF-Image] Parsed parts count:', parts.length);
    
    // 파트 정보 로깅
    parts.forEach((part, index) => {
      console.log(`[PDF-Image] Part ${index}: name="${part.name}", filename="${part.filename}", size=${part.content.length}`);
    });
    
    // 파일과 필드 분리
    let fileData = null;
    const fields = {};
    
    parts.forEach(part => {
      if (part.filename) {
        // 파일 데이터
        fileData = {
          buffer: part.content,
          filename: part.filename,
          name: part.name
        };
        console.log('[PDF-Image] Found file:', part.filename, 'size:', part.content.length);
      } else {
        // 필드 데이터
        fields[part.name] = part.content.toString();
        console.log('[PDF-Image] Found field:', part.name, '=', part.content.toString());
      }
    });
    
    if (!fileData) {
      console.error('[PDF-Image] No file found in multipart data');
      res.status(400).json({ error: 'file is required' });
      return;
    }
    
    // Render 서비스로 전송할 FormData 생성
    console.log('[PDF-Image] Creating FormData for Render service...');
    const formData = new FormData();
    
    // 파일 추가
    formData.append('file', fileData.buffer, {
      filename: fileData.filename,
      contentType: 'application/pdf'
    });
    
    // 필드 추가 (기본값 포함)
    formData.append('format', fields.format || 'png');
    formData.append('dpi', fields.dpi || '144');
    
    console.log('[PDF-Image] Sending request to Render service...');
    console.log('[PDF-Image] File size:', fileData.buffer.length);
    console.log('[PDF-Image] Format:', fields.format || 'png');
    console.log('[PDF-Image] DPI:', fields.dpi || '144');
    
    const response = await fetch(renderServiceUrl, {
      method: 'POST',
      body: formData,
      headers: formData.getHeaders()
    });
    
    console.log('[PDF-Image] Response status:', response.status);
    console.log('[PDF-Image] Response headers:', Object.fromEntries(response.headers.entries()));
    
    if (response.ok) {
      const contentType = response.headers.get('content-type');
      console.log('[PDF-Image] Success! Content-Type:', contentType);
      
      if (contentType && contentType.startsWith('image/')) {
        // 이미지 응답
        const resultBuffer = await response.arrayBuffer();
        res.setHeader('Content-Type', contentType);
        res.status(200).send(Buffer.from(resultBuffer));
      } else {
        // JSON 응답 (다중 이미지 등)
        const result = await response.json();
        res.status(200).json(result);
      }
    } else {
      const errorText = await response.text();
      console.error('[PDF-Image] Render service error:', errorText);
      res.status(response.status).json({ 
        error: 'Render service error', 
        details: errorText,
        status: response.status
      });
    }
    
  } catch (error) {
    console.error('[PDF-Image] Handler error:', error);
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
    bodyParser: false, // Native parsing을 위해 비활성화
    sizeLimit: '100mb', // 파일 크기 제한
  },
}