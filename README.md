# 속독 트레이닝

『과학적 속독법』(박화엽, 독서개발사, 1989)의 훈련 과정을 화면에서 따라 하는 속독 훈련 앱입니다.

- 웹: https://imkorea2414.github.io/
- 개인정보처리방침: https://imkorea2414.github.io/privacy.html
- Android 패키지 이름: `io.github.imkorea2414.speedread`

## 폴더 구성

| 경로 | 내용 |
| --- | --- |
| `src/template.html` | 앱 원본. 고친 뒤 `python3 tools/build.py`로 `index.html` 생성 |
| `index.html` | 빌드 결과 (직접 고치지 않음) |
| `manifest.webmanifest`, `sw.js`, `icons/` | 설치·오프라인 동작 |
| `privacy.html` | 개인정보처리방침 |
| `.well-known/assetlinks.json` | 웹 주소와 Android 앱을 연결하는 확인 파일 |
| `android/` | Google Play용 Android 프로젝트 (Trusted Web Activity) |
| `.github/workflows/android.yml` | Play에 올릴 `.aab` 파일을 자동으로 만드는 작업 |

## 처음 한 번 설정

1. **GitHub Pages 켜기:** 저장소 Settings → Pages → Source를 "Deploy from a branch", Branch를 `main` / `/ (root)`로 저장합니다.
2. **서명 키 비밀값 넣기:** Settings → Secrets and variables → Actions → New repository secret에서 아래 세 개를 만듭니다. 값은 따로 받은 `secrets.txt`와 `upload.keystore.base64`에 있습니다.
   - `KEYSTORE_BASE64`: `upload.keystore.base64` 파일 내용 전체
   - `KEYSTORE_PASSWORD`: `secrets.txt`의 값
   - `KEY_PASSWORD`: `secrets.txt`의 값
3. **앱 파일 만들기:** Actions → "Android app bundle" → Run workflow. 끝나면 실행 결과 아래 Artifacts에서 `.aab` 파일을 내려받아 Play Console에 올립니다.

서명 키 파일(`upload.keystore`)과 비밀번호는 저장소에 올리지 말고 안전한 곳에 따로 보관하세요. 잃어버리면 Play Console에서 업로드 키 재설정을 요청해야 합니다.

## Play Console에 올린 뒤

Play Console → 설정 → 앱 서명(App integrity)에 나오는 **앱 서명 키의 SHA-256 인증서 지문**을 `.well-known/assetlinks.json`의 `sha256_cert_fingerprints`에 추가해야 합니다. 이 지문이 없으면 Play에서 설치한 앱 위쪽에 주소창이 보입니다.

개발 맥락과 원칙, 남은 일은 `CLAUDE.md`에 있습니다.
