# 글자수 및 변환기 - Replit 배포 가이드

## 🚀 Replit에서 실행하기

### 빠른 시작

1. **Fork 하기**: 오른쪽 상단의 'Fork' 버튼을 클릭하여 프로젝트를 자신의 Replit 계정으로 복제합니다.
2. **자동 설치**: Replit은 `.replit` 및 `replit.nix` 파일을 읽고 필요한 의존성을 자동으로 설치합니다.
3. **실행하기**: 상단의 'Run' 버튼을 클릭하면 자동으로 `npm run dev` 명령이 실행됩니다.
4. **접속하기**: 오른쪽 패널에 웹뷰가 표시되며, 외부 URL로도 접근할 수 있습니다.

### 수동 설정 (필요한 경우)

```bash
# 의존성 설치
npm install

# 개발 서버 실행
npm run dev
```

## 📋 프로젝트 정보

### 주요 기능

- **텍스트 분석**: 글자수, 단어수, 문장수, 문단수, 읽기 시간 계산
- **텍스트 변환**: 대/소문자 변환, 첫 글자 대문자, 공백 제거 등
- **실시간 분석**: 입력과 동시에 즉시 분석 결과 확인
- **반응형 디자인**: 모든 디바이스에서 최적화된 사용자 경험

### 기술 스택

- **Frontend**: Next.js 14, React 18
- **상태 관리**: MobX State Tree
- **스타일링**: Tailwind CSS
- **언어**: JavaScript (ES6+)

## 🔧 Replit 환경 설정

### 환경 변수 (필요한 경우)

프로젝트에 환경 변수가 필요한 경우, Replit의 'Secrets' 탭에서 설정할 수 있습니다:

1. 왼쪽 패널에서 'Secrets' 탭 선택
2. 'New Secret' 버튼 클릭
3. 키와 값 입력 후 저장

### 포트 설정

이 프로젝트는 기본적으로 3000번 포트를 사용합니다. Replit은 이 포트를 자동으로 외부에 노출시킵니다.

## 🌐 배포 옵션

### 지속적 배포

Replit에서는 다음과 같은 방법으로 지속적 배포를 설정할 수 있습니다:

1. GitHub 저장소와 연결
2. 변경사항 발생 시 자동 배포 설정

### 커스텀 도메인 설정

Replit Deployments를 통해 커스텀 도메인을 설정할 수 있습니다:

1. 'Deployments' 탭으로 이동
2. 'Connect Domain' 선택
3. 안내에 따라 DNS 설정 구성

## 📚 추가 자료

- [Replit 공식 문서](https://docs.replit.com/)
- [Next.js 문서](https://nextjs.org/docs)
- [MobX State Tree 문서](https://mobx-state-tree.js.org/)

## 🤝 기여하기

1. 이 프로젝트를 Fork합니다
2. 새로운 기능 브랜치를 생성합니다 (`git checkout -b feature/amazing-feature`)
3. 변경사항을 커밋합니다 (`git commit -m 'Add some amazing feature'`)
4. 브랜치에 Push합니다 (`git push origin feature/amazing-feature`)
5. Pull Request를 생성합니다

## 📄 라이선스

© 2024 글자수 및 변환기. 실시간 텍스트 분석 도구

---

**개발자**: AI Assistant  
**버전**: 1.0.0  
**최종 업데이트**: 2024년 12월