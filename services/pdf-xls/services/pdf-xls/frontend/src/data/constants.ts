import { Tool, Category, FAQ, Feature, Statistic } from '../types';

// PopularTools 컴포넌트용 도구 카테고리 버튼 데이터
export const TOOL_CATEGORIES = [
  { id: 'all', name: '모든 도구', icon: 'Grid3X3' },
  { id: 'pdf', name: 'PDF변환도구', icon: 'FileText' },
  { id: 'image', name: '이미지도구', icon: 'Image' },
  { id: 'ai', name: 'AI도구', icon: 'Brain' },
  { id: 'image-transform', name: '이미지변환도구', icon: 'RefreshCw' },
  { id: 'document', name: '문서도구', icon: 'FileType' },
  { id: 'youtube', name: 'YOUTUBE도구', icon: 'Youtube' },
  { id: 'video', name: '동영상도구', icon: 'Video' },
];

// 도구 데이터
export const TOOLS: Tool[] = [
  // PDF 도구들
  {
    id: 'pdf-svg',
    name: 'PDF to SVG 변환기',
    description: 'PDF 파일을 고품질 SVG 벡터 이미지로 변환',
    category: 'pdf',
    tags: ['pdf', 'svg', 'vector', 'converter'],
    icon: 'Vector',
    featured: true,
    path: '/tools/pdf-svg'
  },
  {
    id: 'pdf-ai',
    name: 'PDF to AI 변환기',
    description: 'PDF 파일을 Adobe Illustrator AI 파일로 변환',
    category: 'pdf',
    tags: ['pdf', 'ai', 'illustrator', 'converter'],
    icon: 'FileText',
    featured: true,
    path: '/tools/pdf-ai'
  },
  {
    id: 'pdf-xls',
    name: 'PDF to XLS 변환기',
    description: 'PDF 파일을 Excel 스프레드시트로 변환',
    category: 'pdf',
    tags: ['pdf', 'xls', 'excel', 'converter'],
    icon: 'FileSpreadsheet',
    featured: true,
    path: '/tools/pdf-xls'
  },
  {
    id: 'pdf-pptx',
    name: 'PDF to PPTX 변환기',
    description: 'PDF 파일을 PowerPoint 프레젠테이션으로 변환',
    category: 'pdf',
    tags: ['pdf', 'pptx', 'powerpoint', 'converter'],
    icon: 'Presentation',
    featured: true,
    path: '/tools/pdf-pptx'
  },
  {
    id: 'pdf-converter',
    name: 'PDF 변환기',
    description: '다양한 파일 형식을 PDF로 변환하거나 PDF를 다른 형식으로 변환',
    category: 'pdf',
    tags: ['pdf', 'converter', 'document'],
    icon: 'FileText',
    featured: true,
    path: '/tools/pdf-converter'
  },
  {
    id: 'pdf-to-doc',
    name: 'PDF to DOC 변환기',
    description: 'PDF 파일을 Word 문서(DOC/DOCX)로 변환',
    category: 'pdf',
    tags: ['pdf', 'doc', 'docx', 'converter'],
    icon: 'FileText',
    featured: true,
    path: '/tools/pdf-to-doc'
  },
  {
    id: 'pdf-to-jpg',
    name: 'PDF to JPG 변환기',
    description: 'PDF 파일을 고품질 JPG 이미지로 변환',
    category: 'pdf',
    tags: ['pdf', 'jpg', 'image', 'converter'],
    icon: 'Image',
    featured: true,
    path: '/tool/pdf-to-jpg'
  },
  {
    id: 'pdf-to-bmp',
    name: 'PDF to BMP 변환기',
    description: 'PDF 파일을 고품질 BMP 이미지로 변환',
    category: 'pdf',
    tags: ['pdf', 'bmp', 'image', 'converter'],
    icon: 'Image',
    featured: true,
    path: '/tools/pdf-bmp'
  },
  {
    id: 'pdf-tiff',
    name: 'PDF → TIFF',
    description: 'PDF 파일을 고품질 TIFF 이미지로 변환',
    category: 'pdf',
    tags: ['pdf', 'tiff', 'image', 'converter'],
    icon: 'Image',
    featured: true,
    path: '/tools/pdf-tiff'
  },
  {
    id: 'pdf-to-png',
    name: 'PDF to PNG 변환기',
    description: 'PDF 파일을 고품질 PNG 이미지로 변환 (투명 배경 지원)',
    category: 'pdf',
    tags: ['pdf', 'png', 'image', 'converter', 'transparent'],
    icon: 'Image',
    featured: true,
    path: '/tools/pdf-png'
  },
  {
    id: 'pdf-to-excel',
    name: 'PDF to Excel 변환기',
    description: 'PDF 파일을 Excel 스프레드시트로 변환',
    category: 'pdf',
    tags: ['pdf', 'excel', 'xlsx', 'converter'],
    icon: 'FileSpreadsheet',
    featured: false,
    path: '/tools/pdf-to-excel'
  },
  {
    id: 'pdf-to-ppt',
    name: 'PDF to PPT 변환기',
    description: 'PDF 파일을 PowerPoint 프레젠테이션으로 변환',
    category: 'pdf',
    tags: ['pdf', 'ppt', 'pptx', 'converter'],
    icon: 'Presentation',
    featured: false,
    path: '/tools/pdf-to-ppt'
  },
  {
    id: 'pdf-merger',
    name: 'PDF 병합기',
    description: '여러 PDF 파일을 하나로 병합',
    category: 'pdf',
    tags: ['pdf', 'merge', 'combine'],
    icon: 'Combine',
    featured: false,
    path: '/tools/pdf-merger'
  },
  {
    id: 'pdf-splitter',
    name: 'PDF 분할기',
    description: 'PDF 파일을 여러 개로 분할',
    category: 'pdf',
    tags: ['pdf', 'split', 'divide'],
    icon: 'Split',
    featured: false,
    path: '/tools/pdf-splitter'
  },

  // 이미지 도구들
  {
    id: 'image-resizer',
    name: '이미지 리사이저',
    description: '이미지 크기를 조정하고 최적화',
    category: 'image',
    tags: ['image', 'resize', 'optimize'],
    icon: 'Image',
    featured: true,
    path: '/tools/image-resizer'
  },
  {
    id: 'image-compressor',
    name: '이미지 압축기',
    description: '이미지 파일 크기를 줄여 최적화',
    category: 'image',
    tags: ['image', 'compress', 'optimize'],
    icon: 'Minimize',
    featured: false,
    path: '/tools/image-compressor'
  },
  {
    id: 'image-cropper',
    name: '이미지 자르기',
    description: '이미지를 원하는 크기로 자르기',
    category: 'image',
    tags: ['image', 'crop', 'cut'],
    icon: 'Crop',
    featured: false,
    path: '/tools/image-cropper'
  },
  {
    id: 'image-filter',
    name: '이미지 필터',
    description: '이미지에 다양한 필터 효과 적용',
    category: 'image',
    tags: ['image', 'filter', 'effect'],
    icon: 'Filter',
    featured: false,
    path: '/tools/image-filter'
  },
  {
    id: 'background-remover',
    name: '배경 제거',
    description: '이미지에서 배경을 자동으로 제거',
    category: 'image',
    tags: ['image', 'background', 'remove'],
    icon: 'Eraser',
    featured: true,
    path: '/tools/background-remover'
  },

  // AI 도구들
  {
    id: 'ai-text-generator',
    name: 'AI 텍스트 생성기',
    description: 'AI를 활용한 창의적인 텍스트 생성',
    category: 'ai',
    tags: ['ai', 'text', 'generator'],
    icon: 'Brain',
    featured: true,
    path: '/tools/ai-text-generator'
  },
  {
    id: 'ai-image-generator',
    name: 'AI 이미지 생성기',
    description: '텍스트 설명으로 AI 이미지 생성',
    category: 'ai',
    tags: ['ai', 'image', 'generator'],
    icon: 'Sparkles',
    featured: true,
    path: '/tools/ai-image-generator'
  },
  {
    id: 'ai-translator',
    name: 'AI 번역기',
    description: 'AI 기반 다국어 번역 서비스',
    category: 'ai',
    tags: ['ai', 'translate', 'language'],
    icon: 'Languages',
    featured: false,
    path: '/tools/ai-translator'
  },
  {
    id: 'ai-summarizer',
    name: 'AI 요약기',
    description: '긴 텍스트를 AI로 요약',
    category: 'ai',
    tags: ['ai', 'summary', 'text'],
    icon: 'FileText',
    featured: false,
    path: '/tools/ai-summarizer'
  },

  // 이미지 변환 도구들
  {
    id: 'jpg-to-png',
    name: 'JPG to PNG 변환기',
    description: 'JPG 이미지를 PNG 형식으로 변환',
    category: 'image-transform',
    tags: ['jpg', 'png', 'convert'],
    icon: 'RefreshCw',
    featured: false,
    path: '/tools/jpg-to-png'
  },
  {
    id: 'png-to-jpg',
    name: 'PNG to JPG 변환기',
    description: 'PNG 이미지를 JPG 형식으로 변환',
    category: 'image-transform',
    tags: ['png', 'jpg', 'convert'],
    icon: 'RefreshCw',
    featured: false,
    path: '/tools/png-to-jpg'
  },
  {
    id: 'webp-converter',
    name: 'WebP 변환기',
    description: '이미지를 WebP 형식으로 변환',
    category: 'image-transform',
    tags: ['webp', 'convert', 'optimize'],
    icon: 'Zap',
    featured: false,
    path: '/tools/webp-converter'
  },
  {
    id: 'svg-converter',
    name: 'SVG 변환기',
    description: '이미지를 SVG 벡터 형식으로 변환',
    category: 'image-transform',
    tags: ['svg', 'vector', 'convert'],
    icon: 'Vector',
    featured: false,
    path: '/tools/svg-converter'
  },

  // 문서 도구들
  {
    id: 'text-formatter',
    name: '텍스트 포맷터',
    description: '텍스트를 다양한 형식으로 변환하고 정리',
    category: 'document',
    tags: ['text', 'format', 'convert'],
    icon: 'Type',
    featured: true,
    path: '/tools/text-formatter'
  },
  {
    id: 'word-counter',
    name: '단어 카운터',
    description: '텍스트의 단어, 문자, 문단 수 계산',
    category: 'document',
    tags: ['word', 'count', 'text'],
    icon: 'Hash',
    featured: false,
    path: '/tools/word-counter'
  },
  {
    id: 'markdown-editor',
    name: '마크다운 에디터',
    description: '마크다운 문서 작성 및 미리보기',
    category: 'document',
    tags: ['markdown', 'editor', 'preview'],
    icon: 'Edit',
    featured: false,
    path: '/tools/markdown-editor'
  },
  {
    id: 'doc-to-pdf',
    name: 'DOC to PDF 변환기',
    description: 'Word 문서를 PDF로 변환',
    category: 'document',
    tags: ['doc', 'pdf', 'convert'],
    icon: 'FileType',
    featured: false,
    path: '/tools/doc-to-pdf'
  },

  // YouTube 도구들
  {
    id: 'youtube-downloader',
    name: 'YouTube 다운로더',
    description: 'YouTube 동영상을 다운로드',
    category: 'youtube',
    tags: ['youtube', 'download', 'video'],
    icon: 'Download',
    featured: true,
    path: '/tools/youtube-downloader'
  },
  {
    id: 'youtube-to-mp3',
    name: 'YouTube to MP3',
    description: 'YouTube 동영상을 MP3 오디오로 변환',
    category: 'youtube',
    tags: ['youtube', 'mp3', 'audio'],
    icon: 'Music',
    featured: true,
    path: '/tools/youtube-to-mp3'
  },
  {
    id: 'youtube-thumbnail',
    name: 'YouTube 썸네일 다운로더',
    description: 'YouTube 동영상 썸네일 이미지 다운로드',
    category: 'youtube',
    tags: ['youtube', 'thumbnail', 'image'],
    icon: 'Image',
    featured: false,
    path: '/tools/youtube-thumbnail'
  },

  // 동영상 도구들
  {
    id: 'video-converter',
    name: '동영상 변환기',
    description: '동영상을 다양한 형식으로 변환',
    category: 'video',
    tags: ['video', 'convert', 'format'],
    icon: 'Video',
    featured: true,
    path: '/tools/video-converter'
  },
  {
    id: 'video-compressor',
    name: '동영상 압축기',
    description: '동영상 파일 크기를 줄여 최적화',
    category: 'video',
    tags: ['video', 'compress', 'optimize'],
    icon: 'Minimize2',
    featured: false,
    path: '/tools/video-compressor'
  },
  {
    id: 'video-trimmer',
    name: '동영상 자르기',
    description: '동영상을 원하는 길이로 자르기',
    category: 'video',
    tags: ['video', 'trim', 'cut'],
    icon: 'Scissors',
    featured: false,
    path: '/tools/video-trimmer'
  },
  {
    id: 'gif-maker',
    name: 'GIF 메이커',
    description: '동영상이나 이미지로 GIF 애니메이션 생성',
    category: 'video',
    tags: ['gif', 'animation', 'maker'],
    icon: 'Clapperboard',
    featured: false,
    path: '/tools/gif-maker'
  },

  // 기타 도구들
  {
    id: 'hash-generator',
    name: '해시 생성기',
    description: 'MD5, SHA1, SHA256 등 다양한 해시값 생성',
    category: 'document',
    tags: ['hash', 'security', 'encrypt'],
    icon: 'Shield',
    featured: true,
    path: '/tools/hash-generator'
  },
  {
    id: 'qr-generator',
    name: 'QR 코드 생성기',
    description: '텍스트나 URL을 QR 코드로 변환',
    category: 'document',
    tags: ['qr', 'code', 'generator'],
    icon: 'QrCode',
    featured: false,
    path: '/tools/qr-generator'
  },
  {
    id: 'color-picker',
    name: '컬러 피커',
    description: '색상 선택 및 다양한 색상 코드 변환',
    category: 'image',
    tags: ['color', 'picker', 'design'],
    icon: 'Palette',
    featured: false,
    path: '/tools/color-picker'
  }
];

