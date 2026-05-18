# Assumption Change Log

계산식, 계수, 시나리오, confidence를 바꿀 때마다 이 파일에 기록합니다.

| 날짜 | 항목 | 기존값 | 변경값 | 이유 | 영향 |
|---|---|---|---|---|---|
| 2026-05-14 | 프로젝트 구조 | ai_scm_project 내부 보고서 | llm_token_capacity_project 독립 프로젝트 | 지속적 fact-check와 숫자 정합성 관리 | 산출물과 운영 문서 분리 |
| 2026-05-18 | A08 tokens_per_second_per_mw | Base numeric band unchanged | Added proposed mechanism/proxy refinement only | Joule/IBM/2026 serving papers support energy/SLO sanity checks but not direct company production coefficient changes | Future energy sanity layer and scenario sensitivity candidate |
| 2026-05-18 | A09 utilization | 2026 45-65%, 2030 60-80% | Base band unchanged; added SLO/workload/placement caveat | 2026 prefill-decode and SLO-aware allocation sources show utilization is constrained by latency and workload shape | Future strict-SLO vs batchable sensitivity candidate |

## 기록 규칙

- 숫자 하나라도 바꾸면 이유를 적습니다.
- 공식 출처로 교체한 경우 source_id를 함께 적습니다.
- 시나리오 조정이면 Bear/Base/Bull 중 어떤 case에 영향을 주는지 적습니다.
- confidence 변경이면 downgrade/upgrade 이유를 적습니다.
