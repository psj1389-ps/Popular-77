# Popular-77 - PDF 변환 도구 모음

Popular-77은 PDF 파일을 다양한 형식으로 변환할 수 있는 웹 애플리케이션입니다. React + TypeScript + Vite로 구축된 현대적인 프론트엔드와 Python 기반의 백엔드 서비스를 제공합니다.

## 🚀 주요 기능

- **PDF to JPG**: PDF 파일을 고품질 JPG 이미지로 변환
- **PDF to DOC**: PDF 파일을 편집 가능한 Word 문서로 변환
- **반응형 디자인**: 모든 디바이스에서 최적화된 사용자 경험
- **실시간 변환**: 빠르고 안정적인 파일 변환 서비스

## 🛠️ 기술 스택

### Frontend
- **React 18** - 사용자 인터페이스
- **TypeScript** - 타입 안전성
- **Vite** - 빠른 개발 환경
- **Tailwind CSS** - 유틸리티 기반 스타일링
- **Lucide React** - 아이콘 라이브러리
- **React Router** - 클라이언트 사이드 라우팅

### Backend
- **Python Flask** - API 서버
- **PDF2Image** - PDF 변환 라이브러리
- **Tesseract OCR** - 텍스트 인식

## 📦 설치 및 실행

### 프론트엔드 설정

```bash
# 의존성 설치
npm install

# 개발 서버 실행
npm run dev

# 프로덕션 빌드
npm run build

# 빌드 미리보기
npm run preview
```

### 백엔드 서비스

```bash
# Python 가상환경 생성
python -m venv venv

# 가상환경 활성화 (Windows)
venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 서버 실행
python app.py
```

## 🌐 배포

### Vercel 배포 (프론트엔드)

1. GitHub에 코드 푸시
2. [Vercel](https://vercel.com)에서 프로젝트 가져오기
3. 자동 배포 설정 완료

자세한 배포 가이드는 [VERCEL_DEPLOYMENT_GUIDE.md](./VERCEL_DEPLOYMENT_GUIDE.md)를 참조하세요.

### 백엔드 배포

백엔드 서비스는 Render, Railway, 또는 기타 Python 호스팅 서비스에 배포할 수 있습니다.

## 📁 프로젝트 구조

```
frontend/
├── src/
│   ├── components/     # 재사용 가능한 컴포넌트
│   ├── pages/         # 페이지 컴포넌트
│   ├── data/          # 상수 및 데이터
│   ├── types/         # TypeScript 타입 정의
│   └── hooks/         # 커스텀 훅
├── public/            # 정적 파일
└── dist/              # 빌드 결과물
```

## 🤝 기여하기

1. 이 저장소를 포크합니다
2. 새로운 기능 브랜치를 생성합니다 (`git checkout -b feature/amazing-feature`)
3. 변경사항을 커밋합니다 (`git commit -m 'Add some amazing feature'`)
4. 브랜치에 푸시합니다 (`git push origin feature/amazing-feature`)
5. Pull Request를 생성합니다

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 📞 지원

문제가 발생하거나 질문이 있으시면 [Issues](https://github.com/psj1389-ps/Popular-77/issues)에서 문의해 주세요.
