# 박종세 교수 인터뷰 미팅 정리

작성일: 2026-07-21

원문:
- `/Users/idongseong/Downloads/TurboScribe Export 1044896196/계룡로141번길.docx`
- `/Users/idongseong/Downloads/TurboScribe Export 1044896196/대학로291번나길.docx`

전사본은 화자 구분이 없고 일부 용어가 오인식되어 있어, 아래 정리는 문맥상 `GPU`, `TPU`, `vLLM`, `MoE`, `TPS`, `KV cache`, `FLOPS` 등으로 보정해 작성했다.

## 1. 한 줄 결론

이번 미팅의 핵심은 “LLM 토큰 수요를 인프라 수요로 역산하는 접근은 방향성은 맞지만, 닫힌 모델의 파라미터/운영 구성이 불투명하기 때문에 순수 이론식만으로 정확히 예측하기는 어렵고, 실제 benchmark/profiling 데이터를 보정계수로 써야 한다”는 것이다.

사업적으로는 hyperscaler가 아닌 대형 IT 기업이 향후 Claude/OpenAI API 비용 부담을 크게 느끼게 될 가능성이 있고, 이들에게 오픈소스 모델 + GPU/네오클라우드 + 서빙 최적화 소프트웨어 조합을 제공하는 시장은 존재할 수 있다는 의견이었다.

## 2. 사업 가설 관련 정리

### 2.1 Agentic AI 시장은 코딩에만 머물지 않을 가능성

- 현재 코딩 에이전트는 토큰 사용량이 매우 크고, 코드라는 도메인은 목적 함수가 비교적 명확해 AI 적용이 빠르게 진행되고 있다.
- 다만 코딩만이 전부는 아니며, 교육, 의료, 기타 산업 업무처럼 “기계적으로 처리 가능한” 영역도 훨씬 더 클 수 있다.
- 수천 개의 AI 스타트업이 다양한 에이전트를 만들고 있고, 모두 실패해서 코딩 에이전트만 남는다고 단정하기는 어렵다.
- 따라서 agentic AI 전체 시장은 아직 초기 단계이며, 토큰 수요와 인프라 수요는 중장기적으로 더 커질 가능성이 있다.

### 2.2 API 기반 frontier model 사용 비용은 점점 부담이 될 수 있음

- 현재 OpenAI, Anthropic 등의 모델은 가격 대비 성능이 아직 기업들이 감내 가능한 수준이지만, 장기적으로는 가격 인상 또는 엔터프라이즈 과금 강화가 일어날 수 있다.
- Google, Meta 같은 hyperscaler는 비용을 감당할 수 있지만, 그보다 작으면서도 엔지니어 수가 수천 명 규모인 대형 IT 기업들은 비용 압박을 받을 수 있다.
- 이 구간이 잠재 고객군으로 보인다. 너무 작은 회사는 자체 인프라 운영보다는 계속 API나 네오클라우드를 쓸 가능성이 높고, hyperscaler는 자체 연구/인프라 역량이 강하다.

### 2.3 타깃 고객

- 1차 타깃은 hyperscaler는 아니지만 충분히 큰 IT 기업.
- 예: 수천 명의 엔지니어를 보유하고, 코딩 에이전트나 LLM 기반 업무 자동화를 적극적으로 쓰는 기업.
- 이들은 현재 Claude/OpenAI 등을 쓰고 있지만, 비용이 커지면 오픈소스 모델 기반 대안을 검토할 가능성이 있다.
- 국내에도 이런 규모의 기업이 존재할 수 있으나, 시장은 국내 한정이 아니라 글로벌로 봐야 한다.

### 2.4 네오클라우드와의 관계

