import fs from 'fs';
import path from 'path';
import { Feed } from 'feed';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// 77-tools.xyz 프로젝트의 도구 목록을 가져오는 함수
async function getAllPosts() {
  // 실제 프로젝트의 도구 데이터를 기반으로 RSS 아이템 생성
  const tools = [
    // PDF 변환 도구들
    {
      slug: 'pdf-to-png',
      title: 'PDF to PNG 변환기',
      date: '2025-01-15',
      summary: 'PDF 파일을 고품질 PNG 이미지로 변환합니다. 투명 배경 지원으로 더욱 깔끔한 결과물을 얻을 수 있습니다.',
      category: 'PDF 변환',
      path: '/tools/pdf-png'
    },
    {
      slug: 'pdf-to-jpg',
      title: 'PDF to JPG 변환기',
      date: '2025-01-14',
      summary: 'PDF 파일을 고품질 JPG 이미지로 변환합니다. 빠르고 안정적인 변환 서비스를 제공합니다.',
      category: 'PDF 변환',
      path: '/tool/pdf-to-jpg'
    },
    {
      slug: 'pdf-to-doc',
      title: 'PDF to DOC 변환기',
      date: '2025-01-13',
      summary: 'PDF 파일을 Word 문서(DOC/DOCX)로 변환합니다. 편집 가능한 문서 형태로 변환하여 작업 효율성을 높입니다.',
      category: 'PDF 변환',
      path: '/tools/pdf-to-doc'
    },
    {
      slug: 'pdf-to-excel',
      title: 'PDF to Excel 변환기',
      date: '2025-01-12',
      summary: 'PDF 파일을 Excel 스프레드시트로 변환합니다. 표 데이터를 정확하게 추출하여 분석 작업에 활용할 수 있습니다.',
      category: 'PDF 변환',
      path: '/tools/pdf-xls'
    },
    {
      slug: 'pdf-to-pptx',
      title: 'PDF to PPTX 변환기',
      date: '2025-01-11',
      summary: 'PDF 파일을 PowerPoint 프레젠테이션으로 변환합니다. 프레젠테이션 자료 제작에 유용합니다.',
      category: 'PDF 변환',
      path: '/tools/pdf-pptx'
    },
    {
      slug: 'pdf-to-svg',
      title: 'PDF to SVG 변환기',
      date: '2025-01-10',
      summary: 'PDF 파일을 고품질 SVG 벡터 이미지로 변환합니다. 확대해도 깨지지 않는 벡터 형식으로 변환합니다.',
      category: 'PDF 변환',
      path: '/tools/pdf-svg'
    },
    {
      slug: 'pdf-to-ai',
      title: 'PDF to AI 변환기',
      date: '2025-01-09',
      summary: 'PDF 파일을 Adobe Illustrator AI 파일로 변환합니다. 디자인 작업에 최적화된 형식으로 변환합니다.',
      category: 'PDF 변환',
      path: '/tools/pdf-ai'
    },
    {
      slug: 'pdf-to-bmp',
      title: 'PDF to BMP 변환기',
      date: '2025-01-08',
      summary: 'PDF 파일을 고품질 BMP 이미지로 변환합니다. 무손실 이미지 형식으로 변환하여 품질을 보장합니다.',
      category: 'PDF 변환',
      path: '/tools/pdf-bmp'
    },
    {
      slug: 'pdf-to-tiff',
      title: 'PDF to TIFF 변환기',
      date: '2025-01-07',
      summary: 'PDF 파일을 고품질 TIFF 이미지로 변환합니다. 인쇄용 고품질 이미지 형식으로 변환합니다.',
      category: 'PDF 변환',
      path: '/tools/pdf-tiff'
    },
    {
      slug: 'pdf-to-gif',
      title: 'PDF to GIF 변환기',
      date: '2025-01-06',
      summary: 'PDF 파일을 GIF 애니메이션으로 변환합니다. 다중 페이지 PDF를 애니메이션으로 표현할 수 있습니다.',
      category: 'PDF 변환',
      path: '/tools/pdf-gif'
    },
    {
      slug: 'pdf-to-image',
      title: 'PDF to Image 변환기',
      date: '2025-01-05',
      summary: 'PDF 파일을 다양한 이미지 형식으로 변환합니다. PNG, JPG, BMP, TIFF, GIF 등 원하는 형식을 선택할 수 있습니다.',
      category: 'PDF 변환',
      path: '/tools/pdf-image'
    },
    {
      slug: 'pdf-to-vector',
      title: 'PDF to Vector 변환기',
      date: '2025-01-04',
      summary: 'PDF 파일을 다양한 벡터 형식으로 변환합니다. SVG, AI 등 벡터 형식으로 변환하여 디자인 작업에 활용할 수 있습니다.',
      category: 'PDF 변환',
      path: '/tools/pdf-vector'
    },
    // 이미지 도구들
    {
      slug: 'image-resizer',
      title: '이미지 리사이저',
      date: '2025-01-03',
      summary: '이미지 크기를 조정하고 최적화합니다. 다양한 크기로 일괄 변환하여 웹사이트나 앱에 최적화된 이미지를 생성할 수 있습니다.',
      category: '이미지 도구',
      path: '/tools/image-resizer'
    },
    {
      slug: 'background-remover',
      title: '배경 제거 도구',
      date: '2025-01-02',
      summary: '이미지에서 배경을 자동으로 제거합니다. AI 기술을 활용하여 정확하고 깔끔한 배경 제거 결과를 제공합니다.',
      category: '이미지 도구',
      path: '/tools/background-remover'
    }
  ];

  // 날짜순으로 정렬 (최신순)
  return tools.sort((a, b) => new Date(b.date) - new Date(a.date));
}

