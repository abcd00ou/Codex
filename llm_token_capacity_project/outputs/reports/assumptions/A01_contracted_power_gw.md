<!-- Converted from A01_contracted_power_gw.docx -->

A01 contracted_power_gw

계약·발표 전력 capacity를 어떻게 읽을 것인가

# Executive Summary

학습용 starting band: 회사별 publicly announced/contracted/planned GW를 상한선으로 사용. 2026-2030 forecast에서는 active_power_gw와 분리.

이 리포트의 숫자 범위는 학습용 starting band입니다. 회사별 공식 telemetry가 공개되면 반드시 교체해야 하며, 공식 source가 없는 값은 fact가 아니라 estimate/proxy/scenario로 표시해야 합니다.

`contracted_power_gw`는 LLM token capacity simulation에서 숫자 정합성을 좌우하는 핵심 가정입니다. 이 문서는 해당 가정이 무엇을 의미하는지, 어떤 물리·운영·경제 원리에 의해 결정되는지, 공개자료를 어떻게 읽어야 하는지, 그리고 모델에 넣을 때 어떤 hallucination 위험을 피해야 하는지를 전문가 관점에서 정리합니다.

# 정의

contracted_power_gw는 특정 model owner 또는 그 host partner가 확보했거나 확보한다고 발표한 전력 capacity의 상한값이다. 여기에는 전력구매계약, utility interconnection, colocation lease, 데이터센터 캠퍼스 planned capacity, cloud partner capacity commitment가 섞일 수 있다. 중요한 점은 이 값이 token capacity가 아니라는 것이다. 전력 capacity는 토큰을 만드는 물리적 필요조건일 뿐, accelerator가 설치되고 cluster가 service-ready 상태가 되어야 비로소 active compute가 된다.

AI 인프라 뉴스에서 GW 숫자는 매우 강한 인상을 주지만, 그 GW가 무엇을 의미하는지 정의하지 않으면 모델을 망친다. 어떤 보도는 site total power를 말하고, 어떤 발표는 multi-year planned capacity를 말하며, 어떤 자료는 one training run의 peak power envelope를 말한다. contracted_power_gw는 이런 숫자 중 회사가 미래에 접근할 수 있는 전력 상한을 잡는 변수이며, active_power_gw, ai_it_load_gw, inference_gw와 같은 하위 변수와 절대 섞으면 안 된다.

# 전문가 관점의 운영 원리

전력 계약은 데이터센터 프로젝트의 시작점에 가깝다. utility가 power를 제공할 수 있어야 하고, 송전망과 변전소가 준비되어야 하며, 현장 배전, UPS, switchgear, backup generation, cooling plant, water 또는 liquid cooling loop가 모두 맞아야 한다. AI 데이터센터는 일반 enterprise data center보다 rack density가 높기 때문에 동일한 MW라도 설계 난이도가 다르다. GB200 NVL72 같은 rack-scale system은 rack 자체가 전력·냉각·네트워크 설계 단위로 바뀌기 때문에, utility 계약만으로 operational readiness를 판단할 수 없다.

계약 전력은 또한 business option value를 갖는다. model owner는 미래 model generation, inference growth, enterprise SLA, training run 경쟁에 대비해 capacity를 선점한다. 따라서 발표 capacity가 모두 바로 사용될 필요는 없다. 기업은 전력과 부지를 먼저 확보해 병목을 줄이고, accelerator supply와 제품 수요가 따라오는 속도에 맞춰 active capacity를 올릴 수 있다. 시뮬레이션에서 contracted_power_gw가 중요한 이유는 미래 상한을 정하기 때문이고, active_power_gw가 중요한 이유는 실제 token generation을 제한하기 때문이다.

# 현실적 숫자 범위 잡기

contracted_power_gw는 직접 발표가 있는 경우 그 숫자를 그대로 fact anchor로 둔다. 단, 문구가 planned인지 committed인지 operational인지 반드시 기록한다. 발표가 없으면 capex, data center lease, cloud agreement, utility interconnection queue, partner announcement를 조합해 estimate로만 둔다. company별 row에서는 single precise number보다 low/base/high band가 더 안전하다.

