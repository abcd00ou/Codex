<!-- converted from study_ai_networking_lv3_20260326.docx -->


[Lv.3 전문가] AI 클러스터 네트워킹 심화
InfiniBand & Ethernet — AI 병목 해소 기술부터 투자 시그널까지
대상: 반도체 마케팅 종사자  |  기준일: 2026-03-24  |  난이도: 기술 기초 → 중급
본 문서는 AI 클러스터 네트워킹(InfiniBand & Ethernet)을 반도체 마케팅 관점에서 이해하기 위한 심층 학습 자료입니다. GPU 간 통신의 기술 원리부터 수혜 기업 분석, 2026-2027 투자 사이클까지 체계적으로 다룹니다.

# 1장. 왜 네트워킹이 AI 병목인가 — Communication Wall
AI 데이터센터에서 GPU 성능을 100% 발휘하지 못하게 하는 가장 큰 원인은 GPU 간 통신 속도입니다. 수천 개의 GPU가 협력해 하나의 모델을 학습할 때, GPU들이 서로 데이터를 주고받는 속도가 전체 학습 시간을 결정합니다.
## 1.1 분산 AI 학습의 통신 문제
[개념] 분산 학습(Distributed Training): GPT-4와 같은 대형 모델은 단일 GPU에 들어가지 않습니다. 수천 개 GPU에 모델을 분산하고, 각 GPU가 계산한 그래디언트(기울기)를 모든 GPU와 공유(AllReduce)해야 합니다.
[마케터 관점] 마케팅 비유: 1,000명의 연구원이 각자 실험을 하고 매 시간마다 전체 결과를 공유해야 하는 상황. 공유 채널(네트워크)이 느리면 연구원(GPU)이 아무리 빠르게 일해도 전체 속도가 느려집니다.
## 1.2 Communication Wall이란
[개념] Communication Wall: GPU 연산 성능(TFLOPS)은 2년마다 2-3배 향상되는 반면, 네트워크 대역폭은 같은 기간 1.5-2배 증가에 그칩니다. 이 격차가 벌어질수록 GPU들이 통신을 기다리며 낭비하는 시간이 늘어납니다.
[계산 예제] 실측 예시 — H100 8개 DGX 서버 학습 효율:
  이론 성능: 8 × 989 TFLOPS = 7,912 TFLOPS
  실제 학습 효율(MFU): 약 38-45% (Model Flop Utilization)
  손실 원인의 40%+: GPU 간 통신 대기(AllReduce 동기화)
  → 네트워크 대역폭 2배 향상 시 MFU 10-15%p 개선 가능
[마케터 관점] 투자 시사점: GPU(NVIDIA)에 $100 쓸 때 네트워킹에도 $15-25 지출이 발생합니다. NVIDIA GPU 판매 증가 → 네트워킹 수요 자동 동반 증가. AI 클러스터 네트워킹 시장: 2024 $8B → 2027 $25B (Omdia).
## 1.3 주요 통신 패턴 이해

### 참고자료


# 2장. AI 네트워킹 토폴로지 — 클러스터 구조 설계
수천 개의 GPU를 어떻게 연결하는가 — 토폴로지(Topology)는 네트워크 비용, 성능, 확장성을 동시에 결정합니다. AI 클러스터에는 세 가지 주요 토폴로지가 사용됩니다.
## 2.1 Fat-Tree 토폴로지
[개념] Fat-Tree: 위로 올라갈수록 링크가 더 굵어지는(많아지는) 트리 구조. 어느 두 노드 사이에도 동일한 대역폭이 보장되는 '무차별 접속(Non-blocking)' 구조. Leaf 스위치 → Spine 스위치 → Core 스위치 3계층으로 구성.
[마케터 관점] Fat-Tree 비유: 고속도로 인터체인지. 어느 출발지에서 목적지로도 같은 속도의 경로가 있습니다. 단점: 스위치/케이블 수가 많아 비용이 높음. 주요 사용처: AWS, Google의 HPC 클러스터.
## 2.2 DragonFly 토폴로지
[개념] DragonFly: GPU 그룹을 '슈퍼노드'로 묶고, 슈퍼노드 간 소수의 링크로 연결. Fat-Tree 대비 케이블 수 최대 50% 절감. 단, 특정 경로에서 대역폭 불균일 발생 가능.
[마케터 관점] DragonFly 비유: 거점 도시 사이를 고속 직통 노선으로 연결하는 구조. 비용 효율적이나 혼잡 구간이 생길 수 있음. NVIDIA의 InfiniBand 대규모 클러스터에 주로 채택.
## 2.3 Rail-Optimized 토폴로지
[개념] Rail-Optimized: AI 학습의 AllReduce 패턴에 최적화된 구조. 서버 내 GPU들이 여러 스위치에 분산 연결(Rail)되어, AllReduce 트래픽이 네트워크에 고르게 분산됩니다.
[마케터 관점] Rail-Optimized 비유: 여러 계산원(스위치)에 고객을 골고루 배분하는 슈퍼마켓 계산대. 대기 줄이 한 곳에 몰리지 않아 전체 처리량이 최대화됩니다. Arista, Meta의 클러스터가 이 방식을 채택.

### 참고자료


# 3장. InfiniBand vs RoCE vs Ethernet — 기술 비교
AI 클러스터 인터커넥트 기술의 3대 선택지를 비교합니다. 이 선택이 NVIDIA vs Broadcom vs Marvell 중 누가 수혜를 받는지를 결정합니다.
## 3.1 핵심 기술 비교표

## 3.2 InfiniBand 세대별 로드맵
[개념] InfiniBand는 IBTA(InfiniBand Trade Association) 표준 기술로, NVIDIA/Mellanox가 실질적으로 독점 개발·공급합니다. 각 세대는 'HDR(High Data Rate)' → 'NDR(Next Data Rate)' → 'XDR(Extended Data Rate)' 명명.

