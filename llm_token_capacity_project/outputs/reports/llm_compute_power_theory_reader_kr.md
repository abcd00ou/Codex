<!-- Converted from llm_compute_power_theory_reader_kr.docx -->

LLM Compute & Power Allocation Theory Reader

생성일: 2026-05-15 | 숫자 가정 현실화를 위한 이론 교재

# 목적

이 문서는 LLM token capacity simulation의 숫자를 더 현실적으로 만들기 위한 배경 이론 교재입니다. 회사별 내부 allocation을 단정하지 않고, 공개자료와 논문을 기반으로 물리적/운영적/경제적으로 말이 되는 가정을 만드는 것이 목표입니다.

# 한 문장 요약

계약 전력은 token capacity가 아니며, 실제 compute 배분은 전력 인프라, accelerator cluster, scheduler, training/inference workload, 제품 SLA, business priority가 겹쳐 결정됩니다.

# 1. 먼저 알아야 할 한계: 회사 내부 allocation 표는 거의 공개되지 않는다

LLM 업체들은 계약 전력, GPU 수, 모델별 traffic, training/inference 비중을 완전한 표로 공개하지 않습니다. 따라서 공부의 목표는 내부 원장을 복원하는 것이 아니라, 공개 신호를 통해 현실적인 범위와 제약 조건을 세우는 것입니다.

공개자료에서 확인되는 것은 대개 planned capacity, partnership, accelerator generation, model card, serving product surface, capex commentary입니다. 반면 active IT load, cluster utilization, product별 routing mix, inference/training split은 대부분 추정 영역입니다.

따라서 임원 보고용 숫자는 항상 세 층으로 나눠야 합니다: 공식 fact, fact에서 파생한 estimate, 미래 시나리오입니다.

# 2. 계약 전력에서 서비스 전력까지의 계층

계약 전력 또는 announced GW는 서비스가 즉시 쓸 수 있는 토큰 capacity가 아닙니다. 보통 interconnection, PPA, colocation lease, site plan, power reservation, long-term cloud agreement가 섞여 있습니다.

서비스 전력으로 내려오려면 전력 인입, 변전 설비, UPS, 냉각, 네트워크, rack integration, GPU/ASIC delivery, cluster burn-in, orchestration layer가 모두 준비되어야 합니다.

그 다음에야 facility power가 IT load로 바뀌고, IT load 중 AI cluster 몫이 정해지며, 그 안에서 training, inference, evaluation, data processing, redundancy reserve로 나뉩니다.

# 3. 기업은 전력을 어떻게 서비스에 배분하는가

현실의 배분은 회계표처럼 고정 비율로 나뉘지 않습니다. capacity planning, quota, priority, SLA, preemption, regional placement, model routing이 함께 작동합니다.

training은 큰 contiguous GPU slice를 오래 잡아먹고, inference는 latency SLO를 맞추기 위해 지역별로 여유 capacity와 autoscaling buffer를 둡니다. 그래서 평균 전력과 peak 예약 capacity가 다를 수 있습니다.

서비스별 배분은 보통 제품 P&L, 전략 우선순위, customer SLA, model freshness, GPU generation suitability, data residency requirement에 따라 정해집니다.

# 4. Training compute의 경제학

Training은 frontier capability를 올리기 위한 장기 투자입니다. 큰 모델일수록 파라미터, 데이터 토큰, optimizer state, activation memory, network bandwidth가 동시에 커집니다.

Kaplan scaling law는 parameter, data, compute를 함께 늘릴수록 loss가 power-law로 개선된다는 직관을 줬고, Chinchilla는 고정 compute에서 model size와 training tokens를 더 균형 있게 키워야 한다는 방향을 제시했습니다.

Training cluster는 짧게 빌렸다 끄기 어렵습니다. 한 번 시작한 run은 checkpoint, failure recovery, experiment pipeline과 묶이므로 높은 priority와 안정적인 power/thermal envelope이 필요합니다.

# 5. Inference compute의 경제학

Inference는 매출과 고객 경험에 직접 연결됩니다. API, chatbot, enterprise assistant, coding agent, search, recommendation, ads workload는 latency와 availability가 중요합니다.

LLM inference는 크게 prefill과 decode로 나뉩니다. prefill은 prompt를 한 번에 처리하는 compute-intensive 단계이고, decode는 한 token씩 생성하면서 KV cache와 memory bandwidth의 영향을 크게 받는 단계입니다.

서비스가 커질수록 inference는 더 큰 share를 요구하지만, 100%를 차지하지는 않습니다. frontier training, fine-tuning, eval, synthetic data generation, safety testing, distillation도 계속 compute를 씁니다.

# 6. 초기 LLM 기업의 training/inference 비중을 어떻게 생각해야 하나

제품 출시 전 또는 초기 연구 중심 단계에서는 training과 experiment가 compute 사용의 중심입니다. 이때 inference는 demo, eval, limited API 정도로 제한됩니다.

