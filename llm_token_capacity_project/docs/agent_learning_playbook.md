# Assumption Agent Learning Playbook

이 문서는 10개 가정 agent를 실제로 계속 학습시키는 방법을 설명합니다. 목적은 agent가 인터넷에서 숫자를 주워오는 것이 아니라, 출처를 읽고 가정의 품질을 점진적으로 올리는 것입니다.

## 기본 철학

LLM token capacity simulation은 정답표가 있는 모델이 아닙니다. 기업 내부의 active power, training/inference split, serving utilization은 대부분 공개되지 않습니다. 따라서 agent의 목표는 숫자를 빠르게 바꾸는 것이 아니라 다음 세 가지를 지속적으로 개선하는 것입니다.

1. 어떤 숫자가 공식 fact인지 구분한다.
2. 어떤 숫자가 estimate/proxy/scenario인지 명확히 표시한다.
3. 새 evidence가 들어왔을 때 어떤 가정을 교체해야 하는지 판단한다.

## Agent별 학습 루프

각 agent는 아래 루프를 반복합니다.

```text
Read
-> Source search
-> Evidence classification
-> State proposal
-> Orchestrator review
-> Generator update
-> Output regeneration
-> Change log
```

## 1. Read

작업자는 먼저 해당 agent 폴더를 읽습니다.

```text
agents/assumptions/Axx_*/README.md
agents/assumptions/Axx_*/state.md
agents/assumptions/Axx_*/evidence.md
agents/assumptions/Axx_*/learning_queue.md
```

그리고 공통 규칙을 읽습니다.

```text
agents/shared/evidence_rules.md
agents/shared/source_quality.md
agents/shared/update_protocol.md
docs/hallucination_checklist.md
```

## 2. Source Search

source search는 다음 순서로 합니다.

1. 회사 공식 발표, product docs, model card, GitHub official repo
2. SEC/IR, earnings transcript, annual report
3. IEA, LBNL/DOE, CRS, Uptime Institute, Epoch AI 등 기관/연구 자료
4. arXiv 논문
5. 언론/시장조사 요약은 원문 추적이 가능할 때만 사용

## 3. Evidence Classification

각 source claim은 아래 중 하나로 분류합니다.

| Class | 사용 방식 |
|---|---|
| Fact | 공식 원문 숫자. fact anchor 가능 |
| Derived Estimate | fact로 계산한 값. 계산식 필요 |
| Proxy | benchmark 또는 유사 모델 대체값. confidence 제한 |
| Scenario | 미래 ramp/mix/efficiency 가정 |

## 4. Evidence 기록

`evidence.md`에는 원문 claim과 우리 해석을 분리해 기록합니다.

좋은 evidence row:

```text
source says: "planned capacity nearly 7 GW"
our interpretation: contracted/planned capacity upper bound, not active inference GW
model field impacted: contracted_power_gw
confidence: Medium
replacement path: site-level operational/energized disclosure
```

나쁜 evidence row:

```text
OpenAI has 7GW inference capacity.
```

이 문장은 planned, active, inference를 섞었기 때문에 금지합니다.

## 5. State Proposal

`state.md`의 Proposed Changes에는 바로 확정값을 쓰지 말고 후보를 남깁니다.

```text
old_value
new_value
reason
evidence_ids
confidence_change
downstream_impact
requires_orchestrator_review
```

## 6. Orchestrator Review가 필요한 경우

아래 변경은 반드시 orchestrator review가 필요합니다.

- active_power_gw 변경
- inference_power_share 변경
- training_power_share 변경
- tokens_per_second_per_mw 변경
- utilization 변경
- attribution_rule 변경
- company token forecast 10% 이상 이동
- benchmark와 main forecast 괴리 50% 이상 발생

## 7. Generator Update

승인 후에만 generator를 수정합니다.

```bash
.venv/bin/python llm_token_capacity_project/tools/generate_llm_token_capacity_report.py
```

## 8. Verification

기본 검증:

```bash
.venv/bin/python llm_token_capacity_project/tools/validate_assumption_agents.py
.venv/bin/python llm_token_capacity_project/tools/generate_llm_token_capacity_report.py
```

문서 산출물까지 다시 만들 경우:

```bash
/Users/idongseong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 llm_token_capacity_project/tools/generate_assumption_textbook.py
/Users/idongseong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 llm_token_capacity_project/tools/generate_compute_power_theory_reader.py
```

## 9. 첫 번째 추천 Cycle

첫 cycle은 A01/A02에 집중합니다.

### Cycle 1 Scope

- A01 contracted_power_gw
- A02 active_power_gw

### 이유

전력 상한과 실제 operational deployment를 분리하지 않으면 downstream token forecast가 모두 과대평가될 수 있습니다.

### 조사 질문

1. 각 회사의 발표 capacity는 planned, committed, operational 중 무엇인가?
2. site-level energization 또는 cluster online evidence가 있는가?
3. capacity owner와 model owner가 다른가?
4. 2026 active conversion ratio를 조정할 evidence가 있는가?
5. 2030 active conversion ratio를 조정할 evidence가 있는가?

## 10. 보고 전 문구 규칙

Executive report에서는 아래 표현을 구분합니다.

- "공식 발표에 따르면"
- "공식 발표 capacity를 상한으로 보면"
- "Base scenario에서는"
- "benchmark sanity check 기준으로는"
- "현재 공개자료만으로는 확인 불가"

강한 문장은 강한 evidence가 있을 때만 씁니다.
