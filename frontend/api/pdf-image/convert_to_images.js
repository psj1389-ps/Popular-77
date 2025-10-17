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
    console.log('[PDF-Image] Starting request processing');
    console.log('[PDF-Image] Content-Type:', req.headers['content-type']);
    console.log('[PDF-Image] Request method:', req.method);
    console.log('[PDF-Image] Request URL:', req.url);
    
    // Render 서비스 URL
    const renderServiceUrl = 'https://pdf-image-00tt.onrender.com/api/pdf-to-images';
    
    // formidable을 사용하여 multipart/form-data 파싱
    const form = formidable({
      maxFileSize: 100 * 1024 * 1024, // 100MB
      keepExtensions: true,
      multiples: false,
    });

    console.log('[PDF-Image] Parsing form data...');
    
    let fields, files;
    try {
      [fields, files] = await form.parse(req);
    } catch (parseError) {
      console.error('[PDF-Image] Form parsing error:', parseError);
      return res.status(400).json({ 
        error: 'Failed to parse form data',
        details: parseError.message,
        contentType: req.headers['content-type']
      });
    }
    
    console.log('[PDF-Image] Parsed fields:', Object.keys(fields));
    console.log('[PDF-Image] Parsed files:', Object.keys(files));
    console.log('[PDF-Image] Files details:', Object.keys(files).map(key => {
      const file = Array.isArray(files[key]) ? files[key][0] : files[key];
      return {
        key,
        originalFilename: file?.originalFilename,
        mimetype: file?.mimetype,
        size: file?.size,
        hasFilepath: !!file?.filepath
      };
    }));
    
    // 파일이 있는지 확인
    if (!files || Object.keys(files).length === 0) {
      console.error('[PDF-Image] No files found in request');
      return res.status(400).json({ 
        error: 'No files uploaded',
        debug: {
          fieldsKeys: Object.keys(fields),
          filesKeys: Object.keys(files),
          contentType: req.headers['content-type'],
          requestBody: 'Cannot display binary data'
        }
      });
    }
    
    // 새로운 FormData 생성
    const formData = new FormData();
    
    // 필드 추가
    Object.keys(fields).forEach(key => {
      const value = Array.isArray(fields[key]) ? fields[key][0] : fields[key];
      console.log(`[PDF-Image] Adding field: ${key} = ${value}`);
      formData.append(key, value);
    });
    
    // 파일 추가 - 'file' 필드명으로 통일
    let fileAdded = false;
    Object.keys(files).forEach(key => {
      const file = Array.isArray(files[key]) ? files[key][0] : files[key];
      if (file && file.filepath && fs.existsSync(file.filepath)) {
        console.log(`[PDF-Image] Adding file: ${key} -> file`);
        console.log(`[PDF-Image] File details:`, {
          originalFilename: file.originalFilename,
          mimetype: file.mimetype,
          size: file.size,
          filepath: file.filepath,
          fileExists: fs.existsSync(file.filepath)
        });
        
        // 항상 'file' 필드명으로 추가 (Flask 서비스가 기대하는 필드명)
        const fileStream = fs.createReadStream(file.filepath);
        formData.append('file', fileStream, {
          filename: file.originalFilename || 'file.pdf',
          contentType: file.mimetype || 'application/pdf'
        });
        fileAdded = true;
      } else {
        console.error(`[PDF-Image] Invalid file object:`, {
          key,
          hasFile: !!file,
          hasFilepath: !!file?.filepath,
          fileExists: file?.filepath ? fs.existsSync(file.filepath) : false
        });
      }
    });
    
    if (!fileAdded) {
      console.error('[PDF-Image] No valid files found to forward');
      return res.status(400).json({ 
        error: 'No valid files found',
        debug: {
          filesInfo: Object.keys(files).map(key => {
            const file = Array.isArray(files[key]) ? files[key][0] : files[key];
            return {
              key,
              hasFilepath: !!file?.filepath,
              originalFilename: file?.originalFilename,
              size: file?.size,
              fileExists: file?.filepath ? fs.existsSync(file.filepath) : false
            };
          })
        }
      });
    }

    console.log('[PDF-Image] Sending request to Render service...');
    console.log('[PDF-Image] FormData headers:', formData.getHeaders());
    
    // Render 서비스로 요청 전송
    const response = await fetch(renderServiceUrl, {
      method: 'POST',
      body: formData,
      headers: {
        ...formData.getHeaders(),
      }
    });

    console.log('[PDF-Image] Render service response status:', response.status);
    console.log('[PDF-Image] Render service response headers:', Object.fromEntries(response.headers.entries()));

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

    // 응답 데이터 처리
    if (response.ok) {
      // 성공적인 응답 - 바이너리 데이터 스트리밍
      const buffer = await response.arrayBuffer();
      console.log('[PDF-Image] Sending successful response, size:', buffer.byteLength);
      res.send(Buffer.from(buffer));
    } else {
      // 에러 응답 - JSON으로 처리
      const errorText = await response.text();
      console.error('[PDF-Image] Render service error:', errorText);
      res.send(errorText);
    }

    // 임시 파일 정리
    Object.keys(files).forEach(key => {
      const file = Array.isArray(files[key]) ? files[key][0] : files[key];
      if (file && file.filepath) {
        try {
          fs.unlinkSync(file.filepath);
          console.log('[PDF-Image] Cleaned up temp file:', file.filepath);
        } catch (e) {
          console.warn('[PDF-Image] Failed to cleanup temp file:', e.message);
        }
      }
    });

  } catch (error) {
    console.error('[PDF-Image] Proxy error:', error);
    console.error('[PDF-Image] Error stack:', error.stack);
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
    sizeLimit: '100mb', // 파일 크기 제한
  },
}