# 🛠️ 레고-시아 개발 및 운영 가이드라인 (Dev Guidelines)

## 1. 이모지 사용 금지 (Strict No-Emoji Policy)
윈도우 콘솔(cp949) 환경 및 서버 자동화 환경에서의 인코딩 호환성을 보장하기 위해, 모든 소스 코드 내 로그 및 출력 메시지에 이모지 사용을 금지한다.

### 🚫 금지 사례
- `print("🚀 배포 시작")` -> **Error 유발**
- `print("✅ 성공")` -> **Error 유발**

### ✅ 올바른 사례
- `print("[DEPLOY] Starting deployment")`
- `print("[OK] Success")`
- `print("[WARN] Warning message")`
- `print("[ERR] Error occurred")`

## 2. 코드 가독성
- 모든 로그는 영문 또는 표준 한글 텍스트(특수문자 제외)로만 구성한다.
- 텔레그램 전송용 메시지(Markdown)는 웹 전송이므로 예외적으로 허용하나, 가급적 최소화한다.

---
*Last Updated: 2026-04-11*
