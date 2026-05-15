# Hallucination Double-Check Checklist

보고 전 이 체크리스트를 사용해 값과 문구를 점검합니다. Excel의 `11_hallucination_checklist`와 같은 목적이지만, 이 MD는 작업 과정에서 계속 수정하는 운영용 문서입니다.

| ID | 체크 항목 | 확인 질문 | 통과 기준 | 실패 시 조치 |
|---|---|---|---|---|
| HC01 | Source existence | 모든 주요 숫자에 source_id가 있는가? | source_id, title, publisher, date, URL/report가 존재 | source 추가 또는 숫자 제거 |
| HC02 | Numeric quote | 원문에 숫자가 직접 존재하는가? | 원문 숫자와 모델 숫자가 일치 | quote note 작성 또는 estimate로 강등 |
| HC03 | Fact vs estimate | fact, estimate, proxy, scenario가 분리됐는가? | derivation_type이 명확 | 보고 문구 수정 |
| HC04 | Closed model params | 비공개 모델 파라미터를 precise number로 쓰지 않았는가? | band 또는 undisclosed 처리 | parameter 표현 수정 |
| HC05 | MoE active params | MoE total/active parameter를 분리했는가? | total과 active가 별도 필드 | active parameter source 확인 |
| HC06 | Host vs owner | cloud host capacity와 model owner token을 혼동하지 않았는가? | attribution_rule 명시 | company row 재분류 |
| HC07 | Microsoft/OpenAI overlap | Copilot, Azure-hosted OpenAI, OpenAI API attribution이 분리됐는가? | overlap note 존재 | 중복 계산 제거 |
| HC08 | Capacity boundary | active_power_gw가 contracted_power_gw 이하인가? | validation PASS | ramp multiplier 조정 |
| HC09 | Power split | training + inference share가 100%인가? | validation PASS | share 수정 |
| HC10 | Unit consistency | GW, MW, tokens/sec, tokens/day, annual token 단위가 맞는가? | 재계산 일치 | 단위 변환 수정 |
| HC11 | Benchmark proxy | benchmark를 실제 회사 성능처럼 쓰지 않았는가? | proxy 문구 명시 | slide/MD wording 수정 |
| HC12 | Inference share | 2026 inference 60%+를 fact처럼 말하지 않았는가? | scenario 표현 사용 | executive summary 수정 |
| HC13 | Outlier review | benchmark와 main model 괴리 큰 row를 검토했는가? | ±50% 이상 row에 review note | confidence downgrade |
| HC14 | China transparency | 중국 업체의 낮은 공개성을 숫자 penalty로 착각하지 않았는가? | confidence만 조정 | assumption note 수정 |
| HC15 | Executive wording | 임원 보고 문구가 확정/추정/시나리오를 구분하는가? | 모든 chart subtitle에 기준 표시 | PPT/HTML/MD 수정 |

## 수동 체크 메모

아래 영역은 다음 리뷰 때 직접 기록합니다.

| 날짜 | reviewer | 확인한 source_id | 이슈 | 조치 |
|---|---|---|---|---|
| 2026-05-14 | Codex | 전체 구조 | 최초 독립 프로젝트 생성 | 운영 문서 추가 |

## 우선순위가 높은 재검토 영역

1. 업체별 active_power_gw
2. inference_power_share
3. tokens_per_second_per_mw
4. closed model parameter band
5. OpenAI, Anthropic, Microsoft attribution overlap
6. China model owner의 실제 commercial serving scale
7. benchmark_reference와 main forecast 괴리 row