- 네오클라우드는 데이터센터, GPU 서버, 전력, 냉각 등 물리 인프라를 제공하는 쪽이다.
- 인터뷰에서 논의된 스타트업 포지션은 네오클라우드 자체라기보다는, 그 위에서 LLM/코딩 에이전트를 효율적으로 돌리게 하는 서빙 소프트웨어 쪽에 가깝다.
- 즉 `모델 - 서빙 소프트웨어 - GPU/TPU/NPU 하드웨어 - 네오클라우드/데이터센터` 스택에서 소프트웨어 최적화 계층을 담당하는 그림이다.

### 2.5 하드웨어별 최적화가 핵심 역량

- 같은 모델도 GPU, TPU, NPU 등 어떤 하드웨어에서 돌리느냐에 따라 성능 특성이 달라진다.
- 단순히 “돌아가게 하는 것”과 “성능을 잘 뽑아내는 것”은 다르다.
- 로우레벨 컴파일러나 하드웨어 접근 계층은 하드웨어 회사가 제공해야 하지만, 그 위에서 모델 서빙 성능을 최적화하는 것은 별도의 소프트웨어 역량이다.
- vLLM 같은 서빙 스택에 하드웨어를 붙이는 작업도 쉽지 않고, 국내 NPU 업체들도 이 소프트웨어 레이어 확보에 많은 엔지니어를 투입하고 있는 것으로 언급됐다.

## 3. 기술 검증 관련 정리

### 3.1 FLOPS 기반 계산식의 의미

- AI 연산은 매우 단순화하면 대부분 곱하기와 더하기이며, 특히 곱하기 연산 비중이 크다.
- GPU의 이론 FLOPS는 코어 수, 클럭, 연산 유닛, utilization을 곱해 “초당 수행 가능한 연산량”을 추정하는 개념이다.
- 이를 모델 파라미터 수 또는 토큰당 필요한 연산량으로 나누면, 매우 높은 수준의 토큰 처리량 추정이 가능하다.
- 다만 이 방식은 다음 가정을 강하게 둔다.
  - 연산이 대부분 곱하기라고 본다.
  - GPU 코어가 충분히 활용된다고 본다.
  - 모델 구조가 단순하다고 본다.
  - memory bandwidth, communication, batching, scheduling overhead 등을 단순화한다.
- 결론적으로 방향성은 말이 되지만, 현실과 차이가 클 수 있으므로 단독 산식으로 쓰면 위험하다.

### 3.2 Decode 단계는 bandwidth 병목이 중요

- batch inference에서는 여러 요청이 같은 model weights를 공유한다.
- 하지만 KV cache는 사용자/요청별로 별도로 생성된다.
- 토큰 하나를 생성할 때 읽어야 하는 데이터는 대략 `model weights + batch size x KV cache`의 형태로 이해할 수 있다.
- decode 단계에서는 compute보다 memory bandwidth가 병목이 되는 경우가 많다.
- 따라서 TPS를 추정할 때 단순 FLOPS뿐 아니라 GPU memory bandwidth, KV cache 크기, batch size를 같이 봐야 한다.

### 3.3 MoE 모델은 dense 모델과 계산 로직이 다름

- dense 모델은 토큰 생성 시 전체 weight를 읽는다는 가정이 상대적으로 자연스럽다.
- MoE는 여러 expert 중 일부만 선택해 사용하기 때문에 매번 전체 weight를 읽는 구조가 아니다.
- 따라서 MoE 모델은 “전체 파라미터 수”가 크더라도 실제 활성화되는 파라미터 수가 더 작을 수 있다.
- 산식에는 전체 파라미터 수가 아니라 active parameters, expert 수, top-k routing 등을 반영해야 한다.
- 단순화를 위해 먼저 dense 모델 기준으로 계산하고, MoE는 별도 보정계수를 두는 접근이 현실적이다.

### 3.4 Dense, sparse, structured sparsity 구분

