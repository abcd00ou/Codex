# InferenceX CoT / Agentic TPS per GPU Overlay

이 산출물은 InferenceX의 main model-config benchmark row를 그대로 사용해 CoT와 agentic workload별 `scenario TPS/GPU`와 `users/GPU`를 계산한 것이다.

## 핵심 가정

```text
scenario_output_tok_s_gpu
= InferenceX output_tok_s_gpu / scenario_call_multiplier

users_per_gpu
= scenario_output_tok_s_gpu / interactivity_tok_s_user
```

- CoT/단일 추론: `scenario_call_multiplier = 1.0`
- Agentic/ReAct 도구 사용: `scenario_call_multiplier = 9.2`
- Interactivity: `30`, `50`, `70` tok/s/user
- GPU, GPU 수, concurrency, ISL/OSL, framework, precision은 InferenceX 원본 row 값을 유지했다.
- 모델별 `main_framework`, `main_precision`이 맞는 `is_main_model_config = yes` row만 사용했다.

## 왜 이렇게 계산했는가

Agentic workload는 사용자 요청 하나가 내부적으로 여러 번의 LLM call을 발생시킨다. 같은 GPU가 처리할 수 있는 내부 token 처리량은 InferenceX가 측정한 값에 가깝지만, 사용자 관점에서 한 업무를 끝내기 위해 필요한 내부 LLM call 수가 늘어난다.

```text
agentic scenario_output_tok_s_gpu
= InferenceX output_tok_s_gpu / 9.2
```

그 다음 사용자가 기대하는 응답 속도, 즉 interactivity를 `30/50/70 tok/s/user`로 두고 GPU 1장이 감당 가능한 동시 사용자 수를 계산한다.

## 사용 데이터

- 원천 DB: `llm_token_capacity_project/data/inferencex/inferencex_benchmark.sqlite`
- 원천 release: https://github.com/SemiAnalysisAI/InferenceX-app/releases/tag/db-dump/2026-06-08
- 사용 row 수: 28,579개 InferenceX benchmark row
- 확장 후 detail row 수: 171,474개
- 모델 수: 9
- GPU 종류 수: 9

## 산출 파일

- `inferencex_dynamic_reasoning_tps_gpu.csv`: row-level detail. 원본 benchmark row마다 CoT/agentic x interactivity 30/50/70 tok/s/user 조합을 붙인 파일.
- `inferencex_dynamic_reasoning_tps_gpu_summary.csv`: model/GPU/ISL/OSL/workload/interactivity tok/s/user별 p10/p50/p90 요약.

## Agentic 1024/1024 샘플

| Model | GPU | ISL/OSL | tok/s/user | Calls/request | Base output tok/s/GPU p50 | Scenario output tok/s/GPU p50 | Users/GPU p50 |
|---|---|---:|---:|---:|---:|---:|---:|
| dsr1 | B200 | 1024/1024 | 30 | 9.2 | 141 | 15.3 | 0.512 |
| dsr1 | B200 | 1024/1024 | 50 | 9.2 | 141 | 15.3 | 0.307 |
| dsr1 | B200 | 1024/1024 | 70 | 9.2 | 141 | 15.3 | 0.219 |
| dsr1 | B300 | 1024/1024 | 30 | 9.2 | 202 | 22.0 | 0.733 |
| dsr1 | B300 | 1024/1024 | 50 | 9.2 | 202 | 22.0 | 0.44 |
| dsr1 | B300 | 1024/1024 | 70 | 9.2 | 202 | 22.0 | 0.314 |
| dsr1 | H200 | 1024/1024 | 30 | 9.2 | 108 | 11.8 | 0.393 |
| dsr1 | H200 | 1024/1024 | 50 | 9.2 | 108 | 11.8 | 0.236 |
| dsr1 | H200 | 1024/1024 | 70 | 9.2 | 108 | 11.8 | 0.168 |
| dsr1 | MI300X | 1024/1024 | 30 | 9.2 | 72.2 | 7.85 | 0.262 |
| dsr1 | MI300X | 1024/1024 | 50 | 9.2 | 72.2 | 7.85 | 0.157 |
| dsr1 | MI300X | 1024/1024 | 70 | 9.2 | 72.2 | 7.85 | 0.112 |
| dsr1 | MI325X | 1024/1024 | 30 | 9.2 | 76.8 | 8.344 | 0.278 |
| dsr1 | MI325X | 1024/1024 | 50 | 9.2 | 76.8 | 8.344 | 0.167 |
| dsr1 | MI325X | 1024/1024 | 70 | 9.2 | 76.8 | 8.344 | 0.119 |
| dsr1 | MI355X | 1024/1024 | 30 | 9.2 | 87.5 | 9.508 | 0.317 |
| dsr1 | MI355X | 1024/1024 | 50 | 9.2 | 87.5 | 9.508 | 0.19 |
| dsr1 | MI355X | 1024/1024 | 70 | 9.2 | 87.5 | 9.508 | 0.136 |

## 해석

- CoT와 agentic은 workload 비중을 섞지 않고 각각 계산했다.
- CoT는 call multiplier가 1.0이라 원본 InferenceX output TPS/GPU를 유지한다.
- Agentic은 call multiplier가 9.2라 scenario output TPS/GPU가 CoT 대비 10.9% 수준이다.
- Interactivity 30/50/70은 비중이 아니라 tok/s/user 요구 수준이며, 값이 높을수록 같은 TPS/GPU에서 감당 가능한 users/GPU가 줄어든다.
- 이 값은 LLMServingSim power model의 full simulation을 대체하지 않는다. tool wait, prefix cache, KV cache pressure, SLO 실패율은 아직 단순화되어 있다.