[계산 예제] NDR vs XDR 투자 임팩트 계산:
  GB200 NVL72 랙 1개 = 72 GPU × 포트당 $2,000 (NDR NIC) = $144,000 네트워킹 비용
  XDR로 전환 시 포트당 ~$2,800 → 랙당 $201,600 (40% 증가)
  2026 GB200 출하 예상 100만 GPU → 교체 수요: ~$2-3B 추가 네트워킹 매출
## 3.3 RoCE — InfiniBand의 이더넷 버전
[개념] RoCE(RDMA over Converged Ethernet): RDMA(원격 직접 메모리 접근) 기술을 표준 이더넷 위에서 구현. InfiniBand의 낮은 지연시간을 이더넷 인프라에서 부분적으로 구현. NVIDIA의 ConnectX NIC가 IB와 RoCE를 모두 지원.
[마케터 관점] RoCE의 마케팅 포지션: '이더넷 인프라를 유지하면서 InfiniBand에 가까운 성능'. 기존 이더넷 투자를 보호하려는 기업들이 선호. 그러나 실제 AI 학습 대형 클러스터에서는 여전히 순수 IB가 우위.
### 참고자료


# 4장. NVIDIA/Mellanox 독점 — NVLink와 InfiniBand의 이중 구조
NVIDIA는 AI 클러스터 네트워킹을 두 레이어에서 동시에 지배합니다: 서버 내부(NVLink)와 서버 간(InfiniBand). 이 이중 독점 구조가 NVIDIA의 해자(Moat)를 더욱 강화합니다.
## 4.1 GB200 NVL72 — 이중 네트워크 구조
[개념] GB200 NVL72 랙 구성:
• 내부 연결(Intra-rack): NVLink 5.0
  - 72 GPU를 NVSwitch 9개가 완전 연결(Full Mesh)
  - 양방향 대역폭: GPU당 1.8TB/s
  - 지연시간: ~1μs 미만
• 외부 연결(Inter-rack): InfiniBand NDR/XDR
  - 랙과 랙 사이, 수천 GPU 규모 연결
  - ConnectX-7 NIC + Quantum-3 스위치 조합
[마케터 관점] 비유: 한 건물(NVL72 랙) 안에서는 내부 엘리베이터(NVLink)로 빠르게 이동하고, 건물 간에는 지하철(InfiniBand)을 이용합니다. NVIDIA는 엘리베이터도, 지하철도 모두 공급합니다.

## 4.2 ConnectX-7 & Quantum-3 — InfiniBand 생태계
[개념] ConnectX-7 NIC(Network Interface Card): 서버에 장착되는 InfiniBand/이더넷 겸용 카드. NDR 400Gbps 지원, GPU-Direct RDMA로 GPU 메모리 직접 접근 가능.
Quantum-3 스위치: InfiniBand NDR 64포트 스위치. AI 클러스터의 '교환원' 역할. 포트당 $500-800 수준.
[마케터 관점] 시장점유율: NVIDIA InfiniBand ~80% (Omdia 2024). 2024년 NVIDIA의 네트워킹 사업부(전 Mellanox) 매출: 약 $3.5B+. GPU를 사면 NIC도, 스위치도 NVIDIA 것을 사야 하는 '락인' 효과.
## 4.3 NVLink vs InfiniBand — 언제 무엇을 쓰나

### 참고자료


# 5장. 이더넷 진영의 반격 — Ultra Ethernet & Broadcom
InfiniBand의 독점에 도전하는 이더넷 진영이 결집하고 있습니다. AI 워크로드에 최적화된 차세대 이더넷 표준과 하드웨어가 2025-2026년 본격 시장에 진입합니다.
## 5.1 Ultra Ethernet Consortium (UEC)
[개념] UEC(Ultra Ethernet Consortium): 2023년 결성된 AI 최적화 이더넷 표준화 단체. AMD, Intel, Meta, Microsoft, Oracle, Broadcom, Cisco, Arista 등 60개+ 기업 참여. 목표: InfiniBand 수준의 낮은 지연시간과 AI 최적화를 표준 이더넷으로 구현.
[마케터 관점] UEC의 전략적 의미: NVIDIA InfiniBand 독점에 대한 업계 연합 저항. 특히 클라우드 사업자(AWS, Azure, Google)는 자체 인프라 통제력을 위해 표준 이더넷 기반 솔루션을 선호합니다.

## 5.2 Broadcom Tomahawk 5 — 이더넷 스위칭 최강자
[개념] Broadcom Tomahawk 5 (BCM78900): 2023년 출시. 총 스위칭 용량 51.2Tbps — 역대 최고. 512포트 × 100GbE 또는 64포트 × 800GbE 구성 가능. AI 클러스터의 Spine 스위치로 채택 확산 중.
[마케터 관점] Broadcom 네트워킹 반도체 매출 (2025년 예상): ~$8B. 주요 고객: Meta, Microsoft, Google이 자체 AI 클러스터에 Tomahawk 기반 스위치 채택. NVIDIA InfiniBand를 쓰지 않는 하이퍼스케일러 = Broadcom 매출.
## 5.3 Arista — AI 네트워크 오케스트레이션
[개념] Arista Networks: 400G/800G 네트워크 장비와 EOS(Extensible Operating System) 기반 소프트웨어 솔루션 제공. AI 클러스터 전용 'AI Spine' 제품군 2024년 출시.
[마케터 관점] Arista 투자 포인트: 하드웨어가 아닌 소프트웨어·서비스 매출 비중 증가 중. AI 클러스터 관리 자동화(AVD, AVS)로 반복 매출(Recurring Revenue) 확대. 2024 매출 성장률 20%+ 유지, AI 네트워킹 수혜 직접 반영.

