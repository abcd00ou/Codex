# 동적 추론 / AI Agent 비용 분석

이 폴더는 논문 **The Cost of Dynamic Reasoning: Demystifying AI Agents and Test-Time Scaling from an AI Infrastructure Perspective**와 연결 GitHub 저장소 **VIA-Research/AgentBench**를 바탕으로, 전력 기반 token capacity 모델에 연결할 수 있는 내용을 정리한 분석 팩이다.

- 논문: https://arxiv.org/abs/2506.04301
- GitHub: https://github.com/VIA-Research/AgentBench
- 분석일: 2026-07-08

GitHub 저장소에는 agent 구현과 benchmark dataset은 있지만, 논문 figure 전체를 재현할 수 있는 모든 raw measurement table은 포함되어 있지 않다. 따라서 이 분석은 `논문에 보고된 시스템 수치`와 `공개 benchmark dataset 직접 집계`를 결합한 것이다.

## 우리 모델과의 연결

현재 전력 기반 token capacity 모델은 대략 다음 구조다.

```text
inference_tokens_per_day
= inference_MW
  * serving_output_tokens_per_second_per_MW
  * 86,400
```

동적 추론과 AI agent workload는 이 산식에서 `serving_output_tokens_per_second_per_MW`를 흔드는 요인이다. 일반 chat workload는 한 user request가 거의 하나의 LLM inference로 끝날 수 있지만, agent workflow는 다음 동작을 반복한다.

- LLM 호출
- tool 호출
- tool 결과를 context에 추가
- 이전 reasoning/history를 다시 prompt에 포함
- reflection 또는 tree search
- 여러 reasoning branch 병렬 실행

따라서 agent workload에서는 단순 InferenceX benchmark TPS/MW를 그대로 쓰면 과대평가될 가능성이 크다. 필요한 값은 다음에 가깝다.

```text
SLO를 만족하는 workload별 sustained output tokens/sec/MW
```

## 논문에서 모델 변수로 가져올 핵심 수치

| 항목 | 논문 보고 수치 | 모델 연결 |
|---|---:|---|
| Agent workflow inflation | agentic system은 CoT 대비 평균 9.2배 더 많은 LLM call | user request당 LLM 호출 수 multiplier |
| LATS 호출량 | 평균 71.0 LLM call/request | 고비용 parallel reasoning sensitivity |
| Latency breakdown | LLM inference 69.4%, tool execution 30.2% | GPU active/standby/idle power 분리 필요 |
| GPU idle | 외부/CPU tool workload에서 GPU idle이 최대 54.5% | tool wait가 전력 효율을 낮춤 |
| GPU 실행 시간 | prefill 4.7%, decode 74.1% | generated output token/TPOT 중심으로 봐야 함 |
| Prefix caching | prefill latency 60.1% 감소, end-to-end latency 15.7% 감소 | agent workload 효율 개선 계수 |
| Serving throughput | prefix caching이 ReAct serving throughput 평균 5.62배 개선 | prefix-cache hit rate를 주요 변수로 분리 |
| KV cache memory | tool-augmented agent는 CoT 대비 평균 3.0배, 최대 5.4배 KV memory 사용 | GPU 수요가 compute보다 memory/KV에 묶일 수 있음 |
| Serving QPS | ShareGPT 6.4 QPS, ReAct HotpotQA 2.6 QPS, ReAct WebShop 1.2 QPS | agent workload fit factor는 chat baseline보다 낮게 설정 |
| Iteration budget | 평균 latency/accuracy는 포화되지만 p95 latency는 계속 증가 | accuracy 최적화와 cost-efficiency 최적화 분리 |

## 공개 benchmark dataset 직접 집계

아래 파일에 AgentBench 저장소의 dataset을 직접 집계한 결과를 저장했다.

- `agentbench_dataset_profile.csv`

token 수는 정확한 tokenizer가 아니라 `max(word_count, chars/4)` 기반의 보수적 근사값이다. billing-grade token accounting이 아니라 workload shape 분석용이다.

주요 결과:

| Dataset | Field | Count | p50 approx tokens | p95 approx tokens | Max approx tokens |
|---|---|---:|---:|---:|---:|
| HotpotQA | question | 7,405 | 22 | 39 | 72 |
| HotpotQA | full_context | 7,405 | 1,378 | 2,136 | 4,218 |
| HotpotQA | question_plus_context | 7,405 | 1,403 | 2,160 | 4,248 |
| HumanEval | prompt | 164 | 99 | 229 | 340 |
| HumanEval | tests | 164 | 111 | 267 | 451 |
| MATH-500 | problem | 500 | 37 | 128 | 433 |
| MATH-500 | solution | 500 | 106 | 331 | 839 |
| WebShop | session IDs | 400 | N/A | N/A | N/A |

