# InferenceX Model x Chat Type x GPU TPS/MW Summary

작성일: 2026-07-23

이 문서는 전력 기반 token capacity 산출에서 사용하는 InferenceX proxy 모델별, 채팅 유형별, GPU별 output TPS/MW를 빠르게 검토하기 위한 요약이다.

## 기준

- 원천 데이터: `llm_token_capacity_project/data/inferencex/normalized/inferencex_benchmark_results.csv`
- 기준 metric: `output_tok_s_mw`
- 단위: generated output tokens/sec/MW
- Benchmark type: `single_turn`
- Model config: `is_main_model_config = yes`
- Interactivity/concurrency: `concurrency 32-256`
- Serving stack selection: Dynamo/TRT-LLM/MTP 계열 stack이 있으면 그 안의 최고 `output_tok_s_mw`, 없으면 같은 조건의 public max
- Short chat: `ISL/OSL 1024/1024`
- Long chat: `ISL/OSL 8192/1024`
- Agentic: agentic trace 평균 `ISL/OSL 100947/860`을 직접 matched benchmark로 쓰지 않고, Kimi K2.5 dynamic reasoning row의 agentic/long ratio를 적용한다.
- Kimi 기준 agentic/long ratio: `10.9%` (`1 / 9.2x`). 산출 근거는 `inferencex_dynamic_reasoning_tps_gpu.csv`의 Kimi K2.5, `workload_type=agentic`, `ISL/OSL 8192/1024`, main config 675개 row의 median ratio다.
- 산식용 selected 값: 위 조건을 통과한 row에서 token output이 가장 많이 나오는 기준이다. 기존 p50/long-context guardrail 기준보다 aggressive capacity reference다.

## 모델 매핑

| Report proxy model | InferenceX source model | 현재 적용 대상 |
|---|---|---|
| `gptoss120b` | `gptoss120b` | Microsoft, xAI, Tencent |
| `frontier_composite` | H200: `gptoss120b`; B200/GB200: `dsv4 + kimik2.5` | OpenAI, Anthropic, Google |
| `llama70b` | `llama70b` | Meta |
| `dsr1` | `dsr1` | DeepSeek |
| `qwen3.5` | `qwen3.5` | Alibaba |

## 산식용 Selected TPS/MW

| Model | GPU | Short selected TPS/MW | Long selected TPS/MW | Agentic selected TPS/MW | Status |
|---|---:|---:|---:|---:|---|
| `gptoss120b` | H200 | 1,459,609 | 1,451,169 | 157,736 | direct/public max / direct/public max / long_chat x 10.9% |
| `gptoss120b` | B200 | 4,516,967 | 2,629,943 | 285,863 | direct/public max / direct/public max / long_chat x 10.9% |
| `gptoss120b` | GB200 | 4,516,967 | 2,629,943 | 285,863 | fallback:B200/public max / fallback:B200/public max / long_chat x 10.9% |
| `frontier_composite` | H200 | 1,459,609 | 1,451,169 | 157,736 | direct/public max / direct/public max / long_chat x 10.9% |
| `frontier_composite` | B200 | 135,306 | 269,470 | 29,290 | direct/public max / direct/optimized max / long_chat x 10.9% |
| `frontier_composite` | GB200 | 105,270 | 422,015 | 45,871 | direct/optimized max / direct/optimized max / long_chat x 10.9% |
| `llama70b` | H200 | 965,061 | 247,853 | 26,941 | direct/public max / direct/public max / long_chat x 10.9% |
| `llama70b` | B200 | 1,228,515 | 384,593 | 41,804 | direct/public max / direct/public max / long_chat x 10.9% |
| `llama70b` | GB200 | 1,228,515 | 384,593 | 41,804 | fallback:B200/public max / fallback:B200/public max / long_chat x 10.9% |
| `dsr1` | H200 | 150,172 | 104,025 | 11,307 | direct/public max / direct/public max / long_chat x 10.9% |
| `dsr1` | B200 | 393,572 | 131,309 | 14,273 | direct/public max / direct/public max / long_chat x 10.9% |
| `dsr1` | GB200 | 393,572 | 131,309 | 14,273 | fallback:B200/public max / fallback:B200/public max / long_chat x 10.9% |
| `qwen3.5` | H200 | 246,069 | 150,267 | 16,333 | direct/public max / direct/public max / long_chat x 10.9% |
| `qwen3.5` | B200 | 1,106,733 | 506,838 | 55,091 | direct/public max / direct/public max / long_chat x 10.9% |
| `qwen3.5` | GB200 | 1,106,733 | 506,838 | 55,091 | fallback:B200/public max / fallback:B200/public max / long_chat x 10.9% |

## Raw 평균/최대 TPS/MW

