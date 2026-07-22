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
- Short chat: `ISL/OSL 1024/1024`
- Long chat: `ISL/OSL 8192/1024`
- Agentic: agentic trace 평균 `ISL/OSL 100947/860`을 직접 matched benchmark로 쓰지 않고, Kimi K2.5 dynamic reasoning row의 agentic/long ratio를 적용한다.
- Kimi 기준 agentic/long ratio: `10.9%` (`1 / 9.2x`). 산출 근거는 `inferencex_dynamic_reasoning_tps_gpu.csv`의 Kimi K2.5, `workload_type=agentic`, `ISL/OSL 8192/1024`, main config 675개 row의 median ratio다.
- 평균값: 위 필터를 통과한 row의 arithmetic mean. outlier와 row-count 부족의 영향을 받으므로 감사용으로 본다.
- 산식용 selected 값: p50 기반이며, long-context 값이 short-chat보다 높게 나오는 경우 `short_chat x 92%` guardrail을 적용한다.
- P50: 같은 필터에서 median. 엑셀 산식의 selected reference와 대조하기 위한 보조값

## 모델 매핑

| Report proxy model | InferenceX source model | 현재 적용 대상 |
|---|---|---|
| `gptoss120b` | `gptoss120b` | Microsoft, xAI, Tencent |
| `frontier_composite` | `dsv4 + kimik2.5` | OpenAI, Anthropic, Google |
| `llama70b` | `llama70b` | Meta |
| `dsr1` | `dsr1` | DeepSeek |
| `qwen3.5` | `qwen3.5` | Alibaba |

## 산식용 Selected TPS/MW

| Model | GPU | Short selected TPS/MW | Long selected TPS/MW | Agentic selected TPS/MW | Status |
|---|---:|---:|---:|---:|---|
| `gptoss120b` | H200 | 798,842 | 533,670 | 58,008 | direct / direct / long_chat x 10.9% |
| `gptoss120b` | B200 | 1,699,560 | 1,189,057 | 129,245 | direct / direct / long_chat x 10.9% |
| `gptoss120b` | GB200 | 1,699,560 | 1,189,057 | 129,245 | fallback:B200 / fallback:B200 / long_chat x 10.9% |
| `frontier_composite` | H200 | 123,401 | 68,876 | 7,487 | direct / direct / long_chat x 10.9% |
| `frontier_composite` | B200 | 95,664 | 72,484 | 7,879 | direct / direct / long_chat x 10.9% |
| `frontier_composite` | GB200 | 88,597 | 81,509 | 8,860 | direct / direct plus long<=short x 92% cap / long_chat x 10.9% |
| `llama70b` | H200 | 486,775 | 189,727 | 20,623 | direct / direct / long_chat x 10.9% |
| `llama70b` | B200 | 528,285 | 269,299 | 29,272 | direct / direct / long_chat x 10.9% |
| `llama70b` | GB200 | 528,285 | 269,299 | 29,272 | fallback:B200 / fallback:B200 / long_chat x 10.9% |
| `dsr1` | H200 | 103,277 | 74,906 | 8,142 | direct / direct / long_chat x 10.9% |
| `dsr1` | B200 | 127,759 | 74,797 | 8,130 | direct / direct / long_chat x 10.9% |
| `dsr1` | GB200 | 127,759 | 74,797 | 8,130 | fallback:B200 / fallback:B200 / long_chat x 10.9% |
| `qwen3.5` | H200 | 161,817 | 116,014 | 12,610 | direct / direct / long_chat x 10.9% |
| `qwen3.5` | B200 | 544,655 | 268,718 | 29,208 | direct / direct / long_chat x 10.9% |
| `qwen3.5` | GB200 | 544,655 | 268,718 | 29,208 | fallback:B200 / fallback:B200 / long_chat x 10.9% |

## Raw 평균 TPS/MW