async function generateRssFeed() {
  const posts = await getAllPosts();
  const siteURL = 'https://77-tools.xyz'; // 웹사이트 주소
  const publicDir = path.join(process.cwd(), 'public'); // public 폴더 경로

  const feed = new Feed({
    title: '77-tools - PDF 변환 및 이미지 도구', // 웹사이트 이름
    description: '다양한 PDF 변환 도구와 이미지 편집 도구를 제공합니다. PDF를 이미지, 문서, 벡터 형식으로 변환하고 이미지를 편집할 수 있는 온라인 도구 모음입니다.', // 웹사이트 설명
    id: siteURL,
    link: siteURL,
    language: 'ko', // 한국어
    copyright: `All rights reserved ${new Date().getFullYear()}, 77-tools`,
    author: {
      name: '77-tools',
      email: 'contact@77-tools.xyz',
      link: siteURL,
    },
    feedLinks: {
      rss2: `${siteURL}/rss.xml`,
    },
    image: `${siteURL}/icons/77-popular-tools.svg`,
    favicon: `${siteURL}/icons/favicon.svg`,
    generator: '77-tools RSS Generator',
  });

  posts.forEach(post => {
    feed.addItem({
      title: post.title,
      id: `${siteURL}${post.path}`, // 도구의 고유 주소
      link: `${siteURL}${post.path}`,
      description: post.summary,
      content: `<p>${post.summary}</p><p>카테고리: ${post.category}</p><p><a href="${siteURL}${post.path}">지금 사용해보기 →</a></p>`,
      date: new Date(post.date),
      category: [
        {
          name: post.category,
          domain: siteURL
        }
      ],
    });
  });

  // public 폴더에 rss.xml 파일 생성
  // public 폴더의 파일은 빌드 시 dist 폴더로 그대로 복사됩니다.
  if (!fs.existsSync(publicDir)) {
    fs.mkdirSync(publicDir, { recursive: true });
  }
  
  fs.writeFileSync(path.join(publicDir, 'rss.xml'), feed.rss2());
  console.log('✅ RSS feed generated successfully at public/rss.xml');
  console.log(`📊 Generated ${posts.length} RSS items`);
  console.log(`🔗 RSS URL: ${siteURL}/rss.xml`);
}

// 스크립트 실행
generateRssFeed().catch(error => {
  console.error('❌ Error generating RSS feed:', error);
  process.exit(1);
});