### 참고자료


# 6장. 수혜 기업 분석 — 시장점유율·매출·밸류에이션
AI 클러스터 네트워킹 시장의 핵심 수혜 기업을 정량 데이터와 함께 분석합니다. 단순 기술 수혜 여부를 넘어 밸류에이션과 성장률을 함께 고려해야 합니다.
## 6.1 기업별 투자 매트릭스

## 6.2 투자 관점 요약
[마케터 관점] NVIDIA: 네트워킹 사업부 매출이 GPU 매출의 5-7% 수준이나, InfiniBand 독점으로 마진이 매우 높음. GPU 판매 → 자동으로 네트워킹 수요 창출.
[마케터 관점] Broadcom: 하이퍼스케일러가 자체 AI 클러스터에 이더넷을 선택할수록 수혜. 커스텀 AI 칩(Google TPU, Meta MTIA 인터커넥트) 설계 수주도 병행.
[마케터 관점] Marvell: 800G 이더넷 PHY 시장에서 NVIDIA에 대한 대안 제공. 커스텀 ASIC(Amazon Trainium 네트워킹) 수주로 성장 가속화.
[마케터 관점] Arista: 순수 AI 네트워킹 장비 플레이어로 가장 직접적 수혜. 하지만 밸류에이션이 이미 상당 부분 반영됨. 소프트웨어 매출 비중 증가가 추가 멀티플 확장의 열쇠.
[주의] 주요 리스크: NVIDIA가 이더넷 진영(UEC)에 본격 참여하거나, 하이퍼스케일러들이 자체 네트워킹 ASIC을 내재화(In-house)할 경우 Broadcom·Marvell·Arista의 시장이 잠식될 수 있음.
### 참고자료


# 7장. Phase 4 투자 파동 — 2026-2027 네트워킹 업그레이드 사이클
AI 인프라 투자는 단계적(Phase)으로 진행됩니다. 현재 Phase 3(전력·냉각) 병목 해소가 진행 중이며, 2026-2027년 Phase 4로 네트워킹이 핵심 업그레이드 대상이 됩니다.
## 7.1 AI 인프라 투자 단계

## 7.2 2026-2027 네트워킹 업그레이드 드라이버
Phase 4 네트워킹 업그레이드를 촉발하는 3가지 핵심 요인:

① GB200/B200 채택 확산: GB200 NVL72는 랙당 72 GPU 연결에 XDR 800Gbps InfiniBand를 요구. 기존 HDR 200Gbps 인프라는 교체 대상.

② 클러스터 규모 확대: 1만 GPU → 10만 GPU 클러스터로 확장 시 네트워크 홉(Hop) 수 증가 → Fat-Tree에서 DragonFly로 토폴로지 전환 필요.

③ 이더넷 진영의 성숙: UEC 400GbE/800GbE 표준 확정(2025~) → 이더넷 AI 클러스터 구축 본격화 → Broadcom/Arista 수요 증가.
[계산 예제] Phase 4 투자 규모 추산:
  2026년 AI GPU 출하 예상: H100급 100만개 + GB200급 50만개
  GPU당 네트워킹 지출 비율: $15,000-25,000 (GPU 가격의 50-80%)
  → 2026년 AI 네트워킹 투자: $22B~37B
  Omdia 예측($25B, 2027)과 정합. 연평균 성장률 ~35%.
## 7.3 투자 타이밍 — 언제 진입해야 하는가
[마케터 관점] 일반 원칙: 병목 인식 시점에서 주가 선행 약 6개월.
Phase 4 신호: ① GB200 출하량 데이터 발표, ② 하이퍼스케일러 CapEx에서 네트워킹 비중 증가 언급, ③ Broadcom/Arista AI 관련 수주잔고 가이던스 상향.
[주의] 리스크: AI 수요 둔화 시 네트워킹 업그레이드 연기 가능. 특히 Arista처럼 밸류에이션이 높은 종목은 가이던스 미스 시 급격한 멀티플 수축 위험.
### 참고자료


# 심화 분석
이 섹션은 Level 2 심화 과정으로, Rail-optimized 토폴로지 설계 원리와 400G→800G 업그레이드 비용 모델을 다룹니다.
## Rail-Optimized 토폴로지 설계 원리
Rail-optimized 토폴로지는 NVIDIA GB200 NVL72 클러스터에 최적화된 AI 전용 네트워크 아키텍처입니다. 기존 Fat-Tree와 근본적으로 다른 설계 원리를 이해합니다.
핵심 개념: Rail = 동일 InfiniBand 스위치에 연결된 GPU 그룹. 각 GPU는 자신의 'Rail 스위치'에만 연결 → 첫 번째 hop이 항상 동일 스위치.

GB200 NVL72 Rail 설계 상세: 72 GPU → 9그룹 × 8 GPU → 각 그룹이 1개 InfiniBand 스위치에 연결. 인트라-레일: NVLink 5.0 (1.8TB/s) 처리. 인터-레일: Quantum-3 InfiniBand 400Gb/s 연결. 결과: AllReduce 효율 기존 대비 30-40% 향상 → GPU 실제 활용률(MFU) 개선.
설계 시 고려사항: Rail 경계를 넘는 통신이 발생하면 병목. 모델 병렬화 전략(Tensor Parallel, Pipeline Parallel)을 Rail 구조에 맞게 설계 필요. Megatron-LM의 Tensor Parallel = Rail 내, Pipeline Parallel = Rail 간 구조가 표준.
## 400G→800G 업그레이드 비용 모델
현재 주류인 400G InfiniBand/Ethernet에서 800G로 업그레이드 시 발생하는 비용을 데이터센터 규모별로 계산합니다.
가정: 10,000 GPU 클러스터, 랙당 8 GPU(NVL72 기준), 스위치 포트당 비용 기준.

