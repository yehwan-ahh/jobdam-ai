# 잡담 (Job談)

현직자 AI 패널과 '3년 뒤의 나'가 공공데이터를 근거로 함께 고민해 주는 청년 진로 탐색 에이전트.
2026 대한민국 청년 CAREER FAIR AI 해커톤 출품용 프로토타입.

## 실행
```bash
pip install -r requirements.txt
streamlit run app.py
```
API 키는 `.streamlit/secrets.toml.example`을 참고해 `.streamlit/secrets.toml`에 넣습니다 (Git에 올리지 않음).

## 데이터 출처
| 출처 | 제공기관 | 이용조건 |
|---|---|---|
| 커리어넷 직업정보(직업백과) Open API | 한국직업능력연구원 | 공공누리 제1유형(출처표시) |
| 국가통계포털(KOSIS) OpenAPI | 국가데이터처 | KOSIS 통계정보활용약관 |

## 유의사항
- 실제 개인정보를 외부 AI API에 입력하지 않습니다. 시연에는 가상 데이터만 사용합니다.
