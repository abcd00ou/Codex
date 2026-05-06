# LLM 기업별 Contracted Compute Capacity 기반 최대 토큰 생성량 시뮬레이션 (2026-05-06)

## 제공 파일 (엑셀에서 바로 열기)
- `simulation_sheet_main.csv`: 회사별 입력/계산 시트
- `simulation_assumptions.csv`: 변수 정의 + 범위 + 근거
- `simulation_logic.csv`: 계산 로직 요약

> 위 3개 CSV는 Excel에서 각각 시트처럼 열 수 있습니다. 필요하면 새 통합문서에 시트로 붙여넣어 사용하세요.

## 1) 핵심 포인트
- OpenAI/Anthropic/Google/Meta/Microsoft/ByteDance/Alibaba/Tencent/DeepSeek의 **정확한 inference 전용 contracted capacity**는 대부분 비공개입니다.
- 따라서 실무적으로는 “capacity 입력값(시나리오)” + “InferenceX 하드웨어별 tok/s”를 결합한 추정이 표준적입니다.

## 2) 계산식
- `Effective_tok_per_s = Contracted_Capacity × Inference_Allocation × Weighted_tok/s/unit × Utilization_U × Decode_Factor_D × SLO_Headroom`
- `Tokens_per_day = Effective_tok_per_s × 86,400`
- `Tokens_per_month = Tokens_per_day × 30`

## 3) 로직 근거 (왜 이 항들이 필요한가)
1. **Inference_Allocation**: 계약 용량 전체가 추론에 100% 고정 배정되지 않음(훈련/추론 전환).
2. **Weighted_tok/s/unit**: 실제 클러스터는 단일 HW가 아니라 H100/H200/B200/MI300X 혼합.
3. **Utilization_U**: 피크 기준 스펙과 평균 운영 처리량 차이 보정.
4. **Decode_Factor_D**: prefill/디코드 비중, 입출력 길이 분포에 따른 실효 처리량 감소 반영.
5. **SLO_Headroom**: P95/P99 latency 보장을 위한 운영 여유(풀가동 회피).

## 4) 입력 가이드
- `Contracted_Capacity`: GPU 대수 또는 MW 기준으로 입력
- `Capacity_Type`: `GPU` 또는 `MW`
- `Model_Mix_Weighted_tok_per_s_per_unit`:
  - GPU 기준이면 `tok/s/gpu`
  - MW 기준이면 `tok/s/MW`
- 보수/기준/공격 3개 시나리오 파일 복제 후 비교 권장

## 5) 예시
가정:
- Contracted_Capacity = 100,000 (GPU)
- Inference_Allocation = 0.70
- Weighted_tok/s/unit = 120
- U = 0.70
- D = 0.80
- SLO_Headroom = 0.90

결과:
- Effective_tok/s = 4,233,600
- Tokens/day = 365,783,040,000
- Tokens/month(30d) = 10,973,491,200,000

## 6) 주의사항
- 회사별 capacity 자체가 비공개/가변이므로 결과는 “입력 가정의 함수”입니다.
- 모델 세대/정밀도/서빙 엔진(vLLM, TRT-LLM, SGLang 등)에 따라 `tok/s`는 크게 변합니다.
- 가능한 경우 동일 workload(문맥 길이/배치/출력 길이)에서 벤치 값을 통일하세요.
