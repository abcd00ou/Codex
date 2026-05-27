# Fact Check Workflow

이 문서는 숫자를 바꿀 때의 작업 순서입니다. 목적은 hallucination을 줄이는 것이 아니라, 숫자가 바뀌는 이유를 보고서 안팎에서 추적 가능하게 만드는 것입니다.

## 1. 숫자 분류

모든 숫자는 아래 네 가지 중 하나로 분류합니다.

| 분류 | 의미 | 예시 |
|---|---|---|
| Fact | 공식 출처에서 직접 확인되는 숫자 | 공개 model parameter, 공식 GW 발표, model card |
| Estimate | fact를 기반으로 계산한 추정값 | active_power_gw, inference_gw |
| Proxy | 유사 모델/벤치마크를 참조한 대체값 | closed model tokens/sec/GPU proxy |
| Scenario | 2027-2030 operational ramp, mix, inference 배분 가정 | Bull/Base/Bear deployment multiplier |

## 2. 출처 확인 순서

1. 회사 공식 발표, IR, SEC filing, model card, technical report
2. Cloud/product 공식 문서
3. Standards body 또는 academic paper
4. SemiAnalysis InferenceX/InferenceMAX 등 benchmark reference
5. 언론/블로그/소셜은 원문 공식 출처로 추적 가능한 경우에만 참고

## 3. 업데이트 절차

1. 원문 URL, 제목, 발행자, 날짜를 확인합니다.
2. 숫자가 원문에 직접 있는지 확인합니다.
3. 숫자가 직접 없으면 derivation_type을 Estimate, Proxy, Scenario로 둡니다.
4. `tools/generate_llm_token_capacity_report.py`의 source, fact anchor, scenario 또는 benchmark 값을 수정합니다.
5. `data/source_review_log.md`에 확인 내역을 기록합니다.
6. 가정이나 계수가 바뀌면 `data/assumption_change_log.md`에 이유를 기록합니다.
7. 생성기를 다시 실행합니다.
8. Excel, PPT, HTML, MD, JSON이 모두 재생성됐는지 확인합니다.
9. `docs/hallucination_checklist.md`를 기준으로 보고 전 review를 합니다.

보고용 Excel 숫자 검증은 `04_Output`에서 `03_Calculation`의 수식으로 내려가고, 다시 `02_Inputs` 및 `01_Benchmark_Input`을 확인하는 순서로 수행합니다. source_id, replacement path, fact/assumption 구분은 workbook을 복잡하게 만들지 않도록 프로젝트 Markdown과 agent 기록에서 유지합니다.

그 다음 agent 기록의 fact-vs-assumption audit에서 주장 강도를 확인합니다. 공식 자료가 뒷받침하는 확인값과 모델 입력값은 분리하되, 이 긴 audit 표는 보고용 Excel에는 표시하지 않습니다.

## 4. 숫자 정합성 체크

필수 체크:

- active_power_gw가 contracted_power_gw보다 큰가?
- PUE 적용 전후 GW/MW 변환이 맞는가?
- inference share와 training share 합이 100%인가?
- `inference_gw * 1,000 * tokens/sec/MW * seconds/day`가 token/day와 일치하는가?
- annual token은 daily token * 365인가?
- benchmark layer와 main forecast가 50% 이상 차이 나는 row가 있는가?
- closed model parameter를 단일 precise number처럼 표현하지 않았는가?
- hosting provider capacity를 model owner token capacity로 잘못 귀속하지 않았는가?
- `contracted_power_gw`가 공식 계약 수치인지, 공식 capacity ceiling인지, scenario envelope인지 구분됐는가?
- `active_power_gw = contracted_power_gw * operational_deployment_share` 및 `active <= contracted` 통제가 적용됐는가?
- GPU/purpose-built accelerator share 합이 100%이며, 실제 fleet disclosure가 없는 share를 fact로 표현하지 않았는가?
- `tokens_per_second_per_mw`가 `01_Benchmark_Input`의 고정조건 output-token proxy와 `02_Inputs`의 GPU/purpose-built mix로 재계산되는가?
- comparable benchmark가 없는 purpose-built accelerator에 추가 uplift가 적용되지 않았는가?
- `utilization`, MoE uplift, software/architecture multiplier가 headline token 산식에서 제외됐는가?

## 5. 보고 문구 체크

임원용 문구는 다음 표현을 구분해야 합니다.

- "공식 발표에 따르면"
- "공식 발표 capacity를 기준으로 추정하면"
- "Base scenario에서는"
- "Benchmark sanity check 기준으로는"
- "현재 공개자료만으로는 확인 불가"

금지 표현:

- 공식 근거 없는 precise model parameter
- planned GW를 active inference GW처럼 표현
- benchmark proxy를 실제 회사 성능처럼 표현
- confidence가 낮은 추정치를 확정적 문장으로 표현

## 6. Sign-off 기준

보고 전 다음 조건을 충족해야 합니다.

- generator validation PASS
- 내부 Markdown hallucination checklist 검토 기록 존재
- PPT에 Hallucination 체크리스트 슬라이드 존재
- JSON에 sources, fact_anchors, benchmark_reference, hallucination_checklist 존재
- 변경된 숫자마다 source_id 또는 assumption_id 존재
- Excel에는 `00_Logic`, `01_Benchmark_Input`, `02_Inputs`, `03_Calculation`, `04_Output`, `05_Checks`만 존재
- 계산 결과 열과 output table이 값 붙여넣기가 아니라 formula로 저장됨
- 내부 fact/assumption audit와 source trace는 Markdown/agent 기록에 유지됨
- 변경 이유가 source log 또는 assumption log에 기록됨
