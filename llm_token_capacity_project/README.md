# LLM Token Capacity Simulation Project

이 프로젝트는 상용 LLM 보유 업체의 2026-2030년 전력, GPU/ASIC, inference/training 비중, 토큰 생성량을 계속 팩트체크하면서 갱신하기 위한 독립 작업공간입니다.

## 목적

임원 보고용 시뮬레이션에서 가장 중요한 것은 예쁜 숫자가 아니라 숫자의 정합성입니다. 이 프로젝트는 다음 질문에 답하기 위해 유지합니다.

- 어떤 업체가 어떤 상용 LLM으로 토큰 생성을 주도하는가?
- 발표된 전력 capacity 중 실제 AI IT load와 inference에 쓰이는 비중은 어느 정도인가?
- 모델 파라미터, MoE active parameter, GPU/ASIC 보급, serving 효율이 토큰 생성량과 논리적으로 맞는가?
- 어떤 숫자가 fact이고, 어떤 숫자가 estimate/proxy/scenario인가?
- 보고서에 들어간 수치가 출처 원문, 계산식, 단위 변환, 시나리오 정의와 맞는가?

## 대상 업체

Core model-owner row는 다음 9개 업체입니다.

- Microsoft
- Google
- Meta
- xAI
- OpenAI
- Anthropic
- DeepSeek
- Alibaba
- Tencent

AWS, Oracle, CoreWeave 등은 model owner가 아니라 hosting/infrastructure capacity로만 attribution합니다.

## 폴더 구조

```text
llm_token_capacity_project/
  tools/
    generate_llm_token_capacity_report.py
  outputs/reports/
    llm_token_capacity_2026_2030.xlsx
    llm_token_capacity_2026_2030.pptx
    llm_token_capacity_2026_2030.html
    llm_token_capacity_2026_2030.md
    llm_token_capacity_2026_2030.json
  docs/
    assumption_learning_kit.md
    methodology.md
    fact_check_workflow.md
    hallucination_checklist.md
    automation.md
  data/
    source_review_log.md
    assumption_change_log.md
    source_watchlist.md
  agents/
    README.md
    shared/
    orchestrator/
    assumptions/
```

## 실행

루트 repo의 가상환경을 사용합니다.

```bash
.venv/bin/python llm_token_capacity_project/tools/generate_llm_token_capacity_report.py
```

생성물은 `llm_token_capacity_project/outputs/reports/` 아래에 저장됩니다.

## 업데이트 원칙

1. 새로운 숫자는 먼저 출처를 확인합니다.
2. 공식 출처가 있으면 source/fact anchor를 업데이트합니다.
3. 공식 출처가 없으면 estimate/proxy/scenario로 표시합니다.
4. 계산식 또는 계수를 바꾸면 `docs/methodology.md`와 `data/assumption_change_log.md`를 같이 갱신합니다.
5. 보고 전 `docs/hallucination_checklist.md`의 항목을 전부 확인합니다.

## 공부 도구

가정을 현실적인 숫자로 조정하기 전에 먼저 아래 자료로 배경지식을 맞춥니다.

- `docs/assumption_learning_kit.md`: 전력, PUE, inference mix, MoE, GPU/ASIC, tokens/sec/MW, utilization, attribution을 공부하는 워크북
- `outputs/reports/assumption_learning_kit_kr.pptx`: 같은 내용을 팀 설명용으로 만든 PPT
- `docs/llm_compute_power_theory_reader.md`: 계약 전력, compute allocation, training/inference 비중, prefill/decode, scheduler 관점의 이론 리더
- `outputs/reports/llm_compute_power_theory_reader_kr.docx`: 이론 리더의 Word 보고서 버전
- `docs/assumptions/`: 10개 핵심 가정별 장문 전문 리포트 Markdown
- `outputs/reports/assumptions/`: 10개 핵심 가정별 Word 보고서
- `agents/`: 각 가정을 agent처럼 계속 학습·검증·업데이트하기 위한 운영 폴더
- `docs/agent_learning_playbook.md`: agent를 실제로 학습시키고 업데이트하는 운영 playbook
- `data/source_watchlist.md`: InferenceX, Introl 등 다음 cycle에서 검토할 source 후보 목록
- `docs/reference_research_landscape.md`: 전문 리포트/논문/시장자료 reference landscape
- `docs/expert_learning_pack.md`: 52개 전문 source 기반의 6-module 심화 학습자료
- `outputs/reports/expert_learning_pack_kr.docx`: 심화 학습자료 Word 보고서
- `docs/agent_learning_expansion_pack.md`: 10개 agent별 2026-05-18 학습 확장 커리큘럼
- `outputs/reports/agent_learning_expansion_pack_kr.docx`: agent 학습 확장 Word 보고서

추천 학습 순서:

1. `llm_compute_power_theory_reader.md`로 전력과 compute allocation의 기본 이론을 공부합니다.
2. `assumption_learning_kit.md`의 1페이지 계산 지도를 읽습니다.
3. `expert_learning_pack.md`의 6-module study plan으로 전문 source를 넓게 학습합니다.
4. `agent_learning_expansion_pack.md`로 agent별 최신 학습 과제를 확인합니다.
5. `docs/assumptions/README.md`에서 10개 가정별 전문 리포트를 순서대로 읽습니다.
6. 매주 하나의 assumption module만 고릅니다.
7. 공식 source 2개에서 숫자 3개만 추출합니다.
8. 추출값을 fact/estimate/proxy/scenario로 분류합니다.
9. 변경 후보를 `data/assumption_change_log.md`에 기록합니다.

## Agent 기반 업데이트

각 가정은 `agents/assumptions/` 아래의 독립 agent가 관리합니다.

각 agent 폴더는 다음 파일을 가집니다.

- `README.md`: agent의 역할, 소유 field, watchout
- `state.md`: 현재 가정 band, confidence, 변경 후보
- `evidence.md`: source-reviewed evidence
- `learning_queue.md`: 다음 조사 과제와 agent prompt

운영 방식:

1. 가정을 바꾸기 전 해당 agent의 `learning_queue.md`에서 하나의 과제를 고릅니다.
2. source를 조사하고 `evidence.md`에 fact/estimate/proxy/scenario로 기록합니다.
3. `state.md`에 변경 후보를 적습니다.
4. cross-field 영향이 있으면 `agents/orchestrator/`에 review flag를 올립니다.
5. orchestrator 승인 후 generator를 수정하고 산출물을 재생성합니다.

Agent 구조가 깨지지 않았는지 확인합니다.

```bash
.venv/bin/python llm_token_capacity_project/tools/validate_assumption_agents.py
```

## 현재 산출물 상태

- 기준일: 2026-05-15
- 범위: 2026-2030
- 시나리오: Bear, Base, Bull, Grid-Constrained / Efficiency-Upside
- 검증 상태: generator validation PASS
- 주요 감사 레이어: formula assumptions, fact anchors, benchmark reference, hallucination checklist