// 카테고리 데이터 (Home 페이지용)
export const CATEGORIES: Category[] = [
  {
    id: 'pdf',
    name: 'PDF 도구',
    description: 'PDF 변환 및 편집 관련 도구들',
    icon: 'FileText',
    color: 'blue'
  },
  {
    id: 'image',
    name: '이미지 도구',
    description: '이미지 편집 및 처리 도구들',
    icon: 'Image',
    color: 'green'
  },
  {
    id: 'ai',
    name: 'AI 도구',
    description: 'AI 기반 생성 및 처리 도구들',
    icon: 'Brain',
    color: 'purple'
  },
  {
    id: 'image-transform',
    name: '이미지 변환 도구',
    description: '이미지 형식 변환 도구들',
    icon: 'RefreshCw',
    color: 'orange'
  },
  {
    id: 'document',
    name: '문서 도구',
    description: '문서 처리 및 변환 도구들',
    icon: 'FileType',
    color: 'red'
  },
  {
    id: 'youtube',
    name: 'YouTube 도구',
    description: 'YouTube 관련 다운로드 및 변환 도구들',
    icon: 'Youtube',
    color: 'red'
  },
  {
    id: 'video',
    name: '동영상 도구',
    description: '동영상 편집 및 변환 도구들',
    icon: 'Video',
    color: 'indigo'
  }
];

