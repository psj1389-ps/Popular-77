import fs from "fs";
import path from "path";

function rfc822(date = new Date()) {
  return date.toUTCString();
}

function buildRss({ site, items }) {
  const channel = `
<channel>
  <title>${site.title}</title>
  <link>${site.url}</link>
  <description>${site.description}</description>
  <language>ko</language>
  <lastBuildDate>${rfc822()}</lastBuildDate>
  <generator>77-tools RSS Generator</generator>
  <copyright>© 2024 77-tools.xyz</copyright>
  <image>
    <url>https://77-tools.xyz/icons/icon-192x192.png</url>
    <title>${site.title}</title>
    <link>${site.url}</link>
  </image>
${items.map(it => `  <item>
    <title>${it.title}</title>
    <link>${it.link}</link>
    <guid>${it.link}</guid>
    <pubDate>${rfc822(new Date(it.date))}</pubDate>
    <description><![CDATA[${it.description || ""}]]></description>
    <category>${it.category || "도구"}</category>
  </item>`).join("")}
</channel>`.trim();
  
  return `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
${channel}
</rss>
`;
}

const site = {
  title: "77-tools",
  url: "https://77-tools.xyz/",
  description: "가장 많이 사용되는 온라인 도구와 AI"
};

// 77-tools.xyz의 실제 도구들을 기반으로 RSS 아이템 생성
const items = [
  {
    title: "PDF to DOCX 변환기",
    link: "https://77-tools.xyz/pdf-to-docx",
    date: "2024-01-15",
    description: "PDF 파일을 Microsoft Word DOCX 형식으로 빠르고 정확하게 변환하세요. 무료 온라인 도구로 간편하게 문서를 편집 가능한 형태로 변환할 수 있습니다.",
    category: "PDF 변환"
  },
  {
    title: "PDF to PPTX 변환기",
    link: "https://77-tools.xyz/pdf-to-pptx",
    date: "2024-01-15",
    description: "PDF 파일을 PowerPoint PPTX 형식으로 변환하여 프레젠테이션을 쉽게 편집하고 수정하세요. 고품질 변환을 보장합니다.",
    category: "PDF 변환"
  },
  {
    title: "PDF to Excel 변환기",
    link: "https://77-tools.xyz/pdf-to-excel",
    date: "2024-01-15",
    description: "PDF 파일의 표와 데이터를 Excel 스프레드시트로 변환하세요. 데이터 분석과 편집이 용이한 형태로 변환됩니다.",
    category: "PDF 변환"
  },
  {
    title: "PDF to JPG 변환기",
    link: "https://77-tools.xyz/pdf-to-jpg",
    date: "2024-01-15",
    description: "PDF 페이지를 고품질 JPG 이미지로 변환하세요. 각 페이지를 개별 이미지 파일로 저장할 수 있습니다.",
    category: "PDF 변환"
  },
  {
    title: "PDF to PNG 변환기",
    link: "https://77-tools.xyz/pdf-to-png",
    date: "2024-01-15",
    description: "PDF를 투명 배경을 지원하는 PNG 이미지로 변환하세요. 웹사이트나 디자인 작업에 최적화된 형식입니다.",
    category: "PDF 변환"
  },
  {
    title: "PDF to SVG 변환기",
    link: "https://77-tools.xyz/pdf-to-svg",
    date: "2024-01-15",
    description: "PDF를 확대/축소해도 품질이 유지되는 벡터 형식인 SVG로 변환하세요. 웹 개발과 그래픽 디자인에 이상적입니다.",
    category: "PDF 변환"
  },
  {
    title: "PDF to TIFF 변환기",
    link: "https://77-tools.xyz/pdf-to-tiff",
    date: "2024-01-15",
    description: "PDF를 고품질 TIFF 이미지로 변환하세요. 인쇄 및 아카이브 목적에 적합한 무손실 압축 형식입니다.",
    category: "PDF 변환"
  },
  {
    title: "PDF to BMP 변환기",
    link: "https://77-tools.xyz/pdf-to-bmp",
    date: "2024-01-15",
    description: "PDF를 BMP 비트맵 이미지로 변환하세요. Windows 환경에서 널리 사용되는 표준 이미지 형식입니다.",
    category: "PDF 변환"
  },
  {
    title: "PDF to GIF 변환기",
    link: "https://77-tools.xyz/pdf-to-gif",
    date: "2024-01-15",
    description: "PDF를 GIF 이미지로 변환하세요. 웹에서 빠른 로딩과 호환성을 제공하는 형식입니다.",
    category: "PDF 변환"
  },
  {
    title: "PDF to AI 변환기",
    link: "https://77-tools.xyz/pdf-to-ai",
    date: "2024-01-15",
    description: "PDF를 Adobe Illustrator AI 형식으로 변환하여 전문적인 벡터 편집이 가능하도록 하세요.",
    category: "PDF 변환"
  },
  {
    title: "PDF to Image 변환기",
    link: "https://77-tools.xyz/pdf-to-image",
    date: "2024-01-15",
    description: "PDF를 다양한 이미지 형식으로 변환하세요. JPG, PNG, TIFF 등 원하는 형식을 선택할 수 있습니다.",
    category: "PDF 변환"
  },
  {
    title: "PDF to Vector 변환기",
    link: "https://77-tools.xyz/pdf-to-vector",
    date: "2024-01-15",
    description: "PDF를 편집 가능한 벡터 형식으로 변환하세요. SVG, AI 등의 벡터 형식을 지원합니다.",
    category: "PDF 변환"
  }
];

const xml = buildRss({ site, items });
const outDir = path.join(process.cwd(), "public");
fs.mkdirSync(outDir, { recursive: true });
fs.writeFileSync(path.join(outDir, "rss.xml"), xml, "utf8");
console.log("✅ generated public/rss.xml");