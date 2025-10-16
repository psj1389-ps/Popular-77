// Vercel Serverless Function for RSS Feed
export default function handler(req, res) {
  // Add console log to track function execution
  console.log("[RSS] handler called", new Date().toISOString());
  
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  
  // Handle preflight requests
  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }
  
  // Only allow GET requests
  if (req.method !== 'GET') {
    res.status(405).json({ error: 'Method not allowed' });
    return;
  }

  const currentDate = new Date().toUTCString();
  
  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>77-tools</title>
    <link>https://77-tools.xyz/</link>
    <description>가장 많이 사용되는 온라인 도구와 AI</description>
    <language>ko</language>
    <lastBuildDate>${currentDate}</lastBuildDate>
    <generator>77-tools RSS Generator</generator>
    <copyright>© 2025 77-tools.xyz</copyright>
    <item>
      <title>PDF를 이미지로 변환</title>
      <link>https://77-tools.xyz/tools/pdf-image</link>
      <guid>https://77-tools.xyz/tools/pdf-image</guid>
      <pubDate>${currentDate}</pubDate>
      <description><![CDATA[PDF 파일을 PNG, JPG, WEBP 등 다양한 이미지 형식으로 변환하는 도구입니다.]]></description>
      <category>PDF 변환</category>
    </item>
    <item>
      <title>PDF를 JPG로 변환</title>
      <link>https://77-tools.xyz/tools/pdf-jpg</link>
      <guid>https://77-tools.xyz/tools/pdf-jpg</guid>
      <pubDate>${currentDate}</pubDate>
      <description><![CDATA[PDF 파일을 고품질 JPG 이미지로 변환하는 전문 도구입니다.]]></description>
      <category>PDF 변환</category>
    </item>
    <item>
      <title>PDF를 PNG로 변환</title>
      <link>https://77-tools.xyz/tools/pdf-png</link>
      <guid>https://77-tools.xyz/tools/pdf-png</guid>
      <pubDate>${currentDate}</pubDate>
      <description><![CDATA[PDF 파일을 투명 배경을 지원하는 PNG 이미지로 변환하는 도구입니다.]]></description>
      <category>PDF 변환</category>
    </item>
    <item>
      <title>PDF를 GIF로 변환</title>
      <link>https://77-tools.xyz/tools/pdf-gif</link>
      <guid>https://77-tools.xyz/tools/pdf-gif</guid>
      <pubDate>${currentDate}</pubDate>
      <description><![CDATA[PDF 파일을 애니메이션 GIF로 변환하는 도구입니다.]]></description>
      <category>PDF 변환</category>
    </item>
    <item>
      <title>PDF를 SVG로 변환</title>
      <link>https://77-tools.xyz/tools/pdf-svg</link>
      <guid>https://77-tools.xyz/tools/pdf-svg</guid>
      <pubDate>${currentDate}</pubDate>
      <description><![CDATA[PDF 파일을 벡터 형식인 SVG로 변환하는 도구입니다.]]></description>
      <category>PDF 변환</category>
    </item>
    <item>
      <title>PDF를 TIFF로 변환</title>
      <link>https://77-tools.xyz/tools/pdf-tiff</link>
      <guid>https://77-tools.xyz/tools/pdf-tiff</guid>
      <pubDate>${currentDate}</pubDate>
      <description><![CDATA[PDF 파일을 고해상도 TIFF 이미지로 변환하는 도구입니다.]]></description>
      <category>PDF 변환</category>
    </item>
  </channel>
</rss>`;
  
  // Set proper headers for RSS feed
  res.setHeader("Content-Type", "application/rss+xml; charset=utf-8");
  res.setHeader("Cache-Control", "public, s-maxage=600, stale-while-revalidate=300");
  
  // Send the RSS XML
  res.status(200).send(xml);
}