10,000 GPU 클러스터의 400G → 800G 전체 업그레이드 총비용: 스위치 $7.5M + 광모듈 $12M + 케이블 $8M = ~$27.5M. 400G NDR 기준 비용 대비 +$19.3M (+234%). 투자 시사점: Mellanox/NVIDIA(스위치), Lumentum/II-VI/Coherent(광모듈), Amphenol/TE Connectivity(케이블) 수혜. 업그레이드 사이클: 2026-2027년 대규모 800G 전환 예상 → 관련 기업 주가 선행.
# 전문가 심층 분석
이 섹션은 Level 3 전문가 과정으로, XDR 800Gbps 차세대 InfiniBand 로드맵과 광네트워킹(Si Photonics) 전환 타임라인을 다룹니다.
## XDR 800Gbps 차세대 InfiniBand 로드맵
NVIDIA Mellanox의 InfiniBand 로드맵은 2년 주기로 세대를 발전시켜 왔습니다. 차세대 XDR(eXtended Data Rate) 800Gbps의 기술 원리와 시장 영향을 분석합니다.

XDR의 기술 도전: 200Gbps PAM4 신호는 SI(Signal Integrity) 문제 심화. 케이블 길이 제한 더욱 엄격해짐 (DAC: 최대 2m, 광케이블 필수). 스위치 칩 전력 소비 증가 → Broadcom Tomahawk 6 경쟁 (400G Ethernet 진영). NVIDIA InfiniBand vs Broadcom Ethernet 대결이 XDR 세대에서 본격화 예상.
XDR 시장 임팩트: Mellanox XDR 출시 시 $8-12B 교체 수요 발생 예상. 2026-2027년 AI 클러스터 신규 구축 + 기존 NDR 업그레이드 수요 중첩. 모니터링: NVIDIA SC(Supercomputing) 컨퍼런스 (매년 11월) XDR 발표 여부.
## 광네트워킹(Si Photonics) 전환 타임라인
전통적인 구리 케이블 + 전기신호 방식의 한계로, 실리콘 포토닉스(Si Photonics) 기반 광네트워킹으로의 전환이 가속화되고 있습니다.

투자 관점: 2026-2027년 CPO 도입 → 기존 플러그인 광모듈 기업 매출 타격 가능성. 동시에 CPO 제조 역량 보유 기업(Intel PSG, Broadcom)에는 기회. 국내 관련 기업: 오이솔루션, 이노광(광모듈), 소프트웨이브(광 부품). 2030년 온-칩 포토닉스 전환 시 반도체 공정 혁명 → TSMC 등 파운드리 수혜.
# 8장. 복습 문제 & 종합 정리
## 복습 문제 (능동적 학습)
아래 질문에 먼저 스스로 답해보고, 힌트를 확인하세요. 답을 '설명할 수 있으면' 이해한 것입니다 (페인만 기법).
Q1. GPU 1,000개 클러스터에서 AllReduce가 학습 속도에 미치는 영향을 설명하고, 왜 네트워크 대역폭이 GPU 성능보다 더 중요한 병목이 될 수 있는지 논하라.
힌트: 1장의 Communication Wall, MFU 38-45% 데이터를 활용하세요. '비동기 학습'이 이를 어떻게 완화하는지도 생각해보세요.
유형: 기술 이해 + 비즈니스 임팩트

Q2. Fat-Tree vs DragonFly 토폴로지를 각각 '스위치 비용'과 '대역폭 균일성' 두 축으로 비교하라. 어떤 상황에서 어느 쪽을 선택하겠는가?
힌트: 2장 토폴로지 비교표를 참고하세요. 클러스터 규모(소형 vs 대형)에 따라 답이 달라집니다.
유형: 기술 비교 + 의사결정

Q3. NVIDIA가 InfiniBand 시장 80%를 점유하면서도 이더넷 진영(UEC)이 성장할 수 있는 근거를 3가지 이상 제시하라.
힌트: 하이퍼스케일러의 벤더 락인 회피 전략, 비용 구조, 표준화 이점을 중심으로 생각해보세요.
유형: 시장 구조 분석

Q4. GB200 NVL72 랙이 NVLink(내부)와 InfiniBand(외부)를 동시에 사용하는 이중 구조의 이유를 기술적·비즈니스적 관점에서 설명하라.
힌트: 4장의 NVLink vs InfiniBand 비교표를 활용하세요. '왜 NVLink만으로는 대형 클러스터를 구성하기 어려운가'를 생각해보세요.
유형: 기술 구조 이해

Q5. Broadcom과 Arista의 수혜 시나리오를 비교하라. 각 회사가 AI 네트워킹에서 어떤 다른 포지션을 가지며, 어느 회사가 더 높은 밸류에이션 프리미엄을 받아야 하는가?
힌트: 6장의 기업 매트릭스와 밸류에이션 데이터를 활용하세요. 소프트웨어 매출 비중의 중요성도 고려하세요.
유형: 투자 분석

Q6. Phase 4 네트워킹 업그레이드 투자 진입 시점을 판단하는 3가지 신호(Signal)를 정의하고, 각 신호가 어떤 종목의 매수 신호가 되는지 연결하라.
힌트: 7장의 투자 타이밍 섹션을 참고하세요. '선행 지표'가 '후행 지표'와 어떻게 다른지 구분해보세요.
유형: 실무 적용 (투자 전략)