ChatGPT/Claude/Gemini 같은 대규모 상용 서비스가 열린 뒤에는 inference가 marginal capacity의 핵심 수요가 됩니다. 특히 무료/저가 사용자 traffic은 비용 압박을 만들고, paid/API traffic은 latency와 availability 투자를 요구합니다.

다만 frontier lab은 차세대 모델 학습을 멈추지 않습니다. 그래서 '초기에는 training-heavy, 상용화 이후 inference-heavy로 이동'이라는 방향은 맞지만, 특정 연도에 몇 %라고 확정하려면 공개 evidence가 부족합니다.

# 7. 왜 prefill/decode가 전력 배분 가정에 중요해지는가

같은 inference라도 prompt가 긴 RAG/agent workload와 짧은 chatbot workload는 자원 사용 패턴이 다릅니다. 긴 prompt는 prefill 비용과 KV cache 부담을 키웁니다.

Splitwise와 DistServe 계열 연구는 prefill과 decode를 분리해 서로 다른 GPU 또는 cluster slice로 배치하면 throughput, cost, power 측면에서 개선 여지가 있음을 보여줍니다.

따라서 tokens/sec/MW는 단일 상수가 아니라 workload mix, prompt length, output length, batching, SLO, memory management에 따라 달라지는 운영 지표입니다.

# 8. 공개자료로 training/inference share를 추론하는 법

직접 공개가 없을 때는 accelerator type, product traffic, cloud quota 문구, inference-specific chip 발표, 모델 출시 cadence, capex timing을 조합합니다.

예를 들어 Google이 inference-oriented TPU를 발표하거나 TPU serving quota를 분리한다는 문서는 inference가 별도 capacity planning 대상임을 보여주지만, Gemini 전체 GW 중 inference share를 직접 알려주지는 않습니다.

Anthropic-AWS, OpenAI-Stargate 같은 deal은 capacity 확보 방향을 보여주지만, 그 capacity가 training과 inference에 몇 대 몇으로 배분되는지는 별도 가정입니다.

# 9. 뉴스 읽는 법: 숫자보다 동사에 주목한다

AI 인프라 뉴스에서 가장 중요한 단어는 planned, committed, secured, leased, operational, energized, deployed, serving입니다. planned와 operational은 완전히 다른 단계입니다.

또 training, run, serve, inference, power, host, capacity, chips, data center site가 한 문장 안에서 어떻게 연결되는지 봐야 합니다.

전문을 그대로 복사해 보관하기보다, 숫자와 동사를 source_review_log에 요약하고 링크를 남기는 방식이 더 안전하고 추적 가능합니다.

# 10. 현실적인 가정 밴드를 만드는 순서

첫째, 물리적 경계부터 잡습니다. active power는 contracted power보다 클 수 없고, inference와 training share의 합은 100%여야 합니다.

둘째, 공개 source가 직접 말하는 숫자와 우리가 계산한 숫자를 분리합니다. planned GW, GPU count, model parameter는 fact일 수 있지만 active inference GW는 대개 estimate입니다.

셋째, 논문은 방향성을 주고 회사 숫자를 직접 주지는 않는다는 점을 기억합니다. PagedAttention, Splitwise, DistServe는 tokens/MW 개선의 mechanism이지 특정 회사의 production efficiency가 아닙니다.

# Long-form Research Report

아래 장은 요약형 학습 노트가 아니라 조사기관 리포트처럼 긴 본문으로 작성한 해설입니다. 각 장은 공개자료가 직접 말하는 것과, 우리가 시뮬레이션에서 추정해야 하는 것을 구분하는 데 초점을 둡니다.

## A. 전력 계약은 왜 곧바로 AI 서비스 capacity가 아닌가

AI 데이터센터 보도에서 가장 흔히 발생하는 해석 오류는 계약 전력 또는 발표 capacity를 곧바로 토큰 생성 capacity로 바꾸는 것이다. 그러나 전력 계약은 물리적 운영 능력의 상한에 가깝고, 실제 서비스 capacity는 그보다 훨씬 많은 중간 단계를 거친다. 전력회사와의 interconnection, 장기 전력구매계약, 토지와 건물 확보, 변전설비, UPS, 냉각, 랙 설치, 네트워크 연결, accelerator 수급, cluster validation, orchestration software까지 모두 준비되어야 비로소 active compute가 된다. 따라서 '7GW planned capacity'라는 숫자가 있다면, 첫 번째 질문은 이것이 몇 년도에 어느 정도 energize되는지이고, 두 번째 질문은 그중 얼마가 실제 AI IT load인지이며, 세 번째 질문은 그 AI IT load 중 얼마가 inference serving에 쓰이는지이다.

조사기관 리포트들이 전력 수요를 추정할 때도 이 차이를 중요하게 본다. IEA의 Energy and AI는 데이터센터 전력 수요가 2030년까지 크게 증가할 수 있다고 보지만, 그 수요는 국가별 전력망, 전원 구성, 송전망, 건설 속도, 효율 개선에 따라 달라진다. LBNL의 미국 데이터센터 에너지 사용 보고서도 데이터센터 전력 사용을 서버, storage, network, cooling, power conversion 등 여러 층으로 나눠 본다. 이런 문헌은 특정 LLM 기업의 내부 배분표를 제공하지는 않지만, 'facility level electricity'와 'useful AI compute' 사이에 구조적 손실과 배분 단계가 있다는 점을 확인시켜 준다.

