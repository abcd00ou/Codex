# Assumption Textbook Index

생성일: 2026-05-15

이 폴더는 LLM token capacity simulation의 11개 핵심 가정을 각각 독립 리포트로 공부하기 위한 자료입니다.

| ID | 가정 | 공부 질문 | Markdown | Word |
|---|---|---|---|---|
| A01 | contracted_power_gw | 계약·발표 전력 capacity를 어떻게 읽을 것인가 | A01_contracted_power_gw.md | outputs/reports/assumptions/A01_contracted_power_gw.docx |
| A02 | active_power_gw | 실제로 AI cluster가 쓸 수 있는 운영 전력을 추정하는 법 | A02_active_power_gw.md | outputs/reports/assumptions/A02_active_power_gw.docx |
| A03 | pue | facility power를 IT load로 바꾸는 핵심 계수 | A03_pue.md | outputs/reports/assumptions/A03_pue.docx |
| A04 | ai_workload_share | IT load 중 실제 AI training/inference cluster가 차지하는 비중 | A04_ai_workload_share.md | outputs/reports/assumptions/A04_ai_workload_share.docx |
| A05 | inference_power_share | AI IT load 중 상용 토큰 생성에 배정되는 전력 비중 | A05_inference_power_share.md | outputs/reports/assumptions/A05_inference_power_share.docx |
| A06 | training_power_share | frontier training, post-training, eval capacity를 어떻게 남길 것인가 | A06_training_power_share.md | outputs/reports/assumptions/A06_training_power_share.docx |
| A07 | active_parameters | Dense와 MoE에서 token당 실제 계산량을 결정하는 핵심 변수 | A07_active_parameters.md | outputs/reports/assumptions/A07_active_parameters.docx |
| A08 | tokens_per_second_per_mw | 1MW inference load가 초당 몇 token을 만들 수 있는가 | A08_tokens_per_second_per_mw.md | outputs/reports/assumptions/A08_tokens_per_second_per_mw.docx |
| A09 | utilization | 이론 capacity 중 실제 연평균 토큰으로 전환되는 비율 | A09_utilization.md | outputs/reports/assumptions/A09_utilization.docx |
| A10 | attribution_rule | host capacity와 model-owner token을 중복 없이 귀속하는 법 | A10_attribution_rule.md | outputs/reports/assumptions/A10_attribution_rule.docx |
| A11 | gpu_asic_mix | GPU와 purpose-built accelerator mix를 tokens/MW로 연결하는 법 | A11_gpu_asic_mix.md | Markdown-first; workbook trace 반영 |

## 추천 학습 순서

1. A01-A02로 전력 capacity의 상한과 active 전환을 이해합니다.
2. A03-A04로 facility power와 AI IT load의 차이를 이해합니다.
3. A05-A06으로 training/inference allocation을 공부합니다.
4. A07-A09로 모델 구조, serving efficiency, utilization을 공부합니다.
5. A10으로 company attribution을 정리해 중복 계산을 제거합니다.
6. A11으로 hardware mix와 tokens/MW bridge의 숫자 근거를 점검합니다.
