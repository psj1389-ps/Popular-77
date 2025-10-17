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
    
    // 새로운 접근 방식: 직접 multipart 파싱 시도
    console.log('[PDF-Image] Attempting direct multipart parsing...');
    
    // formidable 설정 최적화
    const form = formidable({
      maxFileSize: 100 * 1024 * 1024, // 100MB
      keepExtensions: true,
      multiples: false,
      allowEmptyFiles: false,
      minFileSize: 1,
    });

    console.log('[PDF-Image] Parsing form data with optimized settings...');
    
    let fields, files;
    try {
      // Promise 기반 파싱 대신 콜백 방식 시도
      const parseResult = await new Promise((resolve, reject) => {
        form.parse(req, (err, fields, files) => {
          if (err) {
            console.error('[PDF-Image] Callback parse error:', err);
            reject(err);
          } else {
            console.log('[PDF-Image] Callback parse success');
            resolve({ fields, files });
          }
        });
      });
      
      fields = parseResult.fields;
      files = parseResult.files;
      
      console.log('[PDF-Image] Form parsing completed successfully');
    } catch (parseError) {
      console.error('[PDF-Image] Form parsing error:', parseError);
      console.error('[PDF-Image] Parse error stack:', parseError.stack);
      
      // 대안: 원시 바이너리 데이터 처리 시도
      console.log('[PDF-Image] Attempting raw binary processing...');
      try {
        const chunks = [];
        req.on('data', chunk => chunks.push(chunk));
        await new Promise((resolve, reject) => {
          req.on('end', resolve);
          req.on('error', reject);
        });
        
        const buffer = Buffer.concat(chunks);
        console.log('[PDF-Image] Raw buffer size:', buffer.length);
        
        if (buffer.length > 0) {
          // 직접 FormData로 전송
          const formData = new FormData();
          formData.append('file', buffer, {
            filename: 'uploaded.pdf',
            contentType: 'application/pdf'
          });
          
          // 기본 파라미터 추가
          formData.append('format', 'png');
          formData.append('dpi', '144');
          
          console.log('[PDF-Image] Sending raw buffer to Render service...');
          const response = await fetch(renderServiceUrl, {
            method: 'POST',
            body: formData,
            headers: formData.getHeaders()
          });
          
          console.log('[PDF-Image] Raw buffer response status:', response.status);
          
          if (response.ok) {
            const resultBuffer = await response.arrayBuffer();
            res.setHeader('Content-Type', response.headers.get('content-type') || 'image/png');
            res.status(200).send(Buffer.from(resultBuffer));
            return;
          } else {
            const errorText = await response.text();
            console.error('[PDF-Image] Raw buffer error:', errorText);
          }
        }
      } catch (rawError) {
        console.error('[PDF-Image] Raw processing error:', rawError);
      }
      
      return res.status(400).json({ 
        error: 'Failed to parse form data',
        details: parseError.message,
        contentType: req.headers['content-type'],
        stack: parseError.stack
      });
    }
    
    console.log('[PDF-Image] Parsed fields:', Object.keys(fields));
    console.log('[PDF-Image] Parsed files:', Object.keys(files));
    
    // 파일 상세 정보 로깅
    const fileDetails = Object.keys(files).map(key => {
      const file = Array.isArray(files[key]) ? files[key][0] : files[key];
      return {
        key,
        originalFilename: file?.originalFilename,
        mimetype: file?.mimetype,
        size: file?.size,
        hasFilepath: !!file?.filepath,
        filepath: file?.filepath
      };
    });
    console.log('[PDF-Image] Files details:', JSON.stringify(fileDetails, null, 2));
    
    // 파일이 있는지 확인
    if (!files || Object.keys(files).length === 0) {
      console.error('[PDF-Image] No files found in request');
      return res.status(400).json({ 
        error: 'No files uploaded',
        debug: {
          fieldsKeys: Object.keys(fields),
          filesKeys: Object.keys(files),
          contentType: req.headers['content-type'],
          requestHeaders: req.headers
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
      if (file && file.filepath) {
        console.log(`[PDF-Image] Processing file: ${key}`);
        console.log(`[PDF-Image] File details:`, {
          originalFilename: file.originalFilename,
          mimetype: file.mimetype,
          size: file.size,
          filepath: file.filepath,
          fileExists: fs.existsSync(file.filepath)
        });
        
        if (fs.existsSync(file.filepath)) {
          // 파일 크기 확인
          const stats = fs.statSync(file.filepath);
          console.log(`[PDF-Image] File stats:`, {
            size: stats.size,
            isFile: stats.isFile(),
            mtime: stats.mtime
          });
          
          // 항상 'file' 필드명으로 추가 (Flask 서비스가 기대하는 필드명)
          const fileStream = fs.createReadStream(file.filepath);
          formData.append('file', fileStream, {
            filename: file.originalFilename || 'file.pdf',
            contentType: file.mimetype || 'application/pdf'
          });
          fileAdded = true;
          console.log(`[PDF-Image] File added successfully: ${file.originalFilename}`);
        } else {
          console.error(`[PDF-Image] File does not exist at path: ${file.filepath}`);
        }
      } else {
        console.error(`[PDF-Image] Invalid file object:`, {
          key,
          hasFile: !!file,
          hasFilepath: !!file?.filepath,
          file: file ? {
            originalFilename: file.originalFilename,
            size: file.size,
            mimetype: file.mimetype
          } : null
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
              filepath: file?.filepath,
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
      details: error.message,
      stack: error.stack
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