// 특징 데이터
export const FEATURES: Feature[] = [
  {
    id: 'secure',
    title: '🔒 안전한 처리',
    description: '모든 처리는 브라우저에서 로컬로 진행되어 데이터가 안전합니다',
    icon: 'Shield'
  },
  {
    id: 'fast',
    title: '⚡ 빠른 속도',
    description: '로컬 처리로 최적화된 빠른 성능과 속도를 제공합니다',
    icon: 'Zap'
  }
];

// 통계 데이터
export const STATISTICS: Statistic[] = [
  {
    id: 'tools',
    label: '사용 가능한 도구',
    value: '99+',
    description: '다양한 온라인 유틸리티'
  },
  {
    id: 'processing',
    label: '로컬 처리',
    value: '100%',
    description: '브라우저에서 안전하게'
  },
  {
    id: 'access',
    label: '24시간 접근',
    value: '24/7',
    description: '언제든지 사용 가능'
  },
  {
    id: 'cost',
    label: '현재 비용',
    value: '$0',
    description: '완전 무료 서비스'
  }
];

// FAQ 데이터
export const FAQS: FAQ[] = [
  {
    id: 'free',
    question: '정말 무료로 사용할 수 있나요?',
    answer: '네! 저희 도구들은 현재 회원가입 없이 기본 사용에 대해 무료로 제공됩니다. 필수 유틸리티를 접근 가능하게 유지하는 것이 목표입니다.',
    category: 'general'
  },
  {
    id: 'security',
    question: '제 데이터는 얼마나 안전한가요?',
    answer: '저희 도구들은 가능한 한 브라우저에서 로컬로 파일을 처리하도록 설계되었습니다. 개인 데이터를 저장하거나 전송하지 않는 것을 목표로 합니다. 자세한 내용은 개인정보 보호정책을 참조하세요.',
    category: 'security'
  },
  {
    id: 'tools',
    question: '어떤 종류의 도구를 제공하나요?',
    answer: '파일 변환기(PDF, 이미지), 해시 생성기, 텍스트 처리기, 이미지 편집기 등 필수 유틸리티를 제공합니다. 위의 전체 컬렉션을 탐색하거나 소개 페이지에서 자세한 내용을 확인하세요.',
    category: 'tools'
  },
  {
    id: 'account',
    question: '계정을 만들어야 하나요?',
    answer: '계정이 필요하지 않습니다! 어떤 도구 페이지든 방문해서 즉시 사용을 시작하세요. 가능한 한 마찰 없이 도구를 설계했습니다.',
    category: 'general'
  },
  {
    id: 'request',
    question: '새로운 도구나 기능을 요청할 수 있나요?',
    answer: '물론입니다! 사용자 피드백을 바탕으로 유용한 도구를 추가하는 것을 항상 고려하고 있습니다. 제안 사항이 있으시면 연락해 주시면 향후 릴리스에서 고려하겠습니다.',
    category: 'features'
  },
  {
    id: 'filesize',
    question: '어떤 파일 크기가 가장 잘 작동하나요?',
    answer: '저희 도구들은 대부분의 일반적인 파일 크기를 효율적으로 처리하도록 최적화되어 있습니다. 처리가 브라우저에서 이루어지므로 성능은 기기의 성능에 따라 달라지며, 다양한 크기의 파일로 작업할 수 있습니다.',
    category: 'technical'
  }
];


// ... (FEATURES, FAQS, STATISTICS 등 기존 코드)