계약 전력의 현실화 속도는 지역마다 다르다. 같은 1GW 발표라도 이미 송전망과 변전 인프라가 가까운 캠퍼스형 데이터센터인지, 신규 부지와 발전원을 묶어야 하는 프로젝트인지에 따라 active capacity 전환 속도가 다르다. 또한 AI rack은 일반 클라우드 서버보다 rack density와 냉각 요구가 높기 때문에, 전력이 들어와도 바로 GPU cluster가 가동된다고 보기 어렵다. 특히 GB200/NVL72 같은 rack-scale system은 전력, 냉각, 네트워크, rack integration이 동시에 맞아야 한다. 이 때문에 시뮬레이션에서는 contracted_power_gw와 active_power_gw를 분리해야 한다.

이 구분은 임원 보고에서 매우 중요하다. 발표 capacity를 모두 active inference capacity로 계산하면 토큰 생성량이 과대평가되고, 메모리 수요도 과대 추정될 수 있다. 반대로 실제로 빠르게 energize되는 프로젝트를 너무 보수적으로 보면 HBM, DDR5, SSD, CXL 수요 전환 타이밍을 놓칠 수 있다. 따라서 현실적인 가정은 단일 숫자가 아니라 deployment curve로 표현해야 한다. 예를 들어 2026년에는 발표 capacity의 20-40%만 active로, 2030년에는 50-80%가 active로 전환되는 식의 밴드가 더 정직하다. 이 밴드는 공식 발표, 지역 전력망 상황, construction milestone, GPU delivery, 고객 서비스 출시 일정으로 계속 교체되어야 한다.

핵심 takeaways

- 계약/계획 GW는 상한선이고 active GW는 운영 가능 capacity다.

- active GW에서도 PUE, AI workload share, training/inference split을 적용해야 한다.

- 발표 숫자를 읽을 때 planned, committed, operational, energized, deployed라는 동사를 구분한다.

## B. LLM 기업은 compute를 어떤 방식으로 배분하는가

LLM 기업의 compute allocation은 전력 배분표 하나로 설명되지 않는다. 실제 운영에서는 capacity planning, GPU cluster topology, scheduler, quota, product priority, latency SLO, model routing, failure reserve가 함께 작동한다. 연구 조직은 장기 training run과 실험 queue를 요구하고, 제품 조직은 API와 챗봇 서비스의 latency와 availability를 요구하며, enterprise 고객은 SLA와 데이터 거주성 요건을 요구한다. 따라서 전력은 단순히 'training 40%, inference 60%' 같은 고정 표로 배분되기보다, cluster 단위와 workload priority 단위로 동적으로 배분된다.

Training workload는 일반적으로 대규모 contiguous accelerator slice를 요구한다. 수천에서 수만 개 GPU가 하나의 실험 또는 training run에 묶이면, 네트워크 topology와 checkpoint, failure recovery, optimizer state가 모두 중요해진다. 이 workload는 시작하면 중간에 쉽게 쪼개거나 다른 서비스로 넘기기 어렵다. 반면 inference workload는 지역별로 배치되고, traffic pattern에 따라 autoscaling되며, latency SLO를 맞추기 위해 여유 capacity를 둔다. 따라서 동일한 평균 전력이라도 training은 large block reservation 성격이 강하고, inference는 distributed serving fleet 성격이 강하다.

초기 LLM 기업은 대개 training-heavy로 시작한다. 아직 대규모 유료 traffic이 없고, 모델 성능 향상이 회사 가치의 핵심이기 때문이다. 하지만 ChatGPT, Claude, Gemini, Copilot, Meta AI, Qwen, DeepSeek API처럼 상용 서비스가 커지면 상황이 바뀐다. 매일 들어오는 요청을 처리하지 못하면 매출과 고객 경험이 직접 훼손된다. 이 단계에서 marginal compute의 상당 부분은 inference로 이동한다. 다만 frontier model 경쟁이 계속되는 한 training이 사라지지는 않는다. 차세대 foundation model, post-training, reinforcement learning, eval, synthetic data generation이 계속 compute를 요구한다.

기업별 차이도 크다. Google은 TPU라는 자체 accelerator와 검색/클라우드/Workspace/Gemini라는 제품 surface를 함께 갖고 있어 inference serving을 내부 hardware roadmap과 묶을 수 있다. OpenAI는 ChatGPT와 API traffic이 크지만 Microsoft, Oracle, Stargate 등 hosting 및 capacity partner와 얽혀 있어 attribution이 복잡하다. Anthropic은 Claude, Bedrock, Vertex AI 등 여러 route로 serving되므로 AWS/Google host capacity와 Anthropic model owner capacity를 분리해야 한다. Meta는 open-weight Llama와 Meta AI product serving, internal ranking/recommendation AI가 함께 존재한다. 중국 업체들은 Qwen, Hunyuan, DeepSeek 같은 모델과 cloud/internal app traffic의 경계가 공개자료에서 덜 명확하다.