| Model | InferenceX source | GPU | Short mean TPS/MW | Short n/status | Long mean TPS/MW | Long n/status | Agentic mean TPS/MW | Agentic basis |
|---|---|---:|---:|---|---:|---|---:|---|
| `gptoss120b` | `gptoss120b` | H200 | 782,278 | 382 / direct | 555,348 | 437 / direct | 60,364 | long_chat x 10.9% |
| `gptoss120b` | `gptoss120b` | B200 | 1,780,482 | 450 / direct | 1,176,458 | 450 / direct | 127,876 | long_chat x 10.9% |
| `gptoss120b` | `gptoss120b` | GB200 | 1,780,482 | 450 / fallback:B200 | 1,176,458 | 450 / fallback:B200 | 127,876 | long_chat x 10.9% |
| `frontier_composite` | `dsv4+kimik2.5` | H200 | 122,936 | 20 / direct | 68,566 | 20 / direct | 7,453 | long_chat x 10.9% |
| `frontier_composite` | `dsv4+kimik2.5` | B200 | 105,993 | 10 / direct | 96,796 | 14 / direct | 10,521 | long_chat x 10.9% |
| `frontier_composite` | `dsv4+kimik2.5` | GB200 | 86,132 | 9 / direct | 153,415 | 18 / direct | 16,676 | long_chat x 10.9% |
| `llama70b` | `llama70b` | H200 | 512,342 | 94 / direct | 188,633 | 88 / direct | 20,504 | long_chat x 10.9% |
| `llama70b` | `llama70b` | B200 | 579,686 | 107 / direct | 254,884 | 79 / direct | 27,705 | long_chat x 10.9% |
| `llama70b` | `llama70b` | GB200 | 579,686 | 107 / fallback:B200 | 254,884 | 79 / fallback:B200 | 27,705 | long_chat x 10.9% |
| `dsr1` | `dsr1` | H200 | 113,000 | 124 / direct | 72,373 | 122 / direct | 7,867 | long_chat x 10.9% |
| `dsr1` | `dsr1` | B200 | 134,815 | 147 / direct | 72,615 | 132 / direct | 7,893 | long_chat x 10.9% |
| `dsr1` | `dsr1` | GB200 | 134,815 | 147 / fallback:B200 | 72,615 | 132 / fallback:B200 | 7,893 | long_chat x 10.9% |
| `qwen3.5` | `qwen3.5` | H200 | 164,117 | 24 / direct | 115,660 | 23 / direct | 12,572 | long_chat x 10.9% |
| `qwen3.5` | `qwen3.5` | B200 | 542,922 | 30 / direct | 290,266 | 27 / direct | 31,551 | long_chat x 10.9% |
| `qwen3.5` | `qwen3.5` | GB200 | 542,922 | 30 / fallback:B200 | 290,266 | 27 / fallback:B200 | 31,551 | long_chat x 10.9% |

## Raw P50 TPS/MW

아래 표는 원천 row의 median이며, 산식용 long-context guardrail을 적용하지 않은 감사용 값이다.

| Model | GPU | Short raw p50 TPS/MW | Long raw p50 TPS/MW | Agentic raw p50 TPS/MW |
|---|---:|---:|---:|---:|
| `gptoss120b` | H200 | 798,842 | 533,670 | 58,008 |
| `gptoss120b` | B200 | 1,699,560 | 1,189,057 | 129,245 |
| `gptoss120b` | GB200 | 1,699,560 | 1,189,057 | 129,245 |
| `frontier_composite` | H200 | 123,401 | 68,876 | 7,487 |
| `frontier_composite` | B200 | 95,664 | 72,484 | 7,879 |
| `frontier_composite` | GB200 | 88,597 | 101,438 | 11,026 |
| `llama70b` | H200 | 486,775 | 189,727 | 20,622 |
| `llama70b` | B200 | 528,285 | 269,299 | 29,272 |
| `llama70b` | GB200 | 528,285 | 269,299 | 29,272 |
| `dsr1` | H200 | 103,277 | 74,906 | 8,142 |
| `dsr1` | B200 | 127,759 | 74,797 | 8,130 |
| `dsr1` | GB200 | 127,759 | 74,797 | 8,130 |
| `qwen3.5` | H200 | 161,817 | 116,014 | 12,610 |
| `qwen3.5` | B200 | 544,655 | 268,718 | 29,209 |
| `qwen3.5` | GB200 | 544,655 | 268,718 | 29,209 |

## 해석 메모

- `direct`는 해당 model/GPU/chat 조건에 맞는 InferenceX row가 존재한다는 뜻이다.
- `fallback`은 해당 GPU에 matched row가 없어서 가장 가까운 B200 또는 GB200 row를 임시 proxy로 사용했다는 뜻이다.
- `frontier_composite`는 DeepSeek V4 Pro(`dsv4`)와 Kimi K2.5(`kimik2.5`)를 함께 쓰는 proxy다.
- Kimi K2.5는 H200/B200 direct row를 보강하고, DeepSeek V4 Pro는 GB200 direct row를 보강한다.
- GB200 raw 평균에서는 long이 short보다 높게 보일 수 있어 산식용 selected 값에는 `long <= short x 92%` guardrail을 적용했다.
- Agentic 값은 아직 100k input급 matched benchmark가 아니라 Kimi K2.5 dynamic reasoning의 agentic/long ratio를 long_chat에 곱한 proxy estimate다.
- 이 표는 public benchmark/proxy이며 OpenAI, Anthropic, Google 등 closed production serving telemetry가 아니다.
