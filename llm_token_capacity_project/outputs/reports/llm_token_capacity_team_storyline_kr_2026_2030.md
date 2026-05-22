# 상용 LLM 토큰 Capacity 팀 발표용 산출물

## 발표 목적

상용 LLM model owner 기준으로 2026-2030년 전력, 추론 GW, tokens/MW, utilization, InferenceX benchmark layer를 연결해 메모리 마케팅팀의 account 우선순위와 제품별 revenue motion을 결정한다.

## 핵심 메시지

2030년 LLM 토큰 병목은 단순 전력 확보보다 **추론 전환 속도, serving 효율, utilization, model-owner별 capacity 집중도**에서 갈린다. 메모리 마케팅은 HBM allocation, DDR5/MRDIMM attach, enterprise SSD/QLC, CXL proof pack을 상위 model owner별로 선제 배치한다.

## 발표 흐름

| Slide | 제목 | 발표 포인트 |
|---:|---|---|
| 1 | 2030년 LLM 토큰 병목 | 결론부터 제시: token capacity는 전력보다 추론 전환과 serving 효율에 민감 |
| 2 | 발표에서 답할 네 가지 질문 | 얼마나 커지나, 누가 주도하나, 무엇이 흔드나, 무엇을 해야 하나 |
| 3 | 2026-2030 generated output token 증가 | 전력 가동 속도와 serving 효율이 토큰 capacity 범위를 결정 |
| 4 | 2030 상위 model owner | 상위 업체 중심 account focus |
| 5 | Token 정의 | generated output token과 processed token, training token 분리 |
| 6 | 전력 funnel 계산 로직 | 추론 GW, tokens/MW, utilization의 곱 구조 설명 |
| 7 | InferenceX로 보정하는 항목 | tokens/MW, J/token, SLO 조건을 serving 효율 계수에 반영 |
| 8 | 핵심 driver | active power와 utilization이 가장 큰 swing factor |
| 9 | 메모리 마케팅 액션 | HBM, DDR5/MRDIMM, SSD/QLC, CXL별 sales motion |
| 10 | 다음 운영 방식 | source refresh, model update, account translation, sales review |
| 11 | Workbook 부록 위치 | 계산식, 가정, InferenceX 원천 테이블 위치 안내 |

## 산출물 위치

- 발표용 PPT: `llm_token_capacity_team_storyline_kr_2026_2030.pptx`
- 전체 검증 Excel: `llm_token_capacity_2026_2030.xlsx`
- HTML 대시보드: `llm_token_capacity_2026_2030.html`
- Markdown 보고서: `llm_token_capacity_2026_2030.md`
- JSON 데이터: `llm_token_capacity_2026_2030.json`

## 발표 시 핵심 정의

- `inference_tokens_per_day`는 generated output token equivalent이다.
- InferenceX total `tok_s_mw`는 input+output 처리량일 수 있으므로 headline forecast에는 직접 대입하지 않는다.
- active GW, inference share, tokens/MW, utilization은 각각 별도 가정이며 서로 대체하지 않는다.
- InferenceX는 tokens/MW와 SLO 조건을 보정하는 benchmark layer로 사용한다.
- 발표 톤은 방어적 설명이 아니라, 검증된 계산 결과를 바탕으로 account action을 정하는 방식으로 가져간다.