시뮬레이션 관점에서 compute allocation은 세 단계로 모델링하는 것이 좋다. 첫째, 기업 또는 model owner의 active AI IT load를 추정한다. 둘째, 그 load를 training, inference, eval/post-training, reserve로 나누되 보고용 모델에서는 training/inference 두 축으로 단순화한다. 셋째, inference load를 다시 model family와 commercial surface로 귀속한다. 이 과정을 거치면 '전력 capacity가 많은 회사'와 '상용 토큰을 많이 생성하는 회사'를 구분할 수 있다.

핵심 takeaways

- Training은 대규모 contiguous cluster slice, inference는 latency SLO 기반 distributed serving fleet에 가깝다.

- 상용화 이후 marginal compute는 inference 쪽으로 이동하지만 frontier training은 계속 남는다.

- host provider와 model owner를 분리하지 않으면 중복 계산 위험이 커진다.

## C. Training compute 비중을 이해하는 이론

Training compute를 이해하려면 scaling law부터 봐야 한다. Kaplan et al.의 scaling law는 모델 성능이 model size, dataset size, compute와 함께 예측 가능한 방식으로 개선된다는 프레임을 제공했다. 이후 Hoffmann et al.의 Chinchilla 논문은 고정 compute 예산에서 지나치게 큰 모델보다 더 많은 데이터 토큰으로 학습한 compute-optimal 모델이 유리할 수 있음을 보였다. 이 두 흐름은 LLM 기업이 왜 계속 training compute를 늘리는지, 그리고 왜 parameter count만으로 training 투자를 판단하면 안 되는지 설명한다.

Training compute의 경제학은 inference와 다르다. Training은 미래 성능과 시장 지위를 위한 투자이며, 단기 매출에 직접 대응되는 비용이라기보다 R&D와 전략 CAPEX의 성격이 강하다. frontier model race에서는 모델이 출시되기 전에도 대규모 compute가 투입된다. 또 pretraining 이후에도 instruction tuning, RLHF/RLAIF, safety tuning, multimodal alignment, code/math specialization, synthetic data generation, eval infrastructure가 필요하다. 따라서 'training'이라는 항목 안에도 여러 workload가 있다.

Epoch AI와 EPRI/Epoch 계열 분석은 frontier training run의 power demand가 2030년까지 매우 커질 수 있음을 제시한다. 다만 이런 숫자는 특정 기업의 연중 평균 전력 배분이 아니라 '최대 frontier training run이 요구할 수 있는 power envelope'에 가깝다. 즉, 2030년에 어떤 training run이 수 GW급 전력을 요구할 수 있다는 전망이 있다 해도, 그것을 특정 회사의 전체 연중 training share로 바로 바꾸면 안 된다. 이 숫자는 training cluster가 여전히 중요한 capacity sink라는 점을 보여주는 evidence로 써야 한다.

Training workload는 scheduling 관점에서 더 경직적이다. 모델 병렬화와 data parallelism, pipeline parallelism, tensor parallelism은 cluster topology에 민감하다. GPU 간 통신 지연, interconnect bandwidth, failure rate, checkpoint cost가 training efficiency를 좌우한다. 그래서 기업은 training용 cluster를 inference용 cluster와 물리적으로 또는 운영적으로 분리할 유인이 있다. 일부 hardware는 양쪽 모두 가능하지만, cluster design과 software stack은 workload에 따라 최적점이 다르다.

시뮬레이션에서는 training_power_share를 단순 잔여값으로 취급하면 안 된다. 특히 초기 frontier lab이나 새로운 model generation을 준비하는 기업은 inference traffic이 증가해도 training reserve를 크게 유지할 수 있다. 반대로 mature commercial model owner는 상용 traffic이 커질수록 inference share가 올라갈 수 있다. 현실적인 가정은 기업의 제품 성숙도, 모델 출시 cadence, frontier training ambition, cloud partner capacity를 함께 반영해야 한다.

핵심 takeaways

- Scaling law는 training compute가 왜 계속 커지는지 설명한다.

- frontier training power 전망은 연중 평균 share가 아니라 peak training envelope로 해석해야 한다.

- training share는 제품 성숙도와 모델 출시 cadence에 따라 업체별로 달라진다.

## D. Inference compute 비중을 이해하는 이론

Inference compute는 상용 LLM 기업의 매출, 고객 경험, 비용 구조를 직접 결정한다. Chatbot, API, enterprise assistant, coding agent, search answer, multimodal generation, RAG, workflow automation은 모두 inference traffic을 만든다. 사용자가 늘고 제품 surface가 넓어질수록 inference capacity는 단순히 모델을 한 번 배포하는 비용이 아니라 상시 운영 비용이 된다. 그래서 상용화 이후 LLM 기업의 capacity planning은 training만큼이나 inference serving economics에 의해 움직인다.