해석:

- HotpotQA는 context가 길어서 long-context / retrieval-heavy agent proxy로 좋다.
- HumanEval은 coding agent, test execution, tool feedback loop proxy로 볼 수 있다.
- MATH는 sequential reasoning, calculator/tool-use proxy로 볼 수 있다.
- WebShop은 repo에 session id만 포함되어 있어 실제 web navigation trace는 별도 WebShop 환경이 필요하다.

## Forecast용 scenario 구분

아래 파일에 scenario별 계수를 저장했다.

- `dynamic_reasoning_scenario_coefficients.csv`
- `inferencex_dynamic_reasoning_tps_gpu.csv`
- `inferencex_dynamic_reasoning_tps_gpu_summary.csv`
- `inferencex_dynamic_reasoning_tps_gpu.md`
- `inferencex_dynamic_reasoning_results_kr.md`

| Scenario | 의미 | 모델 사용처 |
|---|---|---|
| `static_chat_or_cot` | 단일 또는 거의 단일 LLM inference | 일반 assistant/chat baseline |
| `react_tool_agent` | multi-step tool-use agent | OpenAI/Claude/Copilot/Grok agent mix |
| `lats_parallel_reasoning` | tree search/parallel reasoning | high-end reasoning sensitivity |
| `llmcompiler_structured_planning` | DAG planning + tool overlap | enterprise workflow automation |

## NVIDIA 미래 GPU TPS/MW 설정

`nvidia_gpu_scaling_inputs.csv`가 GPU 스케일링의 사용자 입력 파일이다. H200/B200/B300/GB200/GB300은 공개 HBM bandwidth와 InferenceX all-in power를 사용하고, R200/VR200/R300/VR300/Post Rubin은 두 입력을 비워 둔다.

미래 GPU의 `hbm_bandwidth_tb_s`와 `all_in_kw`를 모두 양수로 입력한 뒤 아래 생성기를 다시 실행한다.

```bash
python tools/generate_nvidia_gpu_interactivity_reference.py
```

적용 수식은 다음과 같다.

```text
target TPS/MW
= source benchmark TPS/MW
  * (target HBM bandwidth / target all-in power)
  / (source HBM bandwidth / source all-in power)
```

- R200 계열은 `anchor_gpu`를 따라 B300 또는 GB300의 동일 proxy/workload/interactivity 선택 행을 사용한다.
- HBM bandwidth/all-in power 배율은 TPS/MW에만 적용한다.
- Interactivity, concurrency, precision, framework는 source InferenceX 행을 그대로 유지한다.
- 미래 GPU 입력 둘 중 하나가 비어 있으면 TPS/MW도 공란으로 남아 임의의 성능값을 만들지 않는다.
- 생성 워크북의 `00b_GPU_Scaling`에서도 R200 이후 HBM bandwidth와 all-in power를 직접 입력할 수 있으며, `01b_Interactivity`와 `00a_Proxy_TPS_MW`가 수식으로 갱신된다.

## InferenceX benchmark에 call multiplier 적용

InferenceX의 main model-config row를 그대로 두고 CoT/agentic call 수만 반영한 TPS/GPU overlay를 추가했다.

핵심 수식:

```text
scenario_total_tok_s_gpu
= InferenceX tok_s_gpu / scenario_call_multiplier

users_per_gpu
= scenario_total_tok_s_gpu / target_tok_s_user
```

적용 기준:

- CoT/단일 추론: `scenario_call_multiplier = 1.0`
- Agentic/ReAct 도구 사용: `scenario_call_multiplier = 9.2`
- Interactivity: `30`, `50`, `70` tok/s/user
- GPU, GPU 수, concurrency, ISL/OSL, framework, precision은 InferenceX 원본 row 값을 유지
- 모델별 `main_framework`, `main_precision`이 맞는 `is_main_model_config = yes` row만 사용

해석:

- CoT와 agentic은 workload 비중을 모르므로 섞지 않고 각각 계산한다.
- CoT는 call multiplier가 1.0이므로 원본 InferenceX TPS/GPU와 동일하다.
- Agentic은 call multiplier가 9.2이므로 scenario total TPS/GPU가 CoT 대비 10.9% 수준이다.
- Interactivity 30/50/70은 비중이 아니라 tok/s/user 요구 수준이며, `users/GPU` 계산에 사용한다.
- 이 값은 tool wait, prefix cache, KV cache pressure, SLO 실패율을 아직 simulation하지 않은 1차 보정치다.

## LLMServingSim power model과 연결

이 논문과 AgentBench는 LLMServingSim power model의 workload trace 설계에 바로 연결된다.

```text
AgentBench task + agent design
  -> calls/request
  -> tool wait time
  -> ISL/OSL growth
  -> branch concurrency
  -> prefix-cache reuse
  -> KV cache pressure
  -> LLMServingSim request trace
  -> power model active/standby/idle energy
  -> simulated_output_tokens / simulated_energy_j
  -> workload-specific tokens/sec/MW correction factor
```

우리 모델에서 쓸 수 있는 계수는 다음처럼 정의하는 것이 좋다.

```text
agent_workload_fit_factor
= simulated_sustained_output_tps_per_MW
  / InferenceX_public_output_tps_per_MW
```

이 값은 단순 utilization multiplier가 아니다. 다음 효과를 함께 반영하는 workload-specific correction factor다.

- user request당 LLM call 증가
- tool wait로 인한 GPU standby/idle
- input history 누적으로 인한 ISL 증가
- output token 분포 변화
- prefix caching hit rate
- KV cache memory pressure
- branch concurrency와 p95 latency
- SLO-valid throughput

## 회사별 연결

| 회사 | agent workload 관련성 | 추천 scenario mix |
|---|---|---|
| OpenAI | ChatGPT, API, reasoning, tool/agent 제품 | static + ReAct agent + LATS sensitivity |
| Anthropic | Claude coding, computer-use, long-context enterprise | ReAct agent + structured planning + long-context KV pressure |
| Google | Gemini product-integrated assistant, tool use | static + ReAct agent, multimodal은 별도 proxy 필요 |
| Meta | Meta AI consumer assistant, Llama proxy | static 중심, agent 비중은 낮은 scenario부터 |
| Microsoft | Copilot enterprise workflow, 반복 context | ReAct agent + LLMCompiler + prefix-cache-heavy |
| xAI | Grok interactive/reasoning | static + LATS/high-reasoning sensitivity |

## 박종세 교수님께 물어볼 질문

1. Agent workload의 `calls/request` 증가를 token capacity forecast에 넣을 때, 단순 multiplier로 넣는 것이 맞는지 아니면 LLMServingSim trace로 풀어야 하는지?
2. Tool wait로 인한 GPU idle/standby는 LLMServingSim power model에서 어떤 방식으로 energy/token에 반영되는지?
3. Prefix caching 효과를 장기 forecast에 넣을 때, prefill latency 개선과 KV memory 감소를 각각 어떻게 분리해야 하는지?
4. Agent workload에서 generated output token capacity보다 KV cache memory가 먼저 병목이 되는 경우를 어떻게 판단하는지?
5. LATS처럼 parallel reasoning을 쓰면 latency는 줄어도 concurrent LLM call과 memory pressure가 커지는데, 이를 GPU 수요로 환산하는 방법은 무엇인지?
6. 기업별 workload mix를 `static`, `tool-agent`, `parallel reasoning`, `structured planning`으로 나누는 접근이 serving-system 관점에서 타당한지?

## 파일 구성

```text
dynamic_reasoning_agent_cost/
  README.md
  agentbench_dataset_profile.csv
  dynamic_reasoning_scenario_coefficients.csv
  inferencex_dynamic_reasoning_results_kr.md
  inferencex_dynamic_reasoning_tps_gpu.md
  inferencex_dynamic_reasoning_tps_gpu.csv
  inferencex_dynamic_reasoning_tps_gpu_summary.csv
```

## 주의점

- AgentBench는 production telemetry가 아니라 benchmark/proxy다.
- 논문 실험은 Llama-3.1-8B 1x A100, Llama-3.1-70B 8x A100 기반이다.
- H200/B200/GB200 또는 custom accelerator에 적용하려면 InferenceX와 LLMServingSim calibration이 필요하다.
- CSV token estimate는 tokenizer-free 근사값이다.
- 회사별 OpenAI, Anthropic, Google, Meta, Microsoft, xAI 실제 workload 비중은 공개되어 있지 않으므로 scenario로 유지해야 한다.
