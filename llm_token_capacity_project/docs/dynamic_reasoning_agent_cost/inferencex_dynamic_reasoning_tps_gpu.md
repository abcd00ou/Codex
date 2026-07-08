# InferenceX CoT / Agentic TPS per GPU Overlay

이 산출물은 InferenceX의 main model-config benchmark row를 그대로 사용해 CoT와 agentic workload별 `scenario TPS/GPU`와 `users/GPU`를 계산한 것이다.

## 핵심 가정

```text
scenario_total_tok_s_gpu
= InferenceX tok_s_gpu / scenario_call_multiplier

users_per_gpu
= scenario_total_tok_s_gpu / target_tok_s_user
```

- CoT/단일 추론: `scenario_call_multiplier = 1.0`
- Agentic/ReAct 도구 사용: `scenario_call_multiplier = 9.2`
- Interactivity: target `30`, `50`, `70` tok/s/user. 실제 row 선택은 `median_tpot`에서 역산한 realized tok/s/user가 target에 가장 가까운 최신 benchmark row를 사용한다.
- GPU, GPU 수, concurrency, ISL/OSL, framework, precision은 InferenceX 원본 row 값을 유지했다.
- 모델별 `main_framework`, `main_precision`이 맞는 `is_main_model_config = yes` row만 사용했다.

## 왜 이렇게 계산했는가

Agentic workload는 사용자 요청 하나가 내부적으로 여러 번의 LLM call을 발생시킨다. 같은 GPU가 처리할 수 있는 내부 token 처리량은 InferenceX가 측정한 값에 가깝지만, 사용자 관점에서 한 업무를 끝내기 위해 필요한 내부 LLM call 수가 늘어난다.

```text
agentic scenario_total_tok_s_gpu
= InferenceX tok_s_gpu / 9.2
```

그 다음 사용자가 기대하는 응답 속도, 즉 target interactivity를 `30/50/70 tok/s/user`로 두고 GPU 1장이 감당 가능한 동시 사용자 수를 계산한다.

## 사용 데이터

- 원천 DB: `llm_token_capacity_project/data/inferencex/inferencex_benchmark.sqlite`
- 원천 release: https://github.com/SemiAnalysisAI/InferenceX-app/releases/tag/db-dump/2026-06-08
- 사용 row 수: 28,579개 InferenceX benchmark row
- 확장 후 detail row 수: 171,474개
- 모델 수: 9
- GPU 종류 수: 9

## 산출 파일

- `inferencex_dynamic_reasoning_tps_gpu.csv`: row-level detail. 원본 benchmark row마다 CoT/agentic x interactivity 30/50/70 tok/s/user 조합을 붙인 파일.
- `inferencex_dynamic_reasoning_tps_gpu_summary.csv`: model/GPU/ISL/OSL/workload/target tok/s/user별 최신 근접 row 요약.

## Agentic 1024/1024 샘플

| Model | GPU | ISL/OSL | target tok/s/user | realized tok/s/user | Concurrency | Calls/request | Base total tok/s/GPU | Scenario total tok/s/GPU | Users/GPU |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| dsr1 | B200 | 1024/1024 | 30 | 28.8 | 256 | 9.2 | 1,707 | 186 | 6.186 |
| dsr1 | B200 | 1024/1024 | 50 | 45.9 | 64 | 9.2 | 678 | 73.7 | 1.474 |
| dsr1 | B200 | 1024/1024 | 70 | 76.2 | 16 | 9.2 | 292 | 31.7 | 0.453 |
| dsr1 | B300 | 1024/1024 | 30 | 30.4 | 256 | 9.2 | 1,808 | 197 | 6.551 |
| dsr1 | B300 | 1024/1024 | 50 | 47.2 | 64 | 9.2 | 714 | 77.6 | 1.552 |
| dsr1 | B300 | 1024/1024 | 70 | 64.0 | 32 | 9.2 | 491 | 53.4 | 0.762 |
| dsr1 | H200 | 1024/1024 | 30 | 31.8 | 64 | 9.2 | 506 | 55.0 | 1.832 |
| dsr1 | H200 | 1024/1024 | 50 | 44.7 | 32 | 9.2 | 354 | 38.5 | 0.77 |
| dsr1 | H200 | 1024/1024 | 70 | 60.8 | 16 | 9.2 | 241 | 26.2 | 0.374 |
| dsr1 | MI300X | 1024/1024 | 30 | 24.6 | 64 | 9.2 | 377 | 41.0 | 1.366 |
| dsr1 | MI300X | 1024/1024 | 50 | 47.6 | 16 | 9.2 | 182 | 19.8 | 0.395 |
| dsr1 | MI300X | 1024/1024 | 70 | 68.6 | 4 | 9.2 | 63.6 | 6.913 | 0.099 |
| dsr1 | MI325X | 1024/1024 | 30 | 28.8 | 64 | 9.2 | 440 | 47.8 | 1.593 |
| dsr1 | MI325X | 1024/1024 | 50 | 52.0 | 16 | 9.2 | 200 | 21.7 | 0.435 |
| dsr1 | MI325X | 1024/1024 | 70 | 70.4 | 4 | 9.2 | 66.1 | 7.187 | 0.103 |
| dsr1 | MI355X | 1024/1024 | 30 | 39.2 | 64 | 9.2 | 589 | 64.0 | 2.132 |
| dsr1 | MI355X | 1024/1024 | 50 | 52.6 | 32 | 9.2 | 393 | 42.7 | 0.854 |
| dsr1 | MI355X | 1024/1024 | 70 | 75.4 | 16 | 9.2 | 281 | 30.6 | 0.437 |

## 해석

- CoT와 agentic은 workload 비중을 섞지 않고 각각 계산했다.
- CoT는 call multiplier가 1.0이라 원본 InferenceX total TPS/GPU를 유지한다.
- Agentic은 call multiplier가 9.2라 scenario total TPS/GPU가 CoT 대비 10.9% 수준이다.
- Interactivity 30/50/70은 비중이 아니라 tok/s/user 요구 수준이며, 값이 높을수록 같은 TPS/GPU에서 감당 가능한 users/GPU가 줄어든다.
- 이 값은 LLMServingSim power model의 full simulation을 대체하지 않는다. tool wait, prefix cache, KV cache pressure, SLO 실패율은 아직 단순화되어 있다.
