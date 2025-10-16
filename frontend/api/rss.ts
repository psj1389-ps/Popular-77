import type { VercelRequest, VercelResponse } from '@vercel/node';
import fs from 'fs';
import path from 'path';

export default function handler(req: VercelRequest, res: VercelResponse) {
  try {
    // Vercel 서버리스 환경에서 파일의 절대 경로를 찾습니다.
    // process.cwd()는 프로젝트의 루트 디렉토리를 가리킵니다.
    // 빌드 시 public 폴더의 내용은 루트에 복사되므로, 'public/rss.xml'이 아닌 'rss.xml'을 찾도록 시도하거나,
    // 더 안정적으로는 빌드 스크립트가 생성한 위치를 정확히 지정해야 합니다.
    //
    // ★★★ Vite 빌드 후 public 폴더의 파일은 dist 폴더 최상위로 복사됩니다.
    // 하지만 API 라우트는 다른 컨텍스트에서 실행될 수 있으므로,
    // 가장 확실한 방법은 rss.xml 파일을 API 폴더 바로 옆이나 루트에 두는 것입니다.
    //
    // 우선, 빌드된 파일이 위치할 것으로 예상되는 경로를 사용합니다.
    const filePath = path.join(process.cwd(), 'public', 'rss.xml');

    // 파일이 실제로 존재하는지 확인합니다.
    if (!fs.existsSync(filePath)) {
      console.error('File not found at:', filePath);
      return res.status(404).send('RSS feed not found.');
    }

    // 파일을 동기적으로 읽습니다.
    const xml = fs.readFileSync(filePath, 'utf-8');

    // 적절한 헤더를 설정합니다.
    res.setHeader('Content-Type', 'application/rss+xml; charset=utf-8');
    res.setHeader('Cache-Control', 'public, s-maxage=1200, stale-while-revalidate=600');
    
    // 200 OK 상태와 함께 XML 데이터를 응답으로 보냅니다.
    res.status(200).send(xml);

  } catch (error: any) {
    // 오류가 발생하면 Vercel 로그에 기록하고 500 에러를 보냅니다.
    console.error('Error generating RSS feed:', error);
    res.status(500).json({ error: 'Internal Server Error', message: error.message });
  }
}