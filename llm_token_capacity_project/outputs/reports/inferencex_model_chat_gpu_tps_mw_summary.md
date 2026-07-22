# InferenceX Model x Chat Type x GPU TPS/MW Summary

작성일: 2026-07-22

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
- Agentic: agentic trace 평균 `ISL/OSL 100947/860`을 직접 matched benchmark로 쓰지 않고, `long_chat TPS/MW x 55%`로 산출
- 평균값: 위 필터를 통과한 row의 arithmetic mean. outlier와 row-count 부족의 영향을 받으므로 감사용으로 본다.
- 산식용 selected 값: p50 기반이며, long-context 값이 short-chat보다 높게 나오는 경우 `short_chat x 92%` guardrail을 적용한다.
- P50: 같은 필터에서 median. 엑셀 산식의 selected reference와 대조하기 위한 보조값

## 모델 매핑

| Report proxy model | InferenceX source model | 현재 적용 대상 |
|---|---|---|
| `gptoss120b` | `gptoss120b` | Microsoft, xAI, Tencent |
| `deepseekv4pro` | `dsv4` | OpenAI, Anthropic, Google |
| `llama70b` | `llama70b` | Meta |
| `dsr1` | `dsr1` | DeepSeek |
| `qwen3.5` | `qwen3.5` | Alibaba |

## 산식용 Selected TPS/MW

| Model | GPU | Short selected TPS/MW | Long selected TPS/MW | Agentic selected TPS/MW | Status |
|---|---:|---:|---:|---:|---|
| `gptoss120b` | H200 | 798,842 | 533,670 | 293,518 | direct / direct / long_chat x 55% |
| `gptoss120b` | B200 | 1,699,560 | 1,189,057 | 653,981 | direct / direct / long_chat x 55% |
| `gptoss120b` | GB200 | 1,699,560 | 1,189,057 | 653,981 | fallback:B200 / fallback:B200 / long_chat x 55% |
| `deepseekv4pro` | H200 | 88,597 | 81,509 | 44,830 | fallback:GB200 / fallback:B200 plus long<=short x 92% cap / long_chat x 55% |
| `deepseekv4pro` | B200 | 88,597 | 81,509 | 44,830 | fallback:GB200 / fallback:B200 plus long<=short x 92% cap / long_chat x 55% |
| `deepseekv4pro` | GB200 | 88,597 | 81,509 | 44,830 | direct / direct plus long<=short x 92% cap / long_chat x 55% |
| `llama70b` | H200 | 486,775 | 189,727 | 104,350 | direct / direct / long_chat x 55% |
| `llama70b` | B200 | 528,285 | 269,299 | 148,114 | direct / direct / long_chat x 55% |
| `llama70b` | GB200 | 528,285 | 269,299 | 148,114 | fallback:B200 / fallback:B200 / long_chat x 55% |
| `dsr1` | H200 | 103,277 | 74,906 | 41,198 | direct / direct / long_chat x 55% |
| `dsr1` | B200 | 127,759 | 74,797 | 41,138 | direct / direct / long_chat x 55% |
| `dsr1` | GB200 | 127,759 | 74,797 | 41,138 | fallback:B200 / fallback:B200 / long_chat x 55% |
| `qwen3.5` | H200 | 161,817 | 116,014 | 63,808 | direct / direct / long_chat x 55% |
| `qwen3.5` | B200 | 544,655 | 268,718 | 147,795 | direct / direct / long_chat x 55% |
| `qwen3.5` | GB200 | 544,655 | 268,718 | 147,795 | fallback:B200 / fallback:B200 / long_chat x 55% |

## Raw 평균 TPS/MW