LLM inference는 prefill과 decode라는 두 단계로 나뉜다. Prefill은 사용자의 prompt token을 병렬로 처리해 attention state와 KV cache를 만드는 단계다. 긴 context, RAG 문서, agent memory, tool-use trace가 붙으면 prefill 비용이 커진다. Decode는 output token을 한 token씩 생성하는 단계로, autoregressive 특성 때문에 latency와 memory bandwidth, KV cache access가 중요하다. 사용자가 보는 체감 latency는 첫 token까지의 시간(TTFT)과 token 간 지연(TPOT)에 의해 결정된다.

PagedAttention/vLLM, Splitwise, DistServe 같은 연구는 inference serving이 단순 matrix multiplication 문제가 아니라 memory management와 scheduling 문제임을 보여준다. PagedAttention은 KV cache를 효율적으로 관리해 serving throughput을 높이는 방향을 제시했고, Splitwise와 DistServe는 prefill과 decode를 분리하거나 disaggregate하면 latency SLO와 throughput을 더 잘 맞출 수 있음을 보였다. 이런 연구는 tokens/sec/MW가 hardware 하나로 결정되는 값이 아니라 serving stack 전체의 함수라는 점을 강조한다.

Inference capacity는 평균 사용률을 100%로 잡을 수 없다. 사용자는 하루 중 특정 시간에 몰리고, enterprise 고객은 region과 data residency를 요구하며, latency SLO를 맞추려면 peak와 failover를 위한 reserve가 필요하다. 또한 모델 routing이 있다. 모든 요청이 가장 큰 frontier model로 가지 않고, latency와 비용을 줄이기 위해 smaller model, distilled model, MoE expert path, tool-specific model로 분산될 수 있다. 따라서 inference_power_share와 utilization은 서로 다른 개념이다. inference share는 AI IT load 중 inference에 배정된 전력이고, utilization은 그 inference capacity가 실제 token generation으로 전환되는 평균 효율이다.

초기 LLM 기업의 inference 비중을 추론할 때는 제품 surface를 봐야 한다. ChatGPT 같은 대규모 consumer surface, Copilot처럼 enterprise productivity surface, Gemini가 검색/Android/Workspace에 결합되는 surface, Claude가 API/Bedrock/enterprise에 배포되는 surface는 모두 inference demand를 증가시킨다. 반면 연구 중심이거나 아직 대규모 paid traffic이 제한적인 모델은 training/experiment share가 더 높을 수 있다. 이 때문에 2026년에 전체 GW의 60% 이상이 inference라고 단정하려면 강한 evidence가 필요하며, 공개자료만으로는 보통 scenario로 취급해야 한다.

핵심 takeaways

- Inference는 prefill, decode, KV cache, latency SLO, batching이 결합된 운영 문제다.

- inference share와 utilization은 다르다.

- 대규모 상용 product surface가 커질수록 inference share 상승 압력이 생긴다.

## E. 논문과 리포트를 숫자 가정으로 바꾸는 법

논문은 회사별 production number를 직접 주지 않는 경우가 대부분이다. Kaplan과 Chinchilla는 training compute 배분의 이론적 방향을 주고, PagedAttention, Splitwise, DistServe는 inference serving efficiency가 어떤 mechanism으로 개선될 수 있는지 보여준다. 하지만 이 논문들의 benchmark 결과를 그대로 OpenAI, Google, Anthropic, Meta의 tokens/sec/MW로 넣으면 안 된다. 논문은 mechanism과 sensitivity를 제공하고, 회사별 값은 공식 infrastructure signal과 별도 추정이 필요하다.

조사기관 리포트도 마찬가지다. IEA, LBNL, CRS, EPRI/Epoch 같은 자료는 macro power demand, grid impact, frontier training envelope, 데이터센터 에너지 사용의 구조를 제공한다. 그러나 특정 LLM 기업이 2028년에 active_power_gw의 몇 %를 inference에 배정하는지는 알려주지 않는다. 따라서 리포트는 '상한/하한', '증가 방향', '전력망 병목', 'training run power envelope', '데이터센터 에너지 baseline'을 만드는 데 쓰고, 업체별 allocation은 model-owner evidence와 결합해야 한다.

숫자로 바꾸는 절차는 네 단계가 좋다. 첫째, source가 직접 말하는 숫자를 fact anchor로 기록한다. 둘째, 그 숫자가 어떤 단위인지 확인한다. TWh/year인지, GW power인지, GPU count인지, FLOPs인지, tokens/sec인지 구분한다. 셋째, 우리 모델의 어느 변수에 영향을 주는지 mapping한다. 예를 들어 IEA 데이터센터 전력 전망은 company active_power_gw를 직접 바꾸지 않고, macro plausibility와 grid constraint scenario에 영향을 준다. DeepSeek active parameter는 MoE model efficiency sanity check에 직접 영향을 준다. 넷째, confidence와 replacement path를 기록한다.