계약 전력의 현실적 범위는 기업 성격에 따라 다르다. OpenAI처럼 Stargate와 Oracle capacity 발표가 있는 경우 model owner attribution을 명시해야 한다. Anthropic은 AWS/Google host capacity와 Claude token owner attribution을 분리해야 한다. Google과 Meta처럼 자체 데이터센터와 accelerator strategy가 큰 기업은 company capex와 data center sustainability disclosure가 유용하다. 중국 업체는 공개성이 낮으므로 confidence를 낮추되, 단순히 낮은 공개성을 낮은 capacity로 해석하면 안 된다.

# 모델링 영향

contracted_power_gw는 forecast의 천장이다. active_power_gw가 이 값을 넘으면 모델 오류다. 하지만 token forecast에 직접 곱하면 안 된다. 올바른 순서는 contracted_power_gw에서 active_power_gw를 만들고, PUE와 AI workload share를 적용한 뒤, inference share와 tokens/sec/MW를 곱하는 것이다.

이 값이 10% 증가해도 단기 token forecast는 거의 변하지 않을 수 있다. 왜냐하면 2026년 forecast는 active deployment가 병목일 수 있기 때문이다. 반대로 2030년 forecast에서는 contracted capacity가 부족하면 active_power_gw의 상한이 되므로 장기 token capacity를 강하게 제한한다.

# Hallucination 위험

가장 큰 위험은 planned GW를 active inference GW로 표현하는 것이다. 두 번째 위험은 host provider capacity를 model owner capacity로 중복 계산하는 것이다. 세 번째 위험은 annual electricity consumption TWh와 instantaneous power GW를 섞는 것이다. 보고서 문구에는 반드시 planned/contracted/operational을 구분해야 한다.

# 실무 체크리스트

- 이 값은 fact, estimate, proxy, scenario 중 무엇인가?

- 단위가 GW, MW, TWh/year, tokens/sec, tokens/day 중 무엇인지 명확한가?

- 회사 공식자료가 직접 말한 숫자인가, 우리가 계산한 숫자인가?

- 값이 10% 변하면 2030 Base forecast가 얼마나 움직이는가?

- low/base/high band와 confidence가 같이 기록되어 있는가?

- 새로운 공식 source가 나오면 어떤 replacement path로 교체할 것인가?

# 권장 모델 필드

- assumption_id: A01_CONTRACTED_POWER_GW

- field_name: contracted_power_gw

- derivation_type: Fact / Estimate / Proxy / Scenario 중 하나

- confidence: High / Medium / Low

- replacement_path: 공식 source가 나오면 교체할 경로

# 참고자료

- IEA_AI: IEA, Energy and AI, IEA, 2025. https://www.iea.org/reports/energy-and-ai

- LBNL_DC: 2024 United States Data Center Energy Usage Report, LBNL / DOE, 2024. https://buildings.lbl.gov/publications/2024-lbnl-data-center-energy-usage-report

- CRS_DC: Data Centers and Their Energy Consumption: FAQ, Congressional Research Service, 2026. https://www.congress.gov/crs-product/R48646

- OPENAI_INFRA: Building the compute infrastructure for the intelligence age, OpenAI, 2025. https://openai.com/index/building-the-compute-infrastructure-for-the-intelligence-age/

- OPENAI_STARGATE: Five new Stargate sites and planned capacity, OpenAI, 2025. https://openai.com/index/five-new-stargate-sites/

# 저작권 및 사용 메모

이 문서는 외부 자료의 전문을 복제하지 않고, 모델링과 학습에 필요한 범위에서 해석과 요약을 제공합니다. 보고서에 수치를 사용할 때는 원문 source를 다시 열어 title, publisher, date, URL, 숫자 정의를 확인해야 합니다.
