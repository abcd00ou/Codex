# Update Protocol

가정 agent가 새로운 source나 숫자를 반영할 때 따르는 절차입니다.

## 1. Read First

작업 전 읽을 파일:

- 해당 agent의 `README.md`
- 해당 agent의 `state.md`
- 해당 agent의 `evidence.md`
- `agents/shared/evidence_rules.md`
- `docs/assumptions/{agent_id}_*.md`
- `docs/hallucination_checklist.md`

## 2. Classify

새 정보가 무엇인지 분류합니다.

```text
Fact / Derived Estimate / Proxy / Scenario
```

Fact로 승격하려면 source 원문에 숫자나 문구가 직접 있어야 합니다.

## 3. Update Evidence

`evidence.md`에 source entry를 추가합니다.

핵심은 "원문이 말한 것"과 "우리가 해석한 것"을 분리하는 것입니다.

## 4. Propose State Change

`state.md`에 즉시 확정값을 덮어쓰기보다, 먼저 변경 후보를 기록합니다.

```text
proposed_change
old_value
new_value
reason
confidence_change
downstream_impact
requires_orchestrator_review
```

## 5. Orchestrator Review

다음 경우에는 반드시 orchestrator review가 필요합니다.

- active_power_gw 변경
- inference_power_share 변경
- tokens_per_second_per_mw 변경
- attribution_rule 변경
- benchmark와 forecast 차이가 50% 이상
- company aggregate token forecast가 10% 이상 이동

## 6. Regenerate Outputs

orchestrator 승인 후 생성기를 실행합니다.

```bash
.venv/bin/python llm_token_capacity_project/tools/generate_llm_token_capacity_report.py
```

## 7. Log

다음 파일을 갱신합니다.

- `data/source_review_log.md`
- `data/assumption_change_log.md`
- `agents/orchestrator/cycle_log.md`
