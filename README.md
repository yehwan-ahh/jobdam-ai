# 잡담 (Job談)

현직자 AI 패널과 '3년 뒤의 나'가 공공데이터를 근거로 함께 고민해 주는 청년 진로 탐색 에이전트.
2026 대한민국 청년 CAREER FAIR AI 해커톤 출품용 프로토타입.

## 실행
```bash
pip install -r requirements.txt
streamlit run app.py
```
API 키는 `.streamlit/secrets.toml.example`을 참고해 `.streamlit/secrets.toml`에 넣습니다 (Git에 올리지 않음).

## 사이트 구성
| 페이지 | 파일 | 내용 |
|---|---|---|
| 대시보드 | `app_pages/home.py` | 서비스 소개, 시작하기 |
| 직무 패널 | `app_pages/panel.py` | 학과로 찾기·직접 고르기·패널 추천 → 직무 선배와 대화, 다른 선배 의견(패널 토론), 국비 훈련과정 |
| 3년 뒤의 나 | `app_pages/future.py` | 취업·대학원·창업 KOSIS 숫자 비교, 갈림길별 '3년 뒤의 나'와 대화 |
| 데이터와 원칙 | `app_pages/data.py` | 데이터 출처, 답변·개인정보 원칙, AI의 한계와 대응 |
| 프로젝트 소개 | `app_pages/about.py` | 로드맵, 링크 |

AI 키가 없으면 시연 모드로 동작합니다. 시스템 프롬프트는 `utils/prompts.py`(맥락·지침·응답 형식·일관성 4단 구조)에 있습니다.

## 데이터 출처
| 출처 | 제공기관 | 이용조건 | 사용 위치 |
|---|---|---|---|
| 고용24 직업정보 OPEN-API | 한국고용정보원 | 공공누리 제4유형(출처표시·상업적 이용금지·변경금지), 고용24 OPEN-API 이용약관 | 직무 선배 답변 근거 |
| 고용24 국민내일배움카드 훈련과정 OPEN-API | 고용노동부·한국고용정보원 | 고용24 OPEN-API 이용약관 | 국비 훈련과정 추천 |
| 국가통계포털(KOSIS) OpenAPI | 국가데이터처 | KOSIS 통계정보활용약관 | 갈림길 비교, 3년 뒤의 나 |
| 상위진출직업(2022) | 한국고용정보원(공공데이터포털) | 공공데이터포털 이용조건 | 학과로 직무 고르기 (`data/major_top_jobs.csv`) |

## Credits / Licenses
| 구분 | 명칭 | 라이선스 |
|---|---|---|
| 오픈소스 | Streamlit | Apache-2.0 |
| 오픈소스 | pandas | BSD-3-Clause |
| 오픈소스 | Altair | BSD-3-Clause |
| 오픈소스 | requests | Apache-2.0 |
| 오픈소스 | OpenAI Python SDK | Apache-2.0 |
| 글꼴 | Noto Sans KR | SIL Open Font License 1.1 |
| AI 모델(서비스) | OpenAI gpt-5-mini | OpenAI API 이용약관 |
| AI 도구(개발) | Claude Code (Anthropic) | 코드·문서 초안 작성 보조 |

## 유의사항
- 실제 개인정보를 외부 AI API에 입력하지 않습니다. 전화번호·이메일·주민등록번호 패턴은 AI에 보내지 않으며, 시연에는 가상 데이터만 사용합니다.
- API 키는 배포 환경의 Secrets에만 보관하며 저장소에 올리지 않습니다.
