# Assumption Agent System

이 폴더는 LLM token capacity simulation의 11개 핵심 가정을 각각 독립 agent처럼 관리하기 위한 운영 구조입니다.

목표는 단순 자동 업데이트가 아닙니다. 각 agent가 자기 가정의 이론, 출처, 현재값, confidence, replacement path를 계속 학습하고, orchestrator가 전체 숫자 정합성을 검토하는 구조를 만드는 것입니다.

## Agent 구조

```text
agents/
  README.md
  shared/
    evidence_rules.md
    update_protocol.md
    source_quality.md
  orchestrator/
    README.md
    cycle_log.md
  review/
    logic_review_agent/
      README.md
      state.md
      checklist.md
      prompt.md
      output_template.md
  assumptions/
    A01_contracted_power_gw/
      README.md
      state.md
      evidence.md
      learning_queue.md
    ...
    A10_attribution_rule/
    A11_gpu_asic_mix/
```

## 역할

- **Assumption agents:** 각 가정의 fact, estimate, proxy, scenario를 관리합니다.
- **Orchestrator:** 가정 간 충돌, 단위 오류, 중복 귀속, token forecast 영향도를 검토합니다.
- **Logic Review Agent:** LLM serving/infra 고급 개발자 관점에서 계산식, 단위, attribution, benchmark mapping, 시나리오 로직을 독립 검수합니다.
- **Shared rules:** 모든 agent가 동일한 source quality와 update protocol을 따르게 합니다.

## 운영 원칙

1. agent는 자기 가정만 수정합니다.
2. source가 없으면 fact로 승격하지 않습니다.
3. 숫자를 바꾸면 `state.md`, `evidence.md`, `data/assumption_change_log.md`를 함께 갱신합니다.
4. cross-assumption 영향이 있으면 orchestrator에 flag를 올립니다.
5. 보고서 재생성 전에는 orchestrator가 전체 validation을 확인합니다.

## 학습 사이클

```text
source 발견
-> source quality 판정
-> fact/estimate/proxy/scenario 분류
-> agent evidence 업데이트
-> state 변경 후보 작성
-> logic review agent의 formula/unit/serving sanity review
-> orchestrator consistency review
-> generator 반영
-> Excel/PPT/HTML/MD/JSON 재생성
```

## Agent가 절대 하면 안 되는 것

- planned GW를 active inference GW로 직접 변환
- closed model parameter rumor를 fact로 기록
- benchmark 값을 production company metric으로 확정
- host capacity와 model-owner token을 중복 계산
- confidence가 낮은 estimate를 executive conclusion처럼 표현

## Logic Review Agent 사용 시점

- `generate_llm_token_capacity_report.py`의 산식, 계수, scenario multiplier를 바꿀 때
- InferenceX, arXiv, vendor benchmark를 `tokens_per_second_per_mw`, `joules_per_token`, `utilization`으로 반영할 때
- PPT/Excel의 headline number가 바뀌었을 때
- 특정 업체의 capacity attribution rule을 수정했을 때
- executive deck에 "constraint", "supply", "inference share" 같은 강한 결론을 넣기 전
