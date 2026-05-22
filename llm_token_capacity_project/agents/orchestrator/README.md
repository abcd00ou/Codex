# Orchestrator Agent

Orchestrator는 10개 assumption agent의 업데이트를 모아 전체 숫자 정합성을 검토합니다.

## 책임

- 가정 간 충돌 검토
- 단위 변환 오류 검토
- active_power_gw <= contracted_power_gw 확인
- inference_power_share + training_power_share = 100% 확인
- host/model-owner attribution 중복 제거
- benchmark_reference와 main forecast 괴리 검토
- executive wording에서 fact/estimate/proxy/scenario 구분 확인

## 입력

- `agents/assumptions/*/state.md`
- `agents/assumptions/*/evidence.md`
- `agents/review/logic_review_agent/state.md`
- `agents/review/logic_review_agent/checklist.md`
- `data/source_review_log.md`
- `data/assumption_change_log.md`
- `outputs/reports/llm_token_capacity_2026_2030.json`

## 출력

- `cycle_log.md`
- generator 업데이트 요청
- hallucination audit flag
- next learning queue

## Review Questions

1. 변경된 가정이 어느 forecast field에 영향을 주는가?
2. downstream token forecast가 10% 이상 움직이는가?
3. benchmark sanity layer와 괴리가 커졌는가?
4. 특정 회사가 host와 model owner 양쪽에 중복 반영됐는가?
5. executive summary 문구가 source confidence보다 강하지 않은가?
6. Logic Review Agent가 단위, 산식, benchmark mapping, attribution 중 하나라도 `blocker`로 표시했는가?

## Approval Criteria

orchestrator는 다음 조건을 만족할 때만 generator 반영을 승인합니다.

- evidence entry 존재
- state change reason 존재
- confidence와 replacement path 존재
- validation rule 위반 없음
- unresolved cross-agent conflict 없음
- logic review blocker 없음