가장 위험한 변환은 서로 다른 단위의 숫자를 연결할 때 발생한다. 예를 들어 annual electricity consumption TWh를 instantaneous GW로 바꾸려면 시간 평균을 고려해야 하고, facility power를 IT load로 바꾸려면 PUE가 필요하며, IT load를 accelerator board power로 바꾸려면 server/network/storage/cooling overhead를 분리해야 한다. 토큰량으로 바꿀 때는 tokens/sec/MW와 utilization이 필요하다. 이런 곱셈 구조 때문에 작은 단위 오류가 forecast를 크게 흔든다.

핵심 takeaways

- 논문은 mechanism, 리포트는 macro boundary, 공식 발표는 fact anchor로 쓴다.

- TWh/year, GW, MW, GPU count, FLOPs, tokens/sec를 섞지 않는다.

- 모든 source는 어떤 변수에 영향을 주는지 mapping해야 한다.

## F. 뉴스와 기업 발표를 읽는 실무 방법

AI infrastructure 뉴스는 숫자보다 동사를 먼저 읽어야 한다. planned, announced, committed, secured, leased, financed, under construction, energized, operational, deployed, serving은 서로 다른 단계다. planned 또는 announced는 전략적 의도와 상한을 의미할 수 있지만, operational 또는 serving은 실제 active capacity에 가까운 신호다. 'GPU를 확보했다'는 말도 cluster가 production serving에 들어갔다는 뜻은 아니다. procurement, delivery, installation, qualification, deployment는 모두 다른 단계다.

또한 누가 주어인지 봐야 한다. Oracle이 데이터센터를 짓고 OpenAI가 쓴다면 capacity owner와 model owner가 다르다. AWS가 Anthropic에 Trainium과 Bedrock capacity를 제공한다면 host infrastructure와 Claude token owner를 분리해야 한다. Microsoft는 자체 Copilot token과 Azure-hosted OpenAI token, third-party model hosting이 섞일 수 있다. 뉴스 한 문장 안에서 'for OpenAI', 'with Microsoft', 'hosted on AWS', 'available through Bedrock' 같은 전치사와 channel 표현을 정확히 읽어야 한다.

전문을 저장할 때도 주의해야 한다. 저작권 있는 기사 전문을 내부 문서에 그대로 붙여넣기보다는, headline, publisher, date, URL, 핵심 숫자, 핵심 동사, 우리 모델에 미치는 변수, confidence를 기록하는 방식이 좋다. 예를 들어 '회사 A가 1GW 데이터센터를 announced'라는 뉴스라면 source_review_log에는 1GW, announced, 지역, expected online date, 관련 업체, 우리 모델 변수(active_power_2030_gw 또는 contracted_power_2030_gw)를 기록한다. 본문 해석은 우리가 작성하고 원문 링크를 남긴다.

뉴스의 숫자가 다른 출처와 충돌하면 최신성을 기준으로 바로 덮어쓰지 말고 정의를 비교해야 한다. 한 리포트는 data center electricity demand를 TWh/year로 말하고, 다른 리포트는 AI power capacity를 GW로 말하며, 또 다른 뉴스는 특정 training run의 peak power를 말할 수 있다. 이 세 숫자는 모두 'AI 전력'처럼 보이지만 같은 변수가 아니다. 충돌처럼 보이는 숫자 대부분은 scope, unit, geography, time basis가 다르기 때문에 생긴다.

핵심 takeaways

- 뉴스는 숫자보다 동사를 먼저 읽는다.

- capacity owner, host provider, model owner, product owner를 분리한다.

- 전문 복사보다 source log 방식이 안전하고 재사용성이 높다.

## G. 현재 시뮬레이션에 바로 적용되는 학습 결론

첫 번째 결론은 active_power_gw가 가장 중요한 재검토 변수라는 점이다. contracted_power_gw는 비교적 뉴스와 발표로 잡을 수 있지만, active_power_gw는 construction, energization, GPU delivery, cluster readiness가 모두 반영되어야 한다. 따라서 이 변수는 confidence를 높게 두기 어렵고, 항상 replacement path를 가져야 한다. site-level operational disclosure가 나오면 즉시 교체해야 한다.

두 번째 결론은 inference_power_share를 fact로 말하면 안 된다는 점이다. 공개자료는 inference-oriented hardware와 product traffic 증가를 보여주지만, 기업별 전체 AI GW 중 inference가 몇 %인지 직접 말하지 않는다. 그러므로 2026년 60% 이상 inference share는 특정 기업 또는 bull scenario에서는 가능하더라도 전체 base case fact로 쓰면 안 된다. 2030년으로 갈수록 commercial inference share가 상승한다는 방향성은 합리적이지만, 숫자는 scenario로 남겨야 한다.

세 번째 결론은 tokens/sec/MW가 단일 benchmark 숫자가 아니라는 점이다. 같은 MW라도 모델 architecture, active parameter, context length, traffic mix, batching 가능성, latency SLO, KV cache 효율, accelerator generation, interconnect, software stack에 따라 달라진다. 따라서 benchmark layer는 sanity check로 쓰고, forecast의 직접 근거로 쓰려면 해당 회사 production 환경과 연결되는 별도 evidence가 필요하다.

