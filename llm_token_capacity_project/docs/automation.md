# Automation Notes

이 문서는 자동화 작업자가 이 프로젝트를 반복 갱신할 때 따라야 할 실행 절차입니다.

## 기본 명령

```bash
.venv/bin/python -m py_compile llm_token_capacity_project/tools/generate_llm_token_capacity_report.py
.venv/bin/python llm_token_capacity_project/tools/generate_llm_token_capacity_report.py
```

## 검증 명령

```bash
.venv/bin/python llm_token_capacity_project/tools/validate_assumption_agents.py
.venv/bin/python - <<'PY'
import json, zipfile
from openpyxl import load_workbook
from pptx import Presentation

base = 'llm_token_capacity_project/outputs/reports/llm_token_capacity_2026_2030'
with open(base + '.json', encoding='utf-8') as f:
    data = json.load(f)

assert data['validation']['status'] == 'PASS'
assert 'Anthropic' in data['metadata']['companies']
assert len(data['hallucination_checklist']) >= 15
assert len(data['benchmark_reference']) == 45

wb = load_workbook(base + '.xlsx', data_only=True)
assert '00_formula_assumptions' in wb.sheetnames
assert '08d_benchmark_reference' in wb.sheetnames
assert '11_hallucination_checklist' in wb.sheetnames

prs = Presentation(base + '.pptx')
assert len(prs.slides) >= 14

for suffix in ['.xlsx', '.pptx']:
    with zipfile.ZipFile(base + suffix) as z:
        assert z.testzip() is None

print('llm token capacity project verification PASS')
PY
```

## 자동화 에이전트 작업 규칙

1. 숫자를 바꾸기 전에 `docs/methodology.md`를 읽습니다.
2. 출처를 추가하면 source_id를 안정적으로 유지합니다.
3. 공식 출처가 아니면 confidence를 높이지 않습니다.
4. benchmark는 forecast가 아니라 sanity check로만 사용합니다.
5. 생성물은 항상 JSON, XLSX, PPTX, HTML, MD를 같이 갱신합니다.
6. 변경 후 `docs/hallucination_checklist.md` 기준으로 review합니다.
7. assumptions 변경은 `data/assumption_change_log.md`에 남깁니다.
8. source 확인은 `data/source_review_log.md`에 남깁니다.

## Assumption Agent 자동화

가정별 업데이트는 `agents/assumptions/`의 agent 폴더를 기준으로 수행합니다.

```text
agents/assumptions/A01_contracted_power_gw/
  README.md
  state.md
  evidence.md
  learning_queue.md
```

Agent loop:

1. 해당 agent의 `learning_queue.md`에서 pending task 하나를 선택합니다.
2. `agents/shared/evidence_rules.md`와 `source_quality.md`를 읽습니다.
3. source를 확인하고 `evidence.md`에 evidence row를 추가합니다.
4. 변경이 필요하면 `state.md`의 Proposed Changes에 후보를 기록합니다.
5. active power, inference share, tokens/MW, utilization, attribution 변경은 반드시 orchestrator review를 거칩니다.
6. 승인 후 generator와 산출물을 업데이트합니다.

## 추후 자동화 후보

- source_id별 URL alive check
- source quote pack 자동 생성
- benchmark/main forecast outlier 자동 표시
- Excel sheet별 required-column 검증
- PPT slide count 및 주요 제목 검증
- confidence downgrade 후보 자동 생성
- 신규 official source가 발견되면 assumption replacement path 제안
- `agent_learning_expansion_pack.md`의 source를 agent별 `evidence.md`로 승격하는 semi-automated review form