- dense는 weight matrix가 대부분 채워져 있는 구조다.
- sparse는 weight matrix에 0이 많아 일부 연산을 생략할 수 있는 구조다.
- 하지만 GPU는 임의 위치의 0을 자동으로 효율적으로 건너뛰기 어렵다.
- 실제 성능 개선을 얻으려면 structured sparsity처럼 하드웨어가 처리하기 좋은 패턴으로 0이 배치되어야 한다.
- MoE에서 말하는 sparsity는 expert gating 차원의 sparsity이고, matrix-level sparsity와는 구분해야 한다.

## 4. LLM 토큰 수요 모델링에 대한 조언

### 4.1 순수 이론식보다 profiling/benchmark 보정이 필요

- 이론식은 높은 수준의 의미는 있지만 정확한 추정에는 한계가 있다.
- 실제 GPU 서버에 모델을 올려 inference를 돌려보고 TPS, utilization, memory usage를 측정하는 profiling이 가장 현실적인 보정 방법이다.
- 직접 실험이 어렵다면 MLPerf 같은 실제 benchmark 또는 GPU/모델/배치 조건이 명시된 inference benchmark 데이터를 활용해야 한다.
- benchmark를 쓸 때는 반드시 다음 조건이 같이 있어야 숫자가 의미를 가진다.
  - GPU 종류와 개수
  - memory/HBM 구성
  - 모델명과 모델 크기
  - batch size
  - input length, output length
  - offline/online serving 조건
  - TPS, TPOT, latency 등 측정 metric

### 4.2 InferenceX/MLPerf류 데이터 활용 방향

- 교수는 “시스템 specification 없이 TPS만 있는 리더보드는 의미가 약하다”고 지적했다.
- 반대로 GPU 수, 모델, batch size, 서버 구성이 명시된 실제 측정값이라면 토큰 생산량 추정에 활용 가능하다고 보았다.
- 따라서 기존 프로젝트의 `tps/MW` 로직은 이론식보다 benchmark 기반으로 보정하는 것이 더 타당하다.
- 특히 짧은 대화, 긴 대화, agentic trace처럼 input/output length와 KV cache 부담이 다른 workload를 분리하는 방향은 합리적이다.

### 4.3 세계 전체 또는 고객사별 토큰 수요 추정

가능한 접근:

1. 애플리케이션 유형별 사용자 수를 추정한다.
2. 사용자당 일일/월간 토큰 생성량을 가정한다.
3. 모델군별 사용 비중을 나눈다.
4. 각 모델/GPU/workload별 benchmark TPS를 적용한다.
5. 필요한 GPU 수, 전력, 데이터센터 용량으로 역산한다.

주의점:

- OpenAI, Anthropic, Google, Meta 같은 닫힌 모델은 실제 모델 크기와 serving architecture를 알기 어렵다.
- 모델 크기 추정은 가능하지만 대부분 소문 또는 외부 추정에 의존한다.
- Meta의 공개 Llama 모델도 실제 Meta 내부 서비스 모델과 같다고 보기 어렵다.
- 따라서 기업별 토큰 수요를 역산할 때는 모델 스펙을 확정값으로 쓰기보다 scenario range로 두는 것이 안전하다.

## 5. Reverse modeling 관련 결론

### 5.1 현재 형태의 simulator는 주로 정방향 도구

- 스펙을 넣으면 성능을 예측하는 정방향 시뮬레이션은 가능하다.
- 반대로 “목표 TPS가 있으니 필요한 GPU/메모리/구성을 자동으로 찾아달라”는 역방향 설계는 현재로서는 어렵다.
- 역방향을 하려면 GPU 수, memory 구성, CXL 사용 여부, cluster 수 등 변수가 많아 design space search 문제가 된다.

### 5.2 현실적인 역산 방법

- 변수를 하나로 제한하면 가능하다.
- 예: 모델과 GPU 종류를 고정하고 GPU 수만 늘려가며 목표 TPS에 도달하는 지점을 찾는 방식.
- 하지만 전체 시스템 설계까지 자동으로 최적화하려면 비용, latency, bandwidth, cluster topology 등 복수 변수를 탐색해야 한다.
- 그래서 실무적으로는 “정밀한 최적 설계”보다 “최소 필요 GPU 수의 범위” 또는 “구성 간 우열 비교” 정도가 적절하다.

