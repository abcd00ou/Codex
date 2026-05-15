# A10 attribution_rule

**부제:** host capacity와 model-owner token을 중복 없이 귀속하는 법

**생성일:** 2026-05-15

**학습용 starting band:** model-owner forecast에서는 token을 모델 소유자에게 귀속. host capacity는 별도 infrastructure layer로 기록.

> 이 리포트의 숫자 범위는 학습용 starting band입니다. 회사별 공식 telemetry가 공개되면 반드시 교체해야 하며, 공식 source가 없는 값은 fact가 아니라 estimate/proxy/scenario로 표시해야 합니다.

## Executive Summary

`attribution_rule`는 LLM token capacity simulation에서 숫자 정합성을 좌우하는 핵심 가정입니다. 이 문서는 해당 가정이 무엇을 의미하는지, 어떤 물리·운영·경제 원리에 의해 결정되는지, 공개자료를 어떻게 읽어야 하는지, 그리고 모델에 넣을 때 어떤 hallucination 위험을 피해야 하는지를 전문가 관점에서 정리합니다.

## 정의

attribution_rule은 특정 전력, accelerator, cloud capacity, token output을 어느 회사 row에 귀속할지 정하는 규칙이다. LLM 생태계에서는 model owner, cloud host, infrastructure investor, product distributor가 다를 수 있기 때문에 attribution이 없으면 숫자가 쉽게 중복된다.

예를 들어 Oracle data center capacity가 OpenAI를 위해 사용된다면 model-owner token forecast에서는 OpenAI capacity로 귀속할 수 있다. 그러나 infrastructure revenue 또는 data center capex 모델에서는 Oracle 또는 project owner layer에 기록해야 한다. 같은 capacity를 OpenAI와 Oracle 양쪽 token capacity에 더하면 중복 계산이다.

## 전문가 관점의 운영 원리

OpenAI/Microsoft 관계는 attribution의 대표적인 난제다. Microsoft Copilot token, Azure-hosted OpenAI API, OpenAI direct ChatGPT/API token, Azure-hosted third-party model token이 섞일 수 있다. model owner 기준 forecast에서는 GPT 계열 token은 OpenAI에, Microsoft-owned Phi/MAI 계열 token은 Microsoft에, Copilot product traffic이 GPT를 호출하는 경우는 token owner와 product owner를 별도 표기해야 한다.

Anthropic도 마찬가지다. AWS Project Rainier와 Trainium2 capacity는 Anthropic Claude training/inference와 연결되지만, capacity host는 AWS다. Google Cloud/Vertex route도 있을 수 있다. model-owner forecast에서는 Claude token을 Anthropic에 귀속하되, host dependency와 hardware mix는 AWS/Google layer에 기록한다.

Google은 Gemini model owner와 TPU/cloud host가 같은 기업 안에 있어 attribution이 비교적 단순하지만, Google Cloud에서 third-party model을 serving하는 경우는 분리해야 한다. Meta는 open-weight Llama 다운로드와 Meta AI serving을 분리해야 한다. DeepSeek, Alibaba, Tencent는 model owner와 cloud/internal app owner가 그룹 내에 있더라도 public serving과 internal integration을 구분해야 한다.

## 현실적 숫자 범위 잡기

attribution은 숫자 band가 아니라 규칙이다. 먼저 분석 목적을 정한다. model-owner token forecast라면 token을 생성하게 한 model family 소유자에게 귀속한다. cloud revenue forecast라면 hosting provider에게 귀속한다. power infrastructure forecast라면 site owner 또는 contracted power owner에게 귀속한다. memory demand forecast라면 실제 accelerator procurement와 qualification owner를 추가로 봐야 한다.

각 row에는 attribution_note를 반드시 둔다. 'OpenAI model tokens hosted on Oracle/Azure/Stargate', 'Anthropic Claude tokens hosted on AWS Trainium/Bedrock and Google Vertex', 'Microsoft Copilot tokens using OpenAI model separated from Microsoft-owned Phi/MAI' 같은 문구가 필요하다.

## 모델링 영향

attribution_rule은 aggregate total을 크게 바꾼다. 중복 계산을 제거하면 company별 token share가 달라지고, US vs China 비교도 달라진다. 또한 memory marketing에서는 실제 구매 의사결정자와 model owner가 다를 수 있으므로 account strategy에도 영향을 준다.

이 규칙은 confidence와도 연결된다. attribution이 명확한 dedicated cluster는 confidence가 높고, multi-tenant cloud serving이나 internal app routing은 confidence가 낮다. 보고서에서는 confidence를 낮춘 이유를 'capacity가 작다'가 아니라 'attribution transparency가 낮다'로 써야 한다.

## Hallucination 위험

가장 큰 위험은 host와 model owner를 동시에 더하는 것이다. 두 번째 위험은 product owner와 model owner를 혼동하는 것이다. 세 번째 위험은 open-weight model 다운로드를 해당 회사의 hosted token generation으로 착각하는 것이다. attribution rule이 없으면 forecast는 구조적으로 부풀려진다.

## 실무 체크리스트

- 이 값은 fact, estimate, proxy, scenario 중 무엇인가?
- 단위가 GW, MW, TWh/year, tokens/sec, tokens/day 중 무엇인지 명확한가?
- 회사 공식자료가 직접 말한 숫자인가, 우리가 계산한 숫자인가?
- 값이 10% 변하면 2030 Base forecast가 얼마나 움직이는가?
- low/base/high band와 confidence가 같이 기록되어 있는가?
- 새로운 공식 source가 나오면 어떤 replacement path로 교체할 것인가?

## 권장 모델 필드

- assumption_id: `A10_ATTRIBUTION_RULE`
- field_name: `attribution_rule`
- derivation_type: Fact / Estimate / Proxy / Scenario 중 하나
- confidence: High / Medium / Low
- replacement_path: 공식 source가 나오면 교체할 경로

## 참고자료

- **OPENAI_INFRA:** Building the compute infrastructure for the intelligence age, OpenAI, 2025. https://openai.com/index/building-the-compute-infrastructure-for-the-intelligence-age/
- **OPENAI_STARGATE:** Five new Stargate sites and planned capacity, OpenAI, 2025. https://openai.com/index/five-new-stargate-sites/
- **AWS_RAINIER:** AWS activates Project Rainier, Amazon, 2025. https://www.aboutamazon.com/news/aws/aws-project-rainier-ai-trainium-chips-compute-cluster
- **AWS_TRN2:** Amazon EC2 Trn2 instances, AWS, accessed 2026-05-15. https://aws.amazon.com/ec2/instance-types/trn2/
- **GOOGLE_IRONWOOD:** Ironwood: the first Google TPU for the age of inference, Google Cloud, 2025. https://blog.google/products/google-cloud/ironwood-tpu-age-of-inference/
- **OPENAI_GPT41:** GPT-4.1 model documentation, OpenAI, accessed 2026-05-15. https://platform.openai.com/docs/models/gpt-4.1

## 저작권 및 사용 메모

이 문서는 외부 자료의 전문을 복제하지 않고, 모델링과 학습에 필요한 범위에서 해석과 요약을 제공합니다. 보고서에 수치를 사용할 때는 원문 source를 다시 열어 title, publisher, date, URL, 숫자 정의를 확인해야 합니다.