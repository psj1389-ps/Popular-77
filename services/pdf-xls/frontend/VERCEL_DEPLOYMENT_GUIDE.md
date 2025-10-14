# 배포 가이드 (Deployment Guide)

이 가이드는 프론트엔드 프로젝트를 GitHub과 Vercel에 배포하는 방법을 설명합니다.

## 📋 사전 준비사항

- [Git](https://git-scm.com/) 설치
- [GitHub](https://github.com/) 계정
- [Vercel](https://vercel.com/) 계정
- Node.js 18+ 설치

## 🚀 1단계: GitHub에 프로젝트 업로드

### 1.1 GitHub 저장소 생성
1. GitHub에 로그인
2. 새 저장소(Repository) 생성
3. 저장소 이름 입력 (예: `popular-77-frontend`)
4. Public 또는 Private 선택
5. "Create repository" 클릭

### 1.2 로컬 프로젝트를 GitHub에 푸시

```bash
# 원격 저장소 추가
git remote add origin https://github.com/psj1389-ps/Popular-77.git

# 기본 브랜치를 main으로 설정
git branch -M main

# GitHub에 푸시
git push -u origin main
```

## 🌐 2단계: Vercel에 배포

### 2.1 Vercel에서 프로젝트 가져오기
1. [Vercel](https://vercel.com/)에 로그인
2. "New Project" 클릭
3. GitHub 계정 연결 (처음 사용시)
4. 방금 생성한 저장소 선택
5. "Import" 클릭

### 2.2 프로젝트 설정
Vercel이 자동으로 다음 설정을 감지합니다:
- **Framework Preset**: Vite
- **Build Command**: `npm run build`
- **Output Directory**: `dist`
- **Install Command**: `npm install`

### 2.3 환경변수 설정 (필요시)
만약 백엔드 API URL이나 기타 환경변수가 필요한 경우:

1. Vercel 프로젝트 대시보드에서 "Settings" 탭 클릭
2. "Environment Variables" 섹션으로 이동
3. 필요한 환경변수 추가:
   ```
   VITE_API_URL=https://your-backend-api.com
   ```

### 2.4 배포 완료
1. "Deploy" 버튼 클릭
2. 배포 완료까지 대기 (보통 1-3분)
3. 배포된 URL 확인 (예: `https://your-project.vercel.app`)

## 🔄 3단계: 자동 배포 설정

Vercel은 GitHub와 연결되어 있어 다음과 같이 자동 배포됩니다:

- **main 브랜치에 푸시**: 프로덕션 배포
- **다른 브랜치에 푸시**: 프리뷰 배포

## 📁 4단계: 프로젝트 구조 확인

현재 프로젝트는 다음과 같이 구성되어 있습니다:

```
frontend/
├── src/
│   ├── components/     # 재사용 가능한 컴포넌트
│   ├── pages/         # 페이지 컴포넌트
│   ├── data/          # 상수 및 데이터
│   ├── types/         # TypeScript 타입 정의
│   └── hooks/         # 커스텀 훅
├── public/            # 정적 파일
├── dist/              # 빌드 결과물 (자동 생성)
├── package.json       # 프로젝트 설정
├── vercel.json        # Vercel 배포 설정
└── vite.config.ts     # Vite 설정
```

## 🛠️ 5단계: 추가 설정 (선택사항)

### 5.1 커스텀 도메인 설정
1. Vercel 프로젝트 대시보드에서 "Settings" → "Domains"
2. 원하는 도메인 입력
3. DNS 설정 완료

### 5.2 성능 최적화
현재 `vercel.json`에 다음 최적화가 적용되어 있습니다:
- SPA 라우팅 지원
- CORS 헤더 설정
- 빌드 최적화

### 5.3 백엔드 API 연결
현재 `package.json`에 프록시 설정이 되어 있습니다:
```json
"proxy": "http://localhost:5000"
```

프로덕션에서는 환경변수를 통해 API URL을 설정하세요.

## 🔧 문제 해결

### 빌드 오류 발생시
```bash
# 로컬에서 빌드 테스트
npm run build

# 타입 체크
npm run check
```

### 배포 실패시
1. Vercel 대시보드에서 빌드 로그 확인
2. 환경변수 설정 확인
3. `vercel.json` 설정 확인

## 📞 지원

배포 과정에서 문제가 발생하면:
- [Vercel 문서](https://vercel.com/docs)
- [GitHub 문서](https://docs.github.com/)
- 프로젝트 이슈 트래커

## 🎉 완료!

축하합니다! 프론트엔드 프로젝트가 성공적으로 배포되었습니다.

- **GitHub 저장소**: 코드 관리 및 협업
- **Vercel 배포**: 자동 배포 및 호스팅
- **PDF-to-JPG 도구**: 완전히 작동하는 변환 도구

이제 전 세계 어디서나 여러분의 도구에 접근할 수 있습니다!