| Model | InferenceX source | GPU | Short mean | Short max | Short n | Long mean | Long max | Long n | Agentic max basis |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `gptoss120b` | `gptoss120b` | H200 | 782,278 | 1,459,609 | 382 | 555,348 | 1,451,169 | 437 | 157,736 |
| `gptoss120b` | `gptoss120b` | B200 | 1,780,482 | 4,516,967 | 450 | 1,176,458 | 2,629,943 | 450 | 285,863 |
| `gptoss120b` | `gptoss120b` | GB200 | 1,780,482 | 4,516,967 | 450 | 1,176,458 | 2,629,943 | 450 | 285,863 |
| `frontier_composite` | `gptoss120b` | H200 | 782,278 | 1,459,609 | 382 | 555,348 | 1,451,169 | 437 | 157,736 |
| `frontier_composite` | `dsv4+kimik2.5` | B200 | 105,993 | 135,306 | 10 | 96,796 | 269,470 | 14 | 29,290 |
| `frontier_composite` | `dsv4+kimik2.5` | GB200 | 86,132 | 105,270 | 9 | 153,415 | 422,015 | 18 | 45,871 |
| `llama70b` | `llama70b` | H200 | 512,342 | 965,061 | 94 | 188,633 | 247,853 | 88 | 26,941 |
| `llama70b` | `llama70b` | B200 | 579,686 | 1,228,515 | 107 | 254,884 | 384,593 | 79 | 41,804 |
| `llama70b` | `llama70b` | GB200 | 579,686 | 1,228,515 | 107 | 254,884 | 384,593 | 79 | 41,804 |
| `dsr1` | `dsr1` | H200 | 113,000 | 150,172 | 124 | 72,373 | 104,025 | 122 | 11,307 |
| `dsr1` | `dsr1` | B200 | 134,815 | 393,572 | 147 | 72,615 | 131,309 | 132 | 14,273 |
| `dsr1` | `dsr1` | GB200 | 134,815 | 393,572 | 147 | 72,615 | 131,309 | 132 | 14,273 |
| `qwen3.5` | `qwen3.5` | H200 | 164,117 | 246,069 | 24 | 115,660 | 150,267 | 23 | 16,333 |
| `qwen3.5` | `qwen3.5` | B200 | 542,922 | 1,106,733 | 30 | 290,266 | 506,838 | 27 | 55,091 |
| `qwen3.5` | `qwen3.5` | GB200 | 542,922 | 1,106,733 | 30 | 290,266 | 506,838 | 27 | 55,091 |

## Raw Max TPS/MW

아래 표는 산식용 max 기준과 대조하기 위한 원천 row 최대값이다.

| Model | GPU | Short raw max TPS/MW | Long raw max TPS/MW | Agentic raw max TPS/MW |
|---|---:|---:|---:|---:|
| `gptoss120b` | H200 | 1,459,609 | 1,451,169 | 157,736 |
| `gptoss120b` | B200 | 4,516,967 | 2,629,943 | 285,863 |
| `gptoss120b` | GB200 | 4,516,967 | 2,629,943 | 285,863 |
| `frontier_composite` | H200 | 1,459,609 | 1,451,169 | 157,736 |
| `frontier_composite` | B200 | 135,306 | 269,470 | 29,290 |
| `frontier_composite` | GB200 | 105,270 | 422,015 | 45,871 |
| `llama70b` | H200 | 965,061 | 247,853 | 26,941 |
| `llama70b` | B200 | 1,228,515 | 384,593 | 41,804 |
| `llama70b` | GB200 | 1,228,515 | 384,593 | 41,804 |
| `dsr1` | H200 | 150,172 | 104,025 | 11,307 |
| `dsr1` | B200 | 393,572 | 131,309 | 14,273 |
| `dsr1` | GB200 | 393,572 | 131,309 | 14,273 |
| `qwen3.5` | H200 | 246,069 | 150,267 | 16,333 |
| `qwen3.5` | B200 | 1,106,733 | 506,838 | 55,091 |
| `qwen3.5` | GB200 | 1,106,733 | 506,838 | 55,091 |

## 해석 메모

- `direct`는 해당 model/GPU/chat 조건에 맞는 InferenceX row가 존재한다는 뜻이다.
- `fallback`은 해당 GPU에 matched row가 없어서 가장 가까운 B200 또는 GB200 row를 임시 proxy로 사용했다는 뜻이다.
- `optimized max`는 Dynamo/TRT-LLM/MTP 계열 stack row가 있어 그 안의 최고 `output_tok_s_mw`를 선택했다는 뜻이다.
- `public max`는 해당 optimized stack row가 없어 같은 조건 전체 public row 중 최고 `output_tok_s_mw`를 선택했다는 뜻이다.
- `frontier_composite`는 H200에서 `gptoss120b`, B200/GB200에서 DeepSeek V4 Pro(`dsv4`)와 Kimi K2.5(`kimik2.5`)를 쓰는 hybrid proxy다.
- 따라서 `frontier_composite`의 H200/B200/GB200 열은 순수 GPU generation uplift 비교가 아니라 GPU별 공개 frontier proxy source를 바꾼 workload reference다.
- Agentic 값은 아직 100k input급 matched benchmark가 아니라 Kimi K2.5 dynamic reasoning의 agentic/long ratio를 long_chat에 곱한 proxy estimate다.
- 이 표는 public benchmark/proxy이며 OpenAI, Anthropic, Google 등 closed production serving telemetry가 아니다.
