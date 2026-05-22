<!-- Converted from A03_pue.docx -->

A03 pue

facility power를 IT load로 바꾸는 핵심 계수

# Executive Summary

학습용 starting band: AI hyperscale 신규 facility 학습 band: 1.08-1.25. 보수적 전체 fleet 또는 미공개 site는 1.15-1.35.

이 리포트의 숫자 범위는 학습용 starting band입니다. 회사별 공식 telemetry가 공개되면 반드시 교체해야 하며, 공식 source가 없는 값은 fact가 아니라 estimate/proxy/scenario로 표시해야 합니다.

`pue`는 LLM token capacity simulation에서 숫자 정합성을 좌우하는 핵심 가정입니다. 이 문서는 해당 가정이 무엇을 의미하는지, 어떤 물리·운영·경제 원리에 의해 결정되는지, 공개자료를 어떻게 읽어야 하는지, 그리고 모델에 넣을 때 어떤 hallucination 위험을 피해야 하는지를 전문가 관점에서 정리합니다.

# 정의

PUE는 Power Usage Effectiveness의 약자로, 데이터센터 전체 facility energy를 IT equipment energy로 나눈 값이다. PUE가 1.2라면 facility가 1.2MW를 소비할 때 IT equipment가 약 1MW를 소비한다는 뜻이다. AI token forecast에서는 active facility power를 IT load로 바꾸기 위해 사용한다.

PUE는 단순하지만 오해가 많은 지표다. PUE는 compute efficiency가 아니라 facility efficiency다. 즉, PUE가 낮다고 GPU가 token을 더 잘 만든다는 뜻은 아니다. 같은 GPU cluster라도 냉각과 전력 변환 overhead가 낮으면 PUE가 낮아지고, 그만큼 facility power 중 IT load로 남는 몫이 커진다.

# 전문가 관점의 운영 원리

AI 데이터센터의 PUE는 cooling architecture에 민감하다. 고밀도 GPU rack은 공랭만으로 대응하기 어렵고, direct-to-chip liquid cooling, rear-door heat exchanger, facility water loop 같은 설계가 중요해진다. 전력 변환 효율, UPS topology, 외기 냉방 가능성, 기후, 물 사용 제약도 PUE를 좌우한다.

Google은 data center별 PUE를 공개하고, Meta도 지속가능성 자료에서 PUE를 보고한다. NREL의 HPC data center 사례는 고효율 설계가 매우 낮은 PUE를 달성할 수 있음을 보여준다. 반면 Uptime Institute의 survey는 industry average PUE가 신규 hyperscale best practice보다 높을 수 있음을 보여준다. 따라서 특정 company/site가 아니라 전체 fleet을 모델링할 때는 best-in-class PUE를 그대로 쓰면 낙관 편향이 생긴다.

# 현실적 숫자 범위 잡기

site-specific PUE가 공개되면 그 값을 사용한다. 공개되지 않으면 세 가지 층으로 나눈다. 첫째, hyperscaler owned new-build AI facility는 낮은 PUE band를 둘 수 있다. 둘째, colocation 또는 mixed workload facility는 중간 band가 안전하다. 셋째, 전력/냉각 retrofit 또는 급하게 ramp하는 site는 더 높은 PUE를 둘 수 있다.

AI rack density가 올라간다고 항상 PUE가 나빠지는 것은 아니다. liquid cooling과 전력 설계가 잘 되면 PUE는 낮아질 수 있다. 그러나 물 사용, heat rejection, partial load operation, redundancy design 때문에 실제 연평균 PUE는 design PUE와 다를 수 있다. 따라서 PUE는 design target이 아니라 annualized operational metric으로 이해해야 한다.

# 모델링 영향

PUE는 active_power_gw를 IT load로 나누는 계수다. PUE가 1.10이면 1GW facility power는 약 0.91GW IT load가 되고, PUE가 1.25이면 0.80GW IT load가 된다. PUE 차이 0.15는 대형 AI fleet에서는 수백 MW의 IT load 차이를 만들 수 있다.

다만 PUE sensitivity는 active_power_gw나 inference_share보다 보통 작을 수 있다. 예를 들어 PUE 1.15와 1.20의 차이는 약 4% 수준의 IT load 차이다. 하지만 임원 보고에서는 PUE를 무시하면 facility power와 IT power를 혼동하게 되므로 반드시 명시해야 한다.

# Hallucination 위험

PUE를 GPU efficiency처럼 설명하면 안 된다. 또 company average PUE를 특정 AI cluster PUE로 확정하면 안 된다. PUE는 연평균, campus-level, site-level, design target에 따라 값이 다르므로 source의 scope를 기록해야 한다.

# 실무 체크리스트

- 이 값은 fact, estimate, proxy, scenario 중 무엇인가?

- 단위가 GW, MW, TWh/year, tokens/sec, tokens/day 중 무엇인지 명확한가?

- 회사 공식자료가 직접 말한 숫자인가, 우리가 계산한 숫자인가?

- 값이 10% 변하면 2030 Base forecast가 얼마나 움직이는가?

- low/base/high band와 confidence가 같이 기록되어 있는가?

- 새로운 공식 source가 나오면 어떤 replacement path로 교체할 것인가?

# 권장 모델 필드

- assumption_id: A03_PUE

- field_name: pue

- derivation_type: Fact / Estimate / Proxy / Scenario 중 하나

- confidence: High / Medium / Low

- replacement_path: 공식 source가 나오면 교체할 경로

# 참고자료

- UPTIME_2024: Global Data Center Survey 2024, Uptime Institute, 2024. https://uptimeinstitute.com/resources/research-and-reports/uptime-institute-global-data-center-survey-results-2024

- GOOGLE_PUE: Power usage effectiveness, Google Data Centers, accessed 2026-05-15. https://datacenters.google/efficiency/

- NREL_PUE: High-Performance Computing Data Center PUE, NREL, accessed 2026-05-15. https://www.nrel.gov/computational-science/measuring-efficiency-pue

- META_SUST: Meta Sustainability: Data centers, Meta, accessed 2026-05-15. https://sustainability.atmeta.com/data-centers/

- LBNL_DC: 2024 United States Data Center Energy Usage Report, LBNL / DOE, 2024. https://buildings.lbl.gov/publications/2024-lbnl-data-center-energy-usage-report

# 저작권 및 사용 메모

이 문서는 외부 자료의 전문을 복제하지 않고, 모델링과 학습에 필요한 범위에서 해석과 요약을 제공합니다. 보고서에 수치를 사용할 때는 원문 source를 다시 열어 title, publisher, date, URL, 숫자 정의를 확인해야 합니다.
