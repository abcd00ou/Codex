# Evidence Rules

모든 assumption agent는 아래 evidence 규칙을 따릅니다.

## Evidence Class

| Class | 의미 | 예 |
|---|---|---|
| Fact | 출처 원문에 직접 있는 숫자 또는 명시 문장 | 공식 GW 발표, model card parameter |
| Derived Estimate | fact를 이용해 계산한 값 | active_power_gw, inference_gw |
| Proxy | 유사 benchmark 또는 공개 모델로 대체한 값 | closed model tokens/sec/MW proxy |
| Scenario | 미래 ramp, mix, efficiency 가정 | Bear/Base/Bull multiplier |

## Source Tier

| Tier | Source | 사용 방식 |
|---|---|---|
| Tier 1 | 회사 공식 발표, SEC/IR, model card, technical report, 공식 docs | fact anchor 가능 |
| Tier 2 | 정부/기관/학술 논문, 표준기관, 연구기관 | macro boundary, mechanism, benchmark |
| Tier 3 | 신뢰도 높은 언론/시장조사 요약 | 보조 evidence, confidence 제한 |
| Reject | anonymous blog, undated claim, social rumor | 사용 금지 |

## Required Fields

새 evidence entry는 반드시 다음 필드를 포함합니다.

```text
evidence_id
source_id
title
publisher
date
url_or_report
source_tier
evidence_class
exact_claim_or_number
unit
applies_to
model_field_impacted
confidence
replacement_path
reviewer
review_date
```

## Numeric Rule

숫자는 반드시 단위를 명시합니다.

- GW: instantaneous power
- MW: instantaneous power
- TWh/year: annual energy
- tokens/sec: throughput
- tokens/day: daily volume
- Q tokens/year: annual token volume
- parameters: model scale
- active parameters: token-level compute scale

단위가 다르면 같은 숫자처럼 비교하지 않습니다.