## 6. Hyperscaler의 실제 최적화 방식에 대한 시사점

- Meta 같은 대형 기업은 NVIDIA의 신형 DGX 서버 프로토타입을 가져와 하드웨어/소프트웨어 co-design 팀이 붙어 성능을 튜닝한다.
- NVIDIA와 사전 협의와 커스터마이징도 많이 하는 것으로 언급됐다.
- 이들은 단순히 GPU를 많이 사는 것이 아니라, 새 서버 구성에서 최대한 많은 token throughput을 뽑아내기 위해 configuration을 계속 실험한다.
- 따라서 hyperscaler의 inference capacity는 “GPU 수 x 이론 성능”으로 단순 계산하기 어렵고, 운영 최적화 역량이 큰 차이를 만든다.

## 7. 프로젝트에 반영할 실무적 시사점

### 7.1 tps/MW 모델을 개선할 방향

- GPU별 이론 FLOPS 기반 계산은 보조 지표로만 사용한다.
- 핵심은 benchmark 기반 `tokens/sec/GPU` 또는 `tokens/sec/MW`를 사용한다.
- workload를 최소 세 그룹으로 분리한다.
  - 짧은 대화: 짧은 ISL/OSL, latency 민감
  - 긴 대화: 긴 ISL, KV cache와 memory bandwidth 부담 증가
  - agentic trace: 긴 context, 반복 호출, tool use, 긴 output 가능성
- 각 workload별 benchmark 평균값을 GPU별로 계산하고, 전체 토큰 수요는 workload mix로 가중 평균한다.

### 7.2 모델별 보정계수

- dense 모델과 MoE 모델은 별도로 분리한다.
- MoE는 total parameter가 아니라 active parameter 기준 보정이 필요하다.
- closed model은 정확한 architecture를 모르므로 pessimistic/base/optimistic scenario로 나눈다.
- benchmark에 없는 모델은 유사 모델군으로 mapping하되, 신뢰도 flag를 붙인다.

### 7.3 보고서 표현상 주의

- “정확한 수요 예측”보다는 “공개 benchmark와 합리적 workload mix를 이용한 scenario estimate”로 표현하는 것이 안전하다.
- 닫힌 모델의 파라미터 수, serving stack, batch policy는 불확실성이 크다고 명시해야 한다.
- 결과 표에는 반드시 입력값의 confidence를 붙이는 편이 좋다.

## 8. 다음 액션

1. InferenceX/MLPerf류 benchmark에서 GPU, model, batch, ISL, OSL, TPS가 함께 있는 row만 사용한다.
2. 짧은 대화, 긴 대화, agentic trace로 benchmark row를 분류한다.
3. GPU별 `TPS/GPU`, `TPS/MW` 평균을 workload별로 계산한다.
4. closed model은 model size scenario를 두고, dense/MoE 여부에 따라 보정한다.
5. customer별 토큰 수요 모델은 “사용자 수 x 사용자당 토큰 x workload mix”에서 시작한다.
6. 최종 산출물은 현재 capacity, planned capacity, required GPU/MW, utilization-adjusted token capacity를 함께 보여준다.

## 9. 미팅에서 남은 핵심 질문

- 고객사별 실제 토큰 수요를 어떤 외부 지표로 proxy할 것인가?
- OpenAI/Anthropic/Google/Meta의 closed model serving architecture를 어떤 scenario로 둘 것인가?
- agentic trace의 평균 ISL/OSL, call depth, tool-call overhead를 어떻게 정의할 것인가?
- benchmark 데이터가 offline serving인지 online serving인지 구분 가능한가?
- GPU 전력은 chip TDP 기준이 아니라 all-in facility/server power 기준으로 통일할 것인가?

