import type { VercelRequest, VercelResponse } from '@vercel/node';

export default function handler(req: VercelRequest, res: VercelResponse) {
  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>77-tools</title>
    <link>https://77-tools.xyz/</link>
    <description>가장 많이 사용되는 온라인 도구와 AI</description>
    <language>ko</language>
    <lastBuildDate>${new Date().toUTCString()}</lastBuildDate>
    <generator>77-tools RSS Generator</generator>
    <copyright>© 2025 77-tools.xyz</copyright>
    <item>
      <title>PDF를 이미지로 변환</title>
      <link>https://77-tools.xyz/tools/pdf-image</link>
      <guid>https://77-tools.xyz/tools/pdf-image</guid>
      <pubDate>${new Date().toUTCString()}</pubDate>
      <description><![CDATA[PDF 파일을 PNG, JPG, WEBP 등 다양한 이미지 형식으로 변환하는 도구입니다.]]></description>
      <category>PDF 변환</category>
    </item>
    <item>
      <title>이미지를 PDF로 변환</title>
      <link>https://77-tools.xyz/tools/image-pdf</link>
      <guid>https://77-tools.xyz/tools/image-pdf</guid>
      <pubDate>${new Date().toUTCString()}</pubDate>
      <description><![CDATA[여러 이미지 파일을 하나의 PDF 문서로 결합하는 도구입니다.]]></description>
      <category>PDF 변환</category>
    </item>
    <item>
      <title>PDF 병합</title>
      <link>https://77-tools.xyz/tools/pdf-merge</link>
      <guid>https://77-tools.xyz/tools/pdf-merge</guid>
      <pubDate>${new Date().toUTCString()}</pubDate>
      <description><![CDATA[여러 PDF 파일을 하나로 병합하는 도구입니다.]]></description>
      <category>PDF 편집</category>
    </item>
    <item>
      <title>PDF 분할</title>
      <link>https://77-tools.xyz/tools/pdf-split</link>
      <guid>https://77-tools.xyz/tools/pdf-split</guid>
      <pubDate>${new Date().toUTCString()}</pubDate>
      <description><![CDATA[PDF 파일을 페이지별로 분할하는 도구입니다.]]></description>
      <category>PDF 편집</category>
    </item>
  </channel>
</rss>`;
  
  res.setHeader("Content-Type", "application/rss+xml; charset=utf-8");
  res.setHeader("Cache-Control", "public, s-maxage=600, stale-while-revalidate=300");
  res.status(200).send(xml);
}