| Model | InferenceX source | GPU | Short mean TPS/MW | Short n/status | Long mean TPS/MW | Long n/status | Agentic mean TPS/MW | Agentic basis |
|---|---|---:|---:|---|---:|---|---:|---|
| `gptoss120b` | `gptoss120b` | H200 | 782,278 | 382 / direct | 555,348 | 437 / direct | 305,441 | long_chat x 55% |
| `gptoss120b` | `gptoss120b` | B200 | 1,780,482 | 450 / direct | 1,176,458 | 450 / direct | 647,052 | long_chat x 55% |
| `gptoss120b` | `gptoss120b` | GB200 | 1,780,482 | 450 / fallback:B200 | 1,176,458 | 450 / fallback:B200 | 647,052 | long_chat x 55% |
| `deepseekv4pro` | `dsv4` | H200 | 86,132 | 9 / fallback:GB200 | 151,336 | 4 / fallback:B200 | 83,235 | long_chat x 55% |
| `deepseekv4pro` | `dsv4` | B200 | 86,132 | 9 / fallback:GB200 | 151,336 | 4 / direct | 83,235 | long_chat x 55% |
| `deepseekv4pro` | `dsv4` | GB200 | 86,132 | 9 / direct | 153,415 | 18 / direct | 84,378 | long_chat x 55% |
| `llama70b` | `llama70b` | H200 | 512,342 | 94 / direct | 188,633 | 88 / direct | 103,748 | long_chat x 55% |
| `llama70b` | `llama70b` | B200 | 579,686 | 107 / direct | 254,884 | 79 / direct | 140,186 | long_chat x 55% |
| `llama70b` | `llama70b` | GB200 | 579,686 | 107 / fallback:B200 | 254,884 | 79 / fallback:B200 | 140,186 | long_chat x 55% |
| `dsr1` | `dsr1` | H200 | 113,000 | 124 / direct | 72,373 | 122 / direct | 39,805 | long_chat x 55% |
| `dsr1` | `dsr1` | B200 | 134,815 | 147 / direct | 72,615 | 132 / direct | 39,938 | long_chat x 55% |
| `dsr1` | `dsr1` | GB200 | 134,815 | 147 / fallback:B200 | 72,615 | 132 / fallback:B200 | 39,938 | long_chat x 55% |
| `qwen3.5` | `qwen3.5` | H200 | 164,117 | 24 / direct | 115,660 | 23 / direct | 63,613 | long_chat x 55% |
| `qwen3.5` | `qwen3.5` | B200 | 542,922 | 30 / direct | 290,266 | 27 / direct | 159,646 | long_chat x 55% |
| `qwen3.5` | `qwen3.5` | GB200 | 542,922 | 30 / fallback:B200 | 290,266 | 27 / fallback:B200 | 159,646 | long_chat x 55% |

## Raw P50 TPS/MW

아래 표는 원천 row의 median이며, 산식용 long-context guardrail을 적용하지 않은 감사용 값이다.

| Model | GPU | Short raw p50 TPS/MW | Long raw p50 TPS/MW | Agentic raw p50 TPS/MW |
|---|---:|---:|---:|---:|
| `gptoss120b` | H200 | 798,842 | 533,670 | 293,518 |
| `gptoss120b` | B200 | 1,699,560 | 1,189,057 | 653,981 |
| `gptoss120b` | GB200 | 1,699,560 | 1,189,057 | 653,981 |
| `deepseekv4pro` | H200 | 88,597 | 136,273 | 74,950 |
| `deepseekv4pro` | B200 | 88,597 | 136,273 | 74,950 |
| `deepseekv4pro` | GB200 | 88,597 | 101,438 | 55,791 |
| `llama70b` | H200 | 486,775 | 189,727 | 104,350 |
| `llama70b` | B200 | 528,285 | 269,299 | 148,114 |
| `llama70b` | GB200 | 528,285 | 269,299 | 148,114 |
| `dsr1` | H200 | 103,277 | 74,906 | 41,198 |
| `dsr1` | B200 | 127,759 | 74,797 | 41,138 |
| `dsr1` | GB200 | 127,759 | 74,797 | 41,138 |
| `qwen3.5` | H200 | 161,817 | 116,014 | 63,808 |
| `qwen3.5` | B200 | 544,655 | 268,718 | 147,795 |
| `qwen3.5` | GB200 | 544,655 | 268,718 | 147,795 |

## 해석 메모

- `direct`는 해당 model/GPU/chat 조건에 맞는 InferenceX row가 존재한다는 뜻이다.
- `fallback`은 해당 GPU에 matched row가 없어서 가장 가까운 B200 또는 GB200 row를 임시 proxy로 사용했다는 뜻이다.
- DeepSeek V4 Pro는 현재 InferenceX source model `dsv4`로 매핑되며, H200 direct row가 부족하다.
- DeepSeek V4 Pro raw 평균에서는 long이 short보다 높게 보일 수 있다. 이는 long row의 일부 높은 concurrency/output-only TPS row와 부족한 direct short row 때문이며, 산식용 selected 값에는 `long <= short x 92%` guardrail을 적용했다.
- Agentic 값은 아직 100k input급 matched benchmark가 아니라 trace-derived estimate다.
- 이 표는 public benchmark/proxy이며 OpenAI, Anthropic, Google 등 closed production serving telemetry가 아니다.
