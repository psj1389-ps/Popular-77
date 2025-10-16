export default function handler(req, res) {
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
      <title>PDF를 JPG로 변환</title>
      <link>https://77-tools.xyz/tools/pdf-jpg</link>
      <guid>https://77-tools.xyz/tools/pdf-jpg</guid>
      <pubDate>${new Date().toUTCString()}</pubDate>
      <description><![CDATA[PDF 파일을 고품질 JPG 이미지로 변환하는 전문 도구입니다.]]></description>
      <category>PDF 변환</category>
    </item>
    <item>
      <title>PDF를 PNG로 변환</title>
      <link>https://77-tools.xyz/tools/pdf-png</link>
      <guid>https://77-tools.xyz/tools/pdf-png</guid>
      <pubDate>${new Date().toUTCString()}</pubDate>
      <description><![CDATA[PDF 파일을 투명 배경을 지원하는 PNG 이미지로 변환하는 도구입니다.]]></description>
      <category>PDF 변환</category>
    </item>
    <item>
      <title>PDF를 GIF로 변환</title>
      <link>https://77-tools.xyz/tools/pdf-gif</link>
      <guid>https://77-tools.xyz/tools/pdf-gif</guid>
      <pubDate>${new Date().toUTCString()}</pubDate>
      <description><![CDATA[PDF 파일을 애니메이션 GIF로 변환하는 도구입니다.]]></description>
      <category>PDF 변환</category>
    </item>
    <item>
      <title>PDF를 SVG로 변환</title>
      <link>https://77-tools.xyz/tools/pdf-svg</link>
      <guid>https://77-tools.xyz/tools/pdf-svg</guid>
      <pubDate>${new Date().toUTCString()}</pubDate>
      <description><![CDATA[PDF 파일을 벡터 형식인 SVG로 변환하는 도구입니다.]]></description>
      <category>PDF 변환</category>
    </item>
    <item>
      <title>PDF를 TIFF로 변환</title>
      <link>https://77-tools.xyz/tools/pdf-tiff</link>
      <guid>https://77-tools.xyz/tools/pdf-tiff</guid>
      <pubDate>${new Date().toUTCString()}</pubDate>
      <description><![CDATA[PDF 파일을 고해상도 TIFF 이미지로 변환하는 도구입니다.]]></description>
      <category>PDF 변환</category>
    </item>
  </channel>
</rss>`;
  
  res.setHeader("Content-Type", "application/rss+xml; charset=utf-8");
  res.setHeader("Cache-Control", "public, s-maxage=600, stale-while-revalidate=300");
  return res.status(200).send(xml);
}