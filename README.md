# 속독 트레이닝

『과학적 속독법』(박화엽, 독서개발사, 1989)의 훈련 과정을 화면에서 따라 하는 속독 훈련 앱입니다. 원저자·출판사와 공식적인 관계가 없는 독립 서비스입니다.

이 저장소에는 원전 본문이나 스캔 이미지를 넣지 않습니다. 측정·독서용 글과 검증용 문장은 직접 쓴 것입니다.

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
| `.github/workflows/pages.yml` | 웹 앱 배포: 서비스에 필요한 파일 9개만 Pages에 올리고, 배포 뒤 실제 사이트를 검사 (`tools/verify_live.py`) |
| `.github/workflows/tests.yml` | 앱 원본이 바뀌면 Chromium·WebKit에서 시나리오 테스트 |
| `tests/` | 시나리오 테스트 16개. 전체 실행: `python3 -m http.server 8765` 를 켠 상태에서 `python3 tests/run_all.py` |
| `docs/` | 출시 계획, 테스트 체크리스트, Play Console·스토어 입력값 초안, 스토어 이미지 |

## 처음 한 번 설정

1. **GitHub Pages 켜기:** 저장소 Settings → Pages → Source를 **"GitHub Actions"**로 저장한 뒤, Actions → "Deploy Pages (service files only)" → Run workflow로 배포합니다. 서비스 파일 9개(`index.html`, `privacy.html`, `manifest.webmanifest`, `sw.js`, `icons/` 4개, `.well-known/assetlinks.json`)만 공개되고 개발 문서는 공개되지 않습니다. 문제가 생기면 Source를 "Deploy from a branch" → `main` / `/ (root)`로 돌리면 예전 방식(저장소 전체 공개)으로 바로 돌아갑니다.
2. **서명 키 비밀값 넣기:** Settings → Secrets and variables → Actions → New repository secret에서 아래 세 개를 만듭니다. 값은 따로 받은 `secrets.txt`와 `upload.keystore.base64`에 있습니다.
   - `KEYSTORE_BASE64`: `upload.keystore.base64` 파일 내용 전체
   - `KEYSTORE_PASSWORD`: `secrets.txt`의 값
   - `KEY_PASSWORD`: `secrets.txt`의 값
3. **앱 파일 만들기:** Actions → "Android app bundle" → Run workflow. 끝나면 실행 결과 아래 Artifacts에서 `.aab` 파일을 내려받아 Play Console에 올립니다.

서명 키 파일(`upload.keystore`)과 비밀번호는 저장소에 올리지 말고 안전한 곳에 따로 보관하세요. 잃어버리면 Play Console에서 업로드 키 재설정을 요청해야 합니다.

## Play Console에 올린 뒤

Play Console → 설정 → 앱 서명(App integrity)에 나오는 **앱 서명 키의 SHA-256 인증서 지문**을 `.well-known/assetlinks.json`의 `sha256_cert_fingerprints`에 추가해야 합니다. 이 지문이 없으면 Play에서 설치한 앱 위쪽에 주소창이 보입니다.

개발 맥락과 원칙, 남은 일은 `CLAUDE.md`에 있습니다.
