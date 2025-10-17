// Vercel Serverless Function for PDF to Image conversion
// Proxy to Render service
import formidable from 'formidable';
import FormData from 'form-data';
import fs from 'fs';

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
    
    // formidable을 사용하여 multipart/form-data 파싱
    const form = formidable({
      maxFileSize: 100 * 1024 * 1024, // 100MB
      keepExtensions: true,
    });

    const [fields, files] = await form.parse(req);
    
    // 새로운 FormData 생성
    const formData = new FormData();
    
    // 필드 추가
    Object.keys(fields).forEach(key => {
      const value = Array.isArray(fields[key]) ? fields[key][0] : fields[key];
      formData.append(key, value);
    });
    
    // 파일 추가
    Object.keys(files).forEach(key => {
      const file = Array.isArray(files[key]) ? files[key][0] : files[key];
      if (file && file.filepath) {
        formData.append(key, fs.createReadStream(file.filepath), {
          filename: file.originalFilename || 'file.pdf',
          contentType: file.mimetype || 'application/pdf'
        });
      }
    });

    // Render 서비스로 요청 전송
    const response = await fetch(renderServiceUrl, {
      method: 'POST',
      body: formData,
      headers: {
        ...formData.getHeaders(),
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

    // 임시 파일 정리
    Object.keys(files).forEach(key => {
      const file = Array.isArray(files[key]) ? files[key][0] : files[key];
      if (file && file.filepath) {
        try {
          fs.unlinkSync(file.filepath);
        } catch (e) {
          console.warn('Failed to cleanup temp file:', e);
        }
      }
    });

  } catch (error) {
    console.error('[PDF-Image] Proxy error:', error);
    res.status(500).json({ 
      error: 'Internal server error',
      message: 'Failed to proxy request to PDF conversion service',
      details: error.message
    });
  }
}

// Vercel 설정
export const config = {
  api: {
    bodyParser: false, // formidable이 직접 파싱하도록 설정
  },
}