## 정답 가이드 (핵심 포인트)
[Q1 핵심] H100 GPU의 실제 학습 효율(MFU) 38-45%: 이론 성능의 절반 이상이 통신 대기로 낭비. 1,000 GPU AllReduce: 각 GPU가 그래디언트를 전체와 공유 → O(N) 통신 복잡도. 네트워크 대역폭 2배 향상 시 MFU 10-15%p 개선 → GPU 추가 구매보다 ROI 높을 수 있음.
[Q2 핵심] Fat-Tree: 스위치 비용 높음(N^2 비례), 대역폭 완전 균일. 소규모~중규모, 최고 성능 요구 클러스터에 적합. DragonFly: 케이블 50% 절감, 대역폭 일부 불균일. 대규모(수만 GPU) 클러스터에서 비용 우위. 선택 기준: 예산 vs 성능 일관성.
[Q3 핵심] ① 벤더 락인 회피: AWS·Azure·Google은 NVIDIA 의존 축소 전략. ② 비용: IB NDR NIC ($2,000) vs 이더넷 400G NIC ($400-600), 5배 차이. ③ 기존 인프라 활용: 이더넷 장비는 기존 데이터센터 인프라와 통합 용이. UEC 표준 확정으로 성능 격차도 좁혀지는 중.
[Q4 핵심] 기술: NVLink는 랙 내부만 가능(거리 제한, 전용 케이블). IB는 수km 거리의 수천 GPU 연결 가능. 비즈니스: NVLink = NVIDIA 독점 → 고마진 고수익. IB = 표준 기반이나 Mellanox 독점 유지 → 역시 고마진. 이중 구조로 NVIDIA가 클러스터 전체 네트워킹 예산 장악.
[Q5 핵심] Broadcom: ASIC 설계, 파운드리 납품 → 장비 가격에 덜 민감, 물량 증가가 핵심. 하이퍼스케일러 자체 클러스터 확장 = Broadcom 수혜 직결. Arista: 장비 + 소프트웨어 번들 → 높은 마진과 반복 매출. AI 네트워크 자동화(EOS) 소프트웨어 비중 증가 시 SaaS 멀티플 적용 가능 → 밸류에이션 프리미엄 정당화.
[Q6 핵심] 신호 ①: GB200 출하량 분기 데이터 → NVIDIA 네트워킹 수주 증가 → IB 관련주 매수. 신호 ②: 하이퍼스케일러 CapEx 발표에서 네트워킹 비중 증가 → Broadcom, Arista. 신호 ③: UEC 표준 확정 뉴스 → 이더넷 채택 가속화 → Broadcom, Marvell, Arista 동반 수혜.

# 종합 참고문헌