네 번째 결론은 attribution이 숫자 정합성의 핵심이라는 점이다. OpenAI와 Microsoft, Anthropic과 AWS/Google, OpenAI와 Oracle/Stargate처럼 model owner와 infrastructure host가 분리된 경우 capacity를 중복 계산하기 쉽다. 모델 owner 기준 token generation forecast를 만들려면 host capacity를 누구의 토큰으로 귀속할지 명시해야 한다. 반대로 hyperscaler capex 모델을 만들 때는 같은 capacity를 infrastructure owner 기준으로 볼 수 있다. 두 관점을 섞으면 숫자가 부풀려진다.

핵심 takeaways

- 가장 먼저 공부하고 교체할 변수는 active_power_gw다.

- inference share는 공개자료상 대부분 scenario이며 fact가 아니다.

- tokens/sec/MW와 attribution rule은 hallucination audit의 핵심이다.

# 핵심 개념 사전

| 개념 | 의미 |
| --- | --- |
| Contracted / planned power | 계약, 계획, 확보, 또는 발표된 전력. active service capacity가 아님. |
| Active power | 실제로 전력 인입과 설비 준비가 끝나 운영 가능한 facility power. |
| IT load | PUE를 제거한 서버, storage, network, accelerator 측 전력. |
| AI IT load | IT load 중 AI training/inference cluster가 차지하는 부분. |
| Training | 모델 weight를 업데이트하는 과정. 장시간 큰 cluster slice가 필요. |
| Inference | 학습된 모델을 서비스에 배치해 prompt를 처리하고 token을 생성하는 과정. |
| Prefill | prompt token을 처리해 KV cache를 만드는 inference 초기 단계. |
| Decode | output token을 autoregressive하게 한 token씩 생성하는 단계. |
| KV cache | 이전 token의 key/value state를 저장해 decode 효율을 높이는 memory state. |
| SLO | latency/availability 목표. capacity reserve와 overprovisioning의 근거. |

# 공부 질문

- 이 회사의 발표는 planned capacity인가, operational capacity인가?

- 해당 전력은 facility power인가, IT load인가, accelerator board power인가?

- 이 capacity는 training용 cluster인가, inference serving용 cluster인가, 둘 다 가능한가?

- 서비스 traffic이 latency-sensitive인가, batchable한가?

- inference workload는 prefill-heavy인가, decode-heavy인가?

- 모델은 dense인가 MoE인가? total parameter와 active parameter가 분리되어 있는가?

- benchmark 논문을 회사 production number로 오해하고 있지는 않은가?

# 읽기 자료 요약

## S01. IEA, Energy and AI

발행자: IEA | 날짜: 2025

링크: https://www.iea.org/reports/energy-and-ai

읽는 목적: 데이터센터 전력 수요와 AI 전력 전망의 macro baseline

기록 방식: 원문 숫자 1-3개, 핵심 동사, 우리 모델에서 바뀔 수 있는 assumption_id를 source_review_log.md에 남깁니다.

## S02. 2024 United States Data Center Energy Usage Report

발행자: Lawrence Berkeley National Laboratory / DOE | 날짜: 2024-12

링크: https://buildings.lbl.gov/publications/2024-lbnl-data-center-energy-usage-report

읽는 목적: 미국 데이터센터 에너지 사용, AI server 추정, water/power baseline

기록 방식: 원문 숫자 1-3개, 핵심 동사, 우리 모델에서 바뀔 수 있는 assumption_id를 source_review_log.md에 남깁니다.

## S03. Data Centers and Their Energy Consumption: Frequently Asked Questions

발행자: Congressional Research Service | 날짜: 2026

링크: https://www.congress.gov/crs-product/R48646

읽는 목적: 미국 정책/전력망 관점의 데이터센터 FAQ

기록 방식: 원문 숫자 1-3개, 핵심 동사, 우리 모델에서 바뀔 수 있는 assumption_id를 source_review_log.md에 남깁니다.

## S04. Electricity Demand and Grid Impacts of AI Data Centers

발행자: arXiv | 날짜: 2025

링크: https://arxiv.org/abs/2509.07218

읽는 목적: AI 데이터센터 부하 특성과 전력망 영향 review

기록 방식: 원문 숫자 1-3개, 핵심 동사, 우리 모델에서 바뀔 수 있는 assumption_id를 source_review_log.md에 남깁니다.

## S05. Scaling Laws for Neural Language Models

발행자: Kaplan et al., arXiv | 날짜: 2020

링크: https://arxiv.org/abs/2001.08361

읽는 목적: 훈련 compute, parameter, data 간 scaling law

기록 방식: 원문 숫자 1-3개, 핵심 동사, 우리 모델에서 바뀔 수 있는 assumption_id를 source_review_log.md에 남깁니다.

## S06. Training Compute-Optimal Large Language Models

