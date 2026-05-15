# A02 active_power_gw

**부제:** 실제로 AI cluster가 쓸 수 있는 운영 전력을 추정하는 법

**생성일:** 2026-05-15

**학습용 starting band:** 2026 active/contracted 15-45%, 2030 active/contracted 45-80%를 학습용 band로 시작. site-level disclosure가 있으면 교체.

> 이 리포트의 숫자 범위는 학습용 starting band입니다. 회사별 공식 telemetry가 공개되면 반드시 교체해야 하며, 공식 source가 없는 값은 fact가 아니라 estimate/proxy/scenario로 표시해야 합니다.

## Executive Summary

`active_power_gw`는 LLM token capacity simulation에서 숫자 정합성을 좌우하는 핵심 가정입니다. 이 문서는 해당 가정이 무엇을 의미하는지, 어떤 물리·운영·경제 원리에 의해 결정되는지, 공개자료를 어떻게 읽어야 하는지, 그리고 모델에 넣을 때 어떤 hallucination 위험을 피해야 하는지를 전문가 관점에서 정리합니다.

## 정의

active_power_gw는 발표 또는 계약된 전력 중 실제로 데이터센터 facility에 들어와 운영 가능한 상태가 된 전력이다. 이 값은 전력망 연결, 변전, 냉각, 랙 설치, accelerator delivery, cluster qualification을 통과한 capacity를 의미한다. token forecast에서는 contracted_power_gw보다 active_power_gw가 훨씬 직접적인 제한 조건이다.

active_power_gw는 여전히 facility-level 전력일 수 있다. 따라서 이 값 자체가 GPU board power 또는 inference power는 아니다. PUE를 적용해 IT load로 바꾸고, AI workload share를 적용해 AI IT load를 만든 뒤, inference/training split을 적용해야 한다.

## 전문가 관점의 운영 원리

데이터센터의 active capacity는 건설 완료와 동일하지 않다. building shell이 완성되어도 utility energization, switchgear test, cooling commissioning, network turn-up, server burn-in, orchestration integration이 남는다. AI cluster는 일반 서버보다 failure domain이 크다. 수만 GPU training cluster는 일부 rack만 준비되어도 전체 cluster efficiency가 크게 떨어질 수 있다. inference fleet은 더 작은 단위로 배치할 수 있지만, latency SLO와 regional redundancy 때문에 역시 완전한 active capacity가 필요하다.

Google Cloud TPU 문서는 training과 serving workload의 provisioning 차이를 보여준다. 같은 accelerator product라도 training job은 throughput과 availability에, serving job은 latency에 최적화된다. 이는 active_power_gw가 단순 전력 가동 여부를 넘어, 해당 cluster가 어떤 workload에 적합하게 provisioned 되었는지를 함께 봐야 함을 의미한다.

AWS Project Rainier처럼 특정 partner를 위한 대형 cluster가 online이라는 발표는 active compute에 가까운 신호다. 그러나 발표가 'nearly half a million Trainium2 chips' 같은 accelerator count를 제공하더라도, 그 전체가 특정 시점에 inference로 쓰인다는 뜻은 아니다. active compute와 workload allocation은 분리해야 한다.

## 현실적 숫자 범위 잡기

active_power_gw를 추정할 때는 milestone 기반 접근이 가장 안전하다. 첫째, announced/contracted capacity가 있는지 확인한다. 둘째, construction 또는 energized milestone이 있는지 본다. 셋째, accelerator delivery 또는 cluster online 발표가 있는지 본다. 넷째, 서비스 배포 또는 API availability 증가와 연결되는지 본다. 이 네 단계가 모두 확인되면 active 비율을 높일 수 있다.

공개자료가 부족하면 deployment ratio를 시나리오로 둔다. 2026년에는 많은 AI capacity가 ramp 중일 수 있으므로 active/contracted ratio를 낮게 잡고, 2030년에는 프로젝트 완공과 accelerator delivery가 누적되며 비율이 올라가는 구조가 현실적이다. 단, 전력망 병목, transformer shortage, cooling constraint, permitting delay가 있으면 2030년에도 active conversion이 낮을 수 있다.

## 모델링 영향

active_power_gw는 token forecast의 가장 큰 sensitivity driver 중 하나다. 모든 하위 계산이 active power에서 시작하기 때문이다. active_power_gw가 10% 오르면, PUE, AI workload share, inference share, tokens/sec/MW, utilization이 같다는 조건에서 token forecast도 거의 10% 오른다.

하지만 active_power_gw는 confidence가 낮은 경우가 많다. 따라서 단일 base 값만 두면 보고서가 취약해진다. 반드시 bear/base/bull deployment ratio를 두고, site-level source가 나오면 교체할 replacement path를 명시해야 한다.

## Hallucination 위험

active_power_gw를 발표 GW와 같게 두는 것이 가장 위험하다. 두 번째 위험은 accelerator count에서 board power만 곱해 facility active power를 추정하는 것이다. board power에는 CPU, memory, networking, power conversion, cooling overhead가 빠져 있다. 세 번째 위험은 online cluster 발표를 연중 평균 active power로 그대로 쓰는 것이다.

## 실무 체크리스트

- 이 값은 fact, estimate, proxy, scenario 중 무엇인가?
- 단위가 GW, MW, TWh/year, tokens/sec, tokens/day 중 무엇인지 명확한가?
- 회사 공식자료가 직접 말한 숫자인가, 우리가 계산한 숫자인가?
- 값이 10% 변하면 2030 Base forecast가 얼마나 움직이는가?
- low/base/high band와 confidence가 같이 기록되어 있는가?
- 새로운 공식 source가 나오면 어떤 replacement path로 교체할 것인가?

## 권장 모델 필드

- assumption_id: `A02_ACTIVE_POWER_GW`
- field_name: `active_power_gw`
- derivation_type: Fact / Estimate / Proxy / Scenario 중 하나
- confidence: High / Medium / Low
- replacement_path: 공식 source가 나오면 교체할 경로

## 참고자료

- **LBNL_DC:** 2024 United States Data Center Energy Usage Report, LBNL / DOE, 2024. https://buildings.lbl.gov/publications/2024-lbnl-data-center-energy-usage-report
- **CRS_DC:** Data Centers and Their Energy Consumption: FAQ, Congressional Research Service, 2026. https://www.congress.gov/crs-product/R48646
- **IEA_AI:** IEA, Energy and AI, IEA, 2025. https://www.iea.org/reports/energy-and-ai
- **GOOGLE_TPU_V5E:** Cloud TPU v5e documentation, Google Cloud, accessed 2026-05-15. https://docs.cloud.google.com/tpu/docs/v5e
- **AWS_RAINIER:** AWS activates Project Rainier, Amazon, 2025. https://www.aboutamazon.com/news/aws/aws-project-rainier-ai-trainium-chips-compute-cluster
- **NVIDIA_GB200:** NVIDIA GB200 NVL72, NVIDIA, accessed 2026-05-15. https://www.nvidia.com/en-us/data-center/gb200-nvl72/

## 저작권 및 사용 메모

이 문서는 외부 자료의 전문을 복제하지 않고, 모델링과 학습에 필요한 범위에서 해석과 요약을 제공합니다. 보고서에 수치를 사용할 때는 원문 source를 다시 열어 title, publisher, date, URL, 숫자 정의를 확인해야 합니다.