| 통신 패턴 | 설명 | 사용 시나리오 | 특성 |
| --- | --- | --- | --- |
| AllReduce | 모든 GPU가 그래디언트를 합산·공유 | 데이터 병렬 학습 | 가장 대역폭 집중적 |
| AllGather | 분산된 텐서를 전체 GPU가 수집 | 모델 병렬 학습 | 용량 집중적 |
| ReduceScatter | 합산 후 결과를 분산 저장 | ZeRO 최적화 | AllReduce의 절반 대역폭 |
| P2P Send/Recv | GPU 쌍 간 직접 전송 | 파이프라인 병렬 학습 | 지연시간 민감 |
| Broadcast | 1개 GPU → 전체 배포 | 파라미터 초기화 | 희귀, 소량 |
| 출처 | URL | 설명 | 연도 |
| --- | --- | --- | --- |
| SemiAnalysis — AI Cluster Networking Deep Dive | https://www.semianalysis.com/p/ai-cluster-networking-deep-dive | Fat-Tree vs DragonFly 토폴로지 비교, NVIDIA IB 독점 구조 분석 | 2024 |
| Omdia — AI Cluster Networking Market 2024 | https://omdia.tech.informa.com/ | AI 클러스터 네트워킹 시장 규모 2024 $8B → 2027 $25B 전망 | 2024 |
| 토폴로지 | 장점 | 단점 | 주요 사용처 |
| --- | --- | --- | --- |
| Fat-Tree | 고성능, 균일 대역폭 | 케이블/스위치 비용 높음 | AWS, Google, 초대형 HPC |
| DragonFly | 케이블 50% 절감, 확장성 | 대역폭 불균일 가능 | NVIDIA IB 대형 클러스터 |
| Rail-Optimized | AllReduce 최적화, 실용적 | 특화 설계 필요 | Meta, Arista 기반 클러스터 |
| Torus | 비용 효율, 근거리 통신 ↑ | 대형 확장 어려움 | Google TPU Pod |
| 출처 | URL | 설명 | 연도 |
| --- | --- | --- | --- |
| SemiAnalysis — AI Cluster Networking Deep Dive | https://www.semianalysis.com/p/ai-cluster-networking-deep-dive | Fat-Tree vs DragonFly 토폴로지 비교, NVIDIA IB 독점 구조 분석 | 2024 |
| Arista Networks — AI Networking Solutions | https://www.arista.com/en/solutions/ai-networking | Rail-Optimized 토폴로지, 400G/800G AI 스파인 스위치 제품군 | 2024 |
| Meta Engineering — AI Cluster Fabric Design | https://engineering.fb.com/2024/network-fabric/ | Meta의 400G 이더넷 기반 AI 클러스터 설계 사례 공개 | 2024 |
| 기술 | 지연시간 | 대역폭 | 비용 | 특징 | 주요 사용처 |
| --- | --- | --- | --- | --- | --- |
| InfiniBand (IB) | ~100ns | NDR 400Gbps | 매우 높음 ($$$) | NVIDIA 독점 생태계 | 대형 AI/HPC 클러스터, 최고 성능 요구 |
| RoCE v2 | ~1-5μs | 400Gbps~ | 중간 ($$) | 표준 이더넷 인프라 위 | 중규모 클러스터, 비용 최적화 |
| Ethernet (표준) | ~10-50μs | 400Gbps~800Gbps | 낮음 ($) | 범용, 멀티벤더 | 소규모~중규모, 분산 추론 |
| 세대 | 대역폭(포트당) | 출시연도 | 주요 AI GPU 세대 |
| --- | --- | --- | --- |
| EDR | 100Gbps | 2015 | A100 이전 HPC 클러스터 |
| HDR | 200Gbps | 2018 | A100/V100 시대 주력 |
| NDR | 400Gbps | 2022 | H100/H200 클러스터 현재 주력 |
| XDR | 800Gbps | 2025~ | GB200/B200 클러스터 차세대 |
| GDR | 1,600Gbps | 2027~ | 추정, Blackwell Ultra 이후 |
| 출처 | URL | 설명 | 연도 |
| --- | --- | --- | --- |
| InfiniBand Trade Association — IBA Specification | https://www.infinibandta.org/ibta-specification/ | InfiniBand 기술 표준, HDR/NDR/XDR 세대별 사양 공식 문서 | 2023 |
| IEEE — RDMA over Converged Ethernet (RoCE v2) | https://www.ieee802.org/ | RoCE 표준 기술 사양, InfiniBand 대비 구현 방식 비교 | 2023 |
| NVIDIA — InfiniBand 네트워킹 제품 페이지 | https://www.nvidia.com/en-us/networking/infiniband/ | ConnectX-7, Quantum-3 스위치 스펙, NDR 400Gbps 로드맵 공식 자료 | 2024 |
| 세대 | 양방향 대역폭(GPU당) | 채택 플랫폼 | 출시연도 |
| --- | --- | --- | --- |
| NVLink 3.0 | 600 GB/s | A100 GPU (DGX A100) | 2020 |
| NVLink 4.0 | 900 GB/s | H100 GPU (DGX H100) | 2022 |
| NVLink 5.0 | 1,800 GB/s | B200/GB200 NVL72 | 2024 |
| NVLink 6.0 | ~3,600 GB/s | Rubin GPU (예상) | 2026~ |
| 기술 | 대역폭 | 지연시간 | 사용 범위 | 특징 |
| --- | --- | --- | --- | --- |
| NVLink 5.0 | 1,800 GB/s (양방향) | ~1μs 미만 | NVL72 랙 내부 | NVIDIA 전용, 비공개 프로토콜 |
| InfiniBand NDR | 400 Gbps | ~100ns | 랙 간, 수천 GPU | IBTA 표준, Mellanox 독점 |
| InfiniBand XDR | 800 Gbps | ~80ns | GB200 이후 | 2025~ 채택 중 |
| 출처 | URL | 설명 | 연도 |
| --- | --- | --- | --- |
| NVIDIA — NVLink & NVSwitch 기술 문서 | https://www.nvidia.com/en-us/data-center/nvlink/ | NVLink 5.0 1.8TB/s 양방향 대역폭, GB200 NVL72 내부 구조 설명 | 2024 |
| NVIDIA — InfiniBand 네트워킹 제품 페이지 | https://www.nvidia.com/en-us/networking/infiniband/ | ConnectX-7, Quantum-3 스위치 스펙, NDR 400Gbps 로드맵 공식 자료 | 2024 |
| UEC 사양 | 내용 | 예상 시기 |
| --- | --- | --- |
| UEC Transport | AI AllReduce 최적화 전송 계층 | 2025~ |
| Congestion Ctrl | AI 트래픽 혼잡 제어 표준 | 2024~ |
| 800GbE | 800Gbps 이더넷 표준 | 2024~ |
| 1.6TbE | 1.6Tbps 차세대 이더넷 | 2026~ |
| 기업 | 주요 제품 | 기술 특징 | 시장점유율 | 포지션 |
| --- | --- | --- | --- | --- |
| Broadcom | Tomahawk 5 | 51.2Tbps 스위칭 | ~60% | 스위칭 ASIC |
| Marvell | Prestera, Alaska | 400G/800G 이더넷 | ~15% | PHY, 커스텀 ASIC |
| Cisco | Nexus 9000/9300 | AI 최적화 스위치 | ~12% | 장비 + 소프트웨어 |
| Arista | 7800R4, AI Spine | 800G 클러스터 스위치 | ~8% | 장비 + EOS |
| Intel | Tofino 3 | 프로그래머블 ASIC | ~5% | P4 프로그래머블 |
| 출처 | URL | 설명 | 연도 |
| --- | --- | --- | --- |
| Ultra Ethernet Consortium — 공식 사이트 | https://ultraethernet.org/ | UEC 기술 사양, AI 워크로드 최적화 이더넷 표준화 로드맵 | 2024 |
| Broadcom — Tomahawk 5 네트워킹 ASIC | https://www.broadcom.com/products/ethernet-connectivity/switching/stratadnx/bcm78900 | 51.2Tbps 스위칭 용량, AI 클러스터 최적화 기능 | 2023 |
| Arista Networks — AI Networking Solutions | https://www.arista.com/en/solutions/ai-networking | Rail-Optimized 토폴로지, 400G/800G AI 스파인 스위치 제품군 | 2024 |
| 기업 | 주요 제품 | 시장점유율 | 관련 매출/성장 | 밸류에이션 | 주요 촉매 |
| --- | --- | --- | --- | --- | --- |
| NVIDIA (Mellanox) | ConnectX-7 NIC, Quantum-3 IB 스위치 | InfiniBand ~80% | 네트워킹 ~$3.5B (2024E), 성장 40%+ | P/E 40x~50x | GB200 출하 가속 |
| Broadcom | Tomahawk 5, Jericho 3 ASIC | 이더넷 스위칭 ASIC ~60% | 네트워킹 ~$8B (2025E), 성장 25%+ | P/E 35x~45x | 하이퍼스케일러 자체 클러스터 확장 |
| Marvell | Prestera 스위칭, Alaska PHY | 이더넷 PHY ~20% | 데이터센터 ~$3B (2025E), 성장 30%+ | P/E 45x~55x | 커스텀 AI ASIC + 네트워킹 복합 수혜 |
| Arista | 7800R4 AI Spine, EOS 소프트웨어 | 대규모 이더넷 장비 ~8% | 연매출 ~$7B (2024E), 성장 20%+ | P/E 50x~60x | AI 인프라 확장 직접 수혜 |
| Cisco | Nexus 9000 AI, Silicon One | 엔터프라이즈 네트워킹 전체 ~12% | 전체 매출 ~$55B, AI 비중 낮음 | P/E 15x~20x | AI 클러스터 시장 진입 가속화 필요 |
| 출처 | URL | 설명 | 연도 |
| --- | --- | --- | --- |
| Bernstein Research — Networking Semiconductor Deep Dive | https://www.bernsteinresearch.com/ | Broadcom, Marvell, NVIDIA 네트워킹 반도체 시장점유율 분석 | 2024 |
| Goldman Sachs — AI Infrastructure Investment 2024 | https://www.goldmansachs.com/insights/articles/generative-ai-infrastructure | 네트워킹을 AI 공급망 4대 병목 중 하나로 지목, $200B 시장 분석 | 2024 |
| Morgan Stanley — AI Networking Winners 2025 | https://www.morganstanley.com/ideas/ai-networking | AI 네트워킹 수혜주 분석: Broadcom, Marvell, Arista 목표주가 업데이트 | 2025 |
| 단계 | 주요 시기 | 핵심 병목 | 내용 | 주요 수혜 |
| --- | --- | --- | --- | --- |
| Phase 1 | 2023 | GPU 확보 | NVIDIA H100 수요 폭증 | NVIDIA, TSMC |
| Phase 2 | 2023-24 | 메모리 병목 해소 | HBM3e, CoWoS 캐파 확대 | SK하이닉스, TSMC |
| Phase 3 | 2024-25 | 전력·냉각 | 데이터센터 전력 인프라, 액냉 시스템 | Vertiv, Eaton, GE Vernova |
| Phase 4 | 2025-26 | 네트워킹 업그레이드 | NDR→XDR, 800GbE 전환 | NVIDIA, Broadcom, Arista |
| Phase 5 | 2026-27 | 엣지·추론 최적화 | 추론 전용 칩, 엣지 AI 인프라 | ARM, Qualcomm, Marvell |
| 출처 | URL | 설명 | 연도 |
| --- | --- | --- | --- |
| Omdia — AI Cluster Networking Market 2024 | https://omdia.tech.informa.com/ | AI 클러스터 네트워킹 시장 규모 2024 $8B → 2027 $25B 전망 | 2024 |
| SemiAnalysis — AI Cluster Networking Deep Dive | https://www.semianalysis.com/p/ai-cluster-networking-deep-dive | Fat-Tree vs DragonFly 토폴로지 비교, NVIDIA IB 독점 구조 분석 | 2024 |
| 토폴로지 | 구조 | 장점 | AI 학습 최적화 | 적용 사례 |
| --- | --- | --- | --- | --- |
| 전통 Fat-Tree | GPU → ToR 스위치 → Spine 스위치 → Core 스위치 | 범용성, 다양한 트래픽 패턴 지원 | AllReduce 시 무작위 경로 → 혼잡 발생. AI 학습 패턴에 비효율 | 일반 클라우드 DC, 범용 HPC |
| Rail-Optimized | GPU 그룹 → Rail 스위치 (비블로킹). Rail 간 연결은 상위 레이어에서만 | AllReduce 트래픽 패턴 최적화. 비블로킹 스위칭으로 지연 최소화 | 단일 클러스터 내 AllReduce는 최소 홉. GPU 간 통신 레이턴시 -30~40% 감소 | AI 전용 클러스터 (GB200 NVL72) |
| DragonFly+Rail 하이브리드 | Rail 내부 + DragonFly 간 연결 | 스케일 확장성 + Rail 최적화 결합 | 복잡성 증가, 구성 어려움 | 10,000 GPU+ 초대형 클러스터 |
| 구분 | 비용 계산 | 설명 | 시기 | 비고 |
| --- | --- | --- | --- | --- |
| 400G HDR InfiniBand | 1,000포트 × $3,500/포트 = $3.5M | 현재 H100 클러스터 표준. Quantum-2 | 2022-2024년 구축 클러스터 | 수명: 3-4년 |
| 400G NDR InfiniBand | 1,000포트 × $4,200/포트 = $4.2M (+20%) | B200 클러스터 기본. Quantum-3 | 2024-2025년 신규 구축 | 800G NDR2로 포트 업그레이드 가능 |
| 800G NDR2 InfiniBand | 1,000포트 × $7,500/포트 = $7.5M (+79%) | 차세대 GB300/Rubin 대응 | 2025-2026년 예상 출시 | 400G NDR 대비 2배 처리량 |
| 광모듈 교체 비용 | 10,000 GPU × $1,200/광모듈 = $12M | 스위치 업그레이드 시 광모듈 전량 교체 | 전체 업그레이드 비용의 40-50% | 수혜: 광모듈 제조사(Lumentum, II-VI) |
| 케이블/배선 | 10,000 GPU × $800/케이블 세트 = $8M | 고속 케이블 (DAC → 액티브 광케이블) | 800G 전환 시 모든 케이블 교체 | 400G DAC → 800G AEC/AOC |
| 세대 | 출시 시기 | 기술 스펙 | 적용 대상 | 제품 |
| --- | --- | --- | --- | --- |
| HDR (200Gb/s) | 2018 | 50Gbps × 4레인 | H100 이전 세대, 많은 레거시 클러스터 | Quantum 스위치, ConnectX-6 |
| NDR (400Gb/s) | 2022 | 100Gbps × 4레인 (PAM4) | 현재 B200 클러스터 표준 | Quantum-3 스위치, ConnectX-7 |
| XDR (800Gb/s) | 2025-2026 예상 | 200Gbps × 4레인 (PAM4) | 차세대 GB300/Rubin GPU 대응 | Quantum-4 스위치 (미공개), ConnectX-8 (예상) |
| GDR (1,600Gb/s) | 2027-2028 예상 | 400Gbps × 4레인 또는 광학 | 2030년 AI 클러스터 대응 | Si Photonics 통합 가능성 |
| 시기 | 기술 발전 | 특징 | 수혜 기업/기술 | 채택률 |
| --- | --- | --- | --- | --- |
| 현재 (2024-2025) | 코-패키지드 옵틱스(CPO) 초기 도입. Intel, Broadcom CPO 샘플 출하 | 스위치 ASIC + 광모듈 별도 패키징. 전력 소비 높음, 거리 제한 | Lumentum, Coherent, II-VI (광모듈). 일반 스위치 + 플러그인 광모듈 | 낮음 (10% 미만) |
| 단기 (2026-2027) | CPO 양산 시작. 800G XDR InfiniBand에서 CPO 필수화 | 스위치 내부에 광모듈 통합. 전력 30% 절감, 밀도 향상 | Intel Silicon Photonics, Broadcom SerDes. 광모듈 기업들 CPO로 전환 | 중간 (30-40%) |
| 중기 (2028-2030) | 온-칩 포토닉스 (OCP, On-Chip Photonics). AI 칩에 광 인터페이스 직접 집적 | GPU↔GPU 광직결 → 구리 케이블 불필요. 대역폭 10TB/s+ 달성 가능 | NVIDIA+파트너사 (연구 단계). TSMC/Intel 파운드리 Si Photonics 공정 | 높음 (단, 비용 과제) |
| 장기 (2030+) | 광 통합 AI 서버: 광 인터커넥트 완전 대체 | 전력 효율 5-10배 개선. 열 발생 대폭 감소 | 새로운 생태계 구성 | AI 네트워킹 패러다임 전환 |
| 출처명 | URL | 설명 | 연도 |
| --- | --- | --- | --- |
| NVIDIA — InfiniBand 네트워킹 제품 페이지 | https://www.nvidia.com/en-us/networking/infiniband/ | ConnectX-7, Quantum-3 스위치 스펙, NDR 400Gbps 로드맵 공식 자료 | 2024 |
| NVIDIA — NVLink & NVSwitch 기술 문서 | https://www.nvidia.com/en-us/data-center/nvlink/ | NVLink 5.0 1.8TB/s 양방향 대역폭, GB200 NVL72 내부 구조 설명 | 2024 |
| Omdia — AI Cluster Networking Market 2024 | https://omdia.tech.informa.com/ | AI 클러스터 네트워킹 시장 규모 2024 $8B → 2027 $25B 전망 | 2024 |
| Ultra Ethernet Consortium — 공식 사이트 | https://ultraethernet.org/ | UEC 기술 사양, AI 워크로드 최적화 이더넷 표준화 로드맵 | 2024 |
| Broadcom — Tomahawk 5 네트워킹 ASIC | https://www.broadcom.com/products/ethernet-connectivity/switching/stratadnx/bcm78900 | 51.2Tbps 스위칭 용량, AI 클러스터 최적화 기능 | 2023 |
| Arista Networks — AI Networking Solutions | https://www.arista.com/en/solutions/ai-networking | Rail-Optimized 토폴로지, 400G/800G AI 스파인 스위치 제품군 | 2024 |
| SemiAnalysis — AI Cluster Networking Deep Dive | https://www.semianalysis.com/p/ai-cluster-networking-deep-dive | Fat-Tree vs DragonFly 토폴로지 비교, NVIDIA IB 독점 구조 분석 | 2024 |
| Marvell Technology — Data Infrastructure Solutions | https://www.marvell.com/products/networking-solutions.html | Marvell 400G/800G 이더넷 PHY, AI 가속 네트워킹 반도체 로드맵 | 2024 |
| IEEE — RDMA over Converged Ethernet (RoCE v2) | https://www.ieee802.org/ | RoCE 표준 기술 사양, InfiniBand 대비 구현 방식 비교 | 2023 |
| Meta Engineering — AI Cluster Fabric Design | https://engineering.fb.com/2024/network-fabric/ | Meta의 400G 이더넷 기반 AI 클러스터 설계 사례 공개 | 2024 |
| Cisco — AI/ML Data Center Networking | https://www.cisco.com/c/en/us/solutions/data-center-virtualization/ai-ml-networking.html | 이더넷 기반 AI 네트워크 솔루션, Nexus 9000 AI 최적화 | 2024 |
| Bernstein Research — Networking Semiconductor Deep Dive | https://www.bernsteinresearch.com/ | Broadcom, Marvell, NVIDIA 네트워킹 반도체 시장점유율 분석 | 2024 |
| Goldman Sachs — AI Infrastructure Investment 2024 | https://www.goldmansachs.com/insights/articles/generative-ai-infrastructure | 네트워킹을 AI 공급망 4대 병목 중 하나로 지목, $200B 시장 분석 | 2024 |
| InfiniBand Trade Association — IBA Specification | https://www.infinibandta.org/ibta-specification/ | InfiniBand 기술 표준, HDR/NDR/XDR 세대별 사양 공식 문서 | 2023 |
| Morgan Stanley — AI Networking Winners 2025 | https://www.morganstanley.com/ideas/ai-networking | AI 네트워킹 수혜주 분석: Broadcom, Marvell, Arista 목표주가 업데이트 | 2025 |