발행자: Hoffmann et al., arXiv | 날짜: 2022

링크: https://arxiv.org/abs/2203.15556

읽는 목적: Chinchilla compute-optimal scaling, parameter/token allocation

기록 방식: 원문 숫자 1-3개, 핵심 동사, 우리 모델에서 바뀔 수 있는 assumption_id를 source_review_log.md에 남깁니다.

## S07. Training compute of frontier AI models grows by 4-5x per year

발행자: Epoch AI | 날짜: 2024

링크: https://epoch.ai/blog/training-compute-of-frontier-ai-models-grows-by-4-5x-per-year

읽는 목적: frontier training compute trend

기록 방식: 원문 숫자 1-3개, 핵심 동사, 우리 모델에서 바뀔 수 있는 assumption_id를 source_review_log.md에 남깁니다.

## S08. How much power will frontier AI training demand in 2030?

발행자: Epoch AI | 날짜: 2025

링크: https://epoch.ai/blog/power-demands-of-frontier-ai-training/

읽는 목적: single frontier training run의 전력 수요 추정

기록 방식: 원문 숫자 1-3개, 핵심 동사, 우리 모델에서 바뀔 수 있는 assumption_id를 source_review_log.md에 남깁니다.

## S09. Efficient Memory Management for LLM Serving with PagedAttention

발행자: Kwon et al., arXiv | 날짜: 2023

링크: https://arxiv.org/abs/2309.06180

읽는 목적: KV cache, batching, serving throughput bottleneck

기록 방식: 원문 숫자 1-3개, 핵심 동사, 우리 모델에서 바뀔 수 있는 assumption_id를 source_review_log.md에 남깁니다.

## S10. Splitwise: Efficient generative LLM inference using phase splitting

발행자: Patel et al., arXiv | 날짜: 2023

링크: https://arxiv.org/abs/2311.18677

읽는 목적: prefill/decode 분리와 power/cost 최적화

기록 방식: 원문 숫자 1-3개, 핵심 동사, 우리 모델에서 바뀔 수 있는 assumption_id를 source_review_log.md에 남깁니다.

## S11. DistServe: Disaggregating Prefill and Decoding

발행자: Zhong et al., arXiv | 날짜: 2024

링크: https://arxiv.org/abs/2401.09670

읽는 목적: TTFT/TPOT SLO와 prefill/decode resource allocation

기록 방식: 원문 숫자 1-3개, 핵심 동사, 우리 모델에서 바뀔 수 있는 assumption_id를 source_review_log.md에 남깁니다.

## S12. Google Ironwood TPU: age of inference

발행자: Google Cloud | 날짜: 2025-04-09

링크: https://blog.google/products/google-cloud/ironwood-tpu-age-of-inference/

읽는 목적: inference-oriented accelerator와 TPU serving 방향

기록 방식: 원문 숫자 1-3개, 핵심 동사, 우리 모델에서 바뀔 수 있는 assumption_id를 source_review_log.md에 남깁니다.

## S13. Cloud TPU inference documentation

발행자: Google Cloud | 날짜: accessed 2026-05-14

링크: https://docs.cloud.google.com/tpu/docs/v5e-inference

읽는 목적: serving quota와 inference deployment 개념

기록 방식: 원문 숫자 1-3개, 핵심 동사, 우리 모델에서 바뀔 수 있는 assumption_id를 source_review_log.md에 남깁니다.

## S14. AWS Trainium

발행자: AWS | 날짜: accessed 2026-05-14

링크: https://aws.amazon.com/ai/machine-learning/trainium/

읽는 목적: training/inference용 custom accelerator positioning

기록 방식: 원문 숫자 1-3개, 핵심 동사, 우리 모델에서 바뀔 수 있는 assumption_id를 source_review_log.md에 남깁니다.

## S15. Amazon and Anthropic expand strategic collaboration

발행자: Amazon | 날짜: 2024

링크: https://www.aboutamazon.com/news/company-news/amazon-invests-additional-5-billion-anthropic-ai/

읽는 목적: Claude, Trainium, Bedrock inference attribution 사례

기록 방식: 원문 숫자 1-3개, 핵심 동사, 우리 모델에서 바뀔 수 있는 assumption_id를 source_review_log.md에 남깁니다.

## S16. OpenAI compute infrastructure / Stargate

발행자: OpenAI | 날짜: 2025-2026

링크: https://openai.com/index/building-the-compute-infrastructure-for-the-intelligence-age/

읽는 목적: planned capacity와 model-owner compute 전략 사례

기록 방식: 원문 숫자 1-3개, 핵심 동사, 우리 모델에서 바뀔 수 있는 assumption_id를 source_review_log.md에 남깁니다.

# 저작권 메모

뉴스와 유료 리포트 전문은 이 문서에 복사하지 않습니다. 대신 핵심 숫자, 출처, 날짜, 해석, 적용 가능한 assumption만 요약합니다. 논문과 공식 보고서도 필요한 범위에서 요약하고 원문 링크를 남깁니다.
