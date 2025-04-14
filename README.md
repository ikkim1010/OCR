# OCR Document Scanner

문서를 스캔하고 OCR을 통해 텍스트를 추출하는 웹 애플리케이션입니다. 모바일 기기에서도 사용할 수 있도록 PWA(Progressive Web App)로 구현되었습니다.

## 주요 기능

- 📸 실시간 카메라 스캔
- 📝 OCR 텍스트 추출
- 📁 문서 카테고리 관리
- 💾 문서 저장 및 관리
- 📱 PWA 지원 (모바일 설치 가능)
- 🔍 문서 검색 및 필터링

## 기술 스택

- Backend: Python Flask
- Frontend: HTML, CSS, JavaScript
- Database: SQLite
- OCR: Tesseract
- Image Processing: OpenCV
- PWA: Service Workers, Web App Manifest

## 설치 방법

1. 필요한 패키지 설치:
```bash
pip install -r requirements.txt
```

2. Tesseract OCR 설치:
- macOS: `brew install tesseract tesseract-lang`
- Ubuntu: `sudo apt-get install tesseract-ocr tesseract-ocr-kor`
- Windows: [Tesseract 설치 프로그램](https://github.com/UB-Mannheim/tesseract/wiki)

3. 환경 변수 설정:
`.env` 파일을 생성하고 다음 내용을 추가합니다:
```
FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///documents.db
UPLOAD_FOLDER=scanned_documents
SERVER_PORT=8080
SERVER_HOST=0.0.0.0
TESSERACT_CMD=/opt/homebrew/bin/tesseract
```

4. 서버 실행:
```bash
python app.py
```

## 사용 방법

1. 웹 브라우저에서 `https://localhost:8080` 접속
2. "카메라 열기" 버튼을 클릭하여 카메라 접근 권한 허용
3. 문서를 카메라로 촬영
4. 카테고리 선택 후 "문서 처리" 버튼 클릭
5. 추출된 텍스트 확인 및 저장

## PWA 설치 방법

### iOS (Safari)
1. Safari에서 웹사이트 접속
2. 공유 버튼 클릭
3. "홈 화면에 추가" 선택

### Android (Chrome)
1. Chrome에서 웹사이트 접속
2. 메뉴 버튼 클릭
3. "홈 화면에 추가" 선택

## 프로젝트 구조

```
OCR/
├── app.py              # Flask 서버
├── models.py           # 데이터베이스 모델
├── requirements.txt    # Python 패키지 의존성
├── .env               # 환경 변수 설정
├── static/            # 정적 파일
│   ├── manifest.json  # PWA 매니페스트
│   ├── sw.js         # Service Worker
│   └── icons/        # 앱 아이콘
├── templates/         # HTML 템플릿
│   └── index.html    # 메인 페이지
└── scanned_documents/ # 스캔된 문서 저장
```

## 환경 변수 설명

- `FLASK_ENV`: Flask 실행 환경 (development/production)
- `FLASK_DEBUG`: 디버그 모드 활성화 (1/0)
- `SECRET_KEY`: Flask 세션 암호화 키
- `DATABASE_URL`: 데이터베이스 연결 URL
- `UPLOAD_FOLDER`: 스캔된 문서 저장 경로
- `SERVER_PORT`: 서버 포트 번호 (기본값: 8080)
- `SERVER_HOST`: 서버 호스트 주소 (기본값: 0.0.0.0)
- `TESSERACT_CMD`: Tesseract OCR 실행 파일 경로

## 라이선스

MIT License

## 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request 