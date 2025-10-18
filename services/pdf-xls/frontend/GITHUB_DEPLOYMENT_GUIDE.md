# GitHub 배포 가이드

Popular-77 프로젝트를 GitHub에 배포하고 Vercel과 연동하는 완전한 가이드입니다.

## 🚀 1단계: GitHub 저장소 생성

### 1.1 GitHub에서 새 저장소 생성
1. [GitHub](https://github.com)에 로그인
2. 우상단의 "+" 버튼 클릭 → "New repository" 선택
3. 저장소 설정:
   - **Repository name**: `Popular-77`
   - **Description**: `PDF 변환 도구 모음 - React + TypeScript + Vite`
   - **Visibility**: Public (또는 Private)
   - **Initialize this repository with**: 체크하지 않음 (이미 로컬에 코드가 있으므로)
4. "Create repository" 클릭

### 1.2 로컬 Git 저장소와 GitHub 연결

현재 프로젝트는 이미 Git이 초기화되어 있고 커밋도 완료된 상태입니다.

```bash
# GitHub 원격 저장소 추가
git remote add origin https://github.com/psj1389-ps/Popular-77.git

# 기본 브랜치를 main으로 변경 (권장)
git branch -M main

# GitHub에 코드 푸시
git push -u origin main
```

## 🌐 2단계: Vercel 배포

### 2.1 Vercel 계정 준비
1. [Vercel](https://vercel.com)에 가입/로그인
2. GitHub 계정으로 로그인하는 것을 권장

### 2.2 프로젝트 가져오기
1. Vercel 대시보드에서 "New Project" 클릭
2. "Import Git Repository" 섹션에서 GitHub 연결
3. `Popular-77` 저장소 선택
4. "Import" 클릭

### 2.3 프로젝트 설정
Vercel이 자동으로 감지하는 설정:
- **Framework Preset**: Vite
- **Root Directory**: `./` (프로젝트 루트)
- **Build Command**: `npm run build`
- **Output Directory**: `dist`
- **Install Command**: `npm install`

**중요**: Root Directory를 `frontend`로 설정해야 합니다!

### 2.4 환경변수 설정 (선택사항)
만약 백엔드 API와 연동이 필요한 경우:

1. "Environment Variables" 섹션에서 추가:
```
VITE_API_URL=https://your-backend-api.com
VITE_PDF_SERVICE_URL=https://your-pdf-service.com
```

### 2.5 배포 실행
1. "Deploy" 버튼 클릭
2. 배포 완료까지 대기 (약 2-3분)
3. 배포 완료 후 제공되는 URL 확인

## 🔄 3단계: 자동 배포 설정

GitHub와 Vercel이 연결되면 자동으로:
- **main 브랜치 푸시** → 프로덕션 배포
- **다른 브랜치 푸시** → 프리뷰 배포
- **Pull Request** → 프리뷰 URL 자동 생성

## 📋 4단계: 배포 후 확인사항

### 4.1 기본 기능 테스트
- [ ] 홈페이지 정상 로딩
- [ ] 페이지 간 라우팅 동작
- [ ] 반응형 디자인 확인
- [ ] 브라우저 콘솔 에러 확인

### 4.2 PDF 변환 기능 테스트
- [ ] PDF to JPG 변환 테스트
- [ ] PDF to DOC 변환 테스트
- [ ] 파일 업로드/다운로드 기능
- [ ] 에러 처리 확인

## 🛠️ 5단계: 문제 해결

### 빌드 실패 시
```bash
# 로컬에서 빌드 테스트
npm run build

# TypeScript 에러 확인
npm run type-check
```

### 라우팅 문제 시
- `vercel.json`의 rewrites 설정 확인
- SPA 라우팅 설정이 올바른지 확인

### API 연결 문제 시
- 환경변수 설정 확인
- CORS 설정 확인
- 백엔드 서버 상태 확인

## 📊 현재 프로젝트 상태

✅ **완료된 설정:**
- Git 저장소 초기화 및 커밋
- TypeScript 설정 및 빌드 최적화
- Vercel 배포 설정 (`vercel.json`)
- 프로젝트 문서화 (README.md)
- 배포 가이드 작성

✅ **빌드 테스트 통과:**
- 모든 TypeScript 에러 해결
- 성공적인 프로덕션 빌드 확인
- 번들 크기 최적화 완료

## 🎯 다음 단계

1. **GitHub 저장소 생성** 후 위의 명령어로 코드 푸시
2. **Vercel에서 프로젝트 가져오기**
3. **Root Directory를 `frontend`로 설정**
4. **배포 완료 후 기능 테스트**

## 📞 지원

배포 과정에서 문제가 발생하면:
- [Vercel 문서](https://vercel.com/docs)
- [GitHub 문서](https://docs.github.com/)
- 프로젝트 Issues 페이지

---

**🎉 축하합니다!** 
모든 설정이 완료되어 있어 배포 과정이 매우 순조로울 것입니다. 
배포 후에는 전 세계 어디서나 PDF 변환 도구에 접근할 수 있습니다!