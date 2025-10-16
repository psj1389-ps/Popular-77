import { VercelRequest, VercelResponse } from '@vercel/node';
import fs from 'fs';
import path from 'path';

export default function handler(req: VercelRequest, res: VercelResponse) {
  try {
    // RSS XML 파일 읽기 - Vercel 환경에서는 public 폴더가 루트에 위치
    const rssPath = path.join(process.cwd(), 'public', 'rss.xml');
    const rssContent = fs.readFileSync(rssPath, 'utf8');
    
    // 적절한 헤더 설정
    res.setHeader('Content-Type', 'application/rss+xml; charset=utf-8');
    res.setHeader('Cache-Control', 'public, max-age=3600');
    res.setHeader('Access-Control-Allow-Origin', '*');
    
    // RSS 내용 반환
    res.status(200).send(rssContent);
  } catch (error) {
    console.error('RSS 파일 읽기 오류:', error);
    res.status(500).json({ error: 'RSS 피드를 불러올 수 없습니다.' });
  }
}