<!-- converted from ai_scm_study_20260324.docx -->


AI 공급망 인텔리전스 리포트
AI Supply Chain Intelligence — 심층 학습 자료
작성일: 2026년 03월 24일

# 1장. AI 공급망 개요
AI 공급망은 최종 사용자의 토큰 수요로부터 시작하여 GPU, HBM 메모리, 패키징(CoWoS), 파운드리(TSMC), 전력 인프라까지 연결된 복잡한 생태계입니다. 각 레이어는 상호의존적이며, 특정 레이어의 병목이 전체 공급망에 영향을 미칩니다.
## 1.1 밸류 체인 레이어 (14개)

## 1.2 공급망 흐름 다이어그램
토큰 수요 → AI 서비스 → 클라우드 DC → GPU 서버 → HBM/DRAM → 패키징(CoWoS) → 파운드리(TSMC)
                                    ↓
                         전력 인프라 / 네트워킹

* 핵심 병목: HBM(95%) → CoWoS(92%) → 전력(78%) 순
### 참고 자료


# 2장. 토큰 수요 → 하드웨어 수요 변환 모델
AI 서비스의 핵심 수요 단위는 '토큰'입니다. 토큰 처리량이 증가할수록 GPU, HBM 메모리, 전력 수요가 연쇄적으로 증가합니다.
## 2.1 핵심 수식

## 2.2 2026년 Q1 현재 수치 (Base 시나리오)

## 2.3 시나리오별 예측 (2024-2027)
### 참고 자료


# 3장. 병목 분석
공급망 병목은 수요 증가 속도가 공급 증설 속도를 초과할 때 발생합니다. 2025년 현재 HBM이 1차 병목이며, Power/Grid가 2026년 주요 병목으로 전환될 전망입니다.
## 3.1 레이어별 가동률 현황 (2026년 Q1 현재)

## 3.2 병목 전이 예측
### 참고 자료


# 4장. 하이퍼스케일러 CapEx 동향
Big 4(Microsoft, Google, Amazon, Meta) + xAI의 AI 인프라 투자는 2024년 $219B에서 2025년 $340B으로 55% 급증했습니다. 이 투자의 약 40-60%가 GPU 구매에 해당하며, NVIDIA 수혜가 가장 큽니다.
## 4.1 연도별 CapEx 테이블 (USD 십억)

## 4.2 AI 투자 시사점
- Microsoft: OpenAI 독점 파트너십 + Azure AI 서비스 확장. $80B CapEx 중 50%+ AI 인프라.
- Google: TPU v5 + NVIDIA GPU 병행. Anthropic 투자로 모델 다양화.
- Amazon: AWS 트레이닝 인프라 + Anthropic $40억 투자. Trainium2 자체 칩 개발.
- Meta: 오픈소스 LLaMA 전략. 자체 MTIA ASIC 칩 개발 중.
- xAI: Grok 모델. 멤피스 Colossus 클러스터 (10만 H100 → 20만 목표).
### 참고 자료


# 5장. 투자 네트워크 분석
AI 공급망의 자금 흐름을 투자 관계(Investment), 하드웨어 공급(Hardware Supply), 서비스 계약(Service), VC 투자(VC) 4가지 유형으로 분류합니다.
## 5.1 주요 투자 관계 요약

## 5.2 하드웨어 공급 구조 (독점/경쟁 분석)
### 참고 자료


# 6장. 투자 시그널 & 포지셔닝
현재 AI 공급망 투자 사이클은 Phase 2 (HBM & 패키징) 단계입니다. Phase 1 GPU 사이클이 무르익은 가운데, HBM 병목이 심화되며 메모리 업사이클이 진행 중입니다.
## 6.1 투자 단계별 로드맵

## 6.2 핵심 투자 시그널
### 참고 자료


# 7장. 2025-2027 수요 예측 시나리오
## 7.1 시나리오 가정

## 7.2 핵심 지표 예측 (2025실적 / 2026현재 / 2027-2028예측)

## 7.3 시나리오별 수혜/피해 기업
### 참고 자료

| 레이어 | 주요 기업 | 병목 위험도 |
| --- | --- | --- |
| 최종 사용자 | OpenAI, Anthropic, Google DeepMind | 낮음 |
| AI 서비스 | OpenAI API, Anthropic API, Cohere | 보통 |
| 클라우드/DC | Microsoft Azure, AWS, Google Cloud | 높음 |
| GPU 서버 | NVIDIA, AMD, Intel Gaudi | 위험 |
| ASIC | Google TPU, AWS Trainium, Microsoft Maia | 보통 |
| HBM 메모리 | SK Hynix, Samsung, Micron | 위험 |
| DRAM | Samsung, SK Hynix, Micron | 보통 |
| SSD 스토리지 | Solidigm, Samsung SSD, Kioxia | 낮음 |
| CPU | Intel, AMD, Ampere | 낮음 |
| 네트워킹 | Broadcom, Marvell, Arista | 높음 |
| 패키징(CoWoS) | TSMC CoWoS, ASE, Amkor | 위험 |
| 전력 인프라 | Vertiv, Eaton, Schneider Electric | 높음 |
| 파운드리 | TSMC, Samsung Foundry, SMIC | 높음 |
| 엣지 AI | Qualcomm, Apple, Samsung LSI | 낮음 |
| Sovereign AI | G42 (UAE), ARAMCO AI (Saudi), GENCI (France) | 보통 |
| 출처 | URL | 설명 |
| --- | --- | --- |
| Bloomberg AI 투자 차트 | https://www.bloomberg.com/graphics/2025-ai-investment-chart/ | AI 공급망 투자 관계 시각화 |
| Sequoia AI 인프라 분석 | https://www.sequoiacap.com/article/ais-600b-question/ | AI $600B 인프라 투자 분석 |
| IEA 전력 보고서 | https://www.iea.org/reports/electricity-2024 | 데이터센터 전력 수요 전망 |
| 수식명 | 공식 |
| --- | --- |
| Token → GPU | GPU 수량 = 일간 토큰 수 ÷ (GPU 초당 토큰 × 가동률) |
| GPU → HBM | HBM 수요(GB) = GPU 수량 × GPU당 HBM 용량 |
| KV 캐시 메모리 | KV Cache(GB) = 컨텍스트 길이 × 동시 사용자 × 2바이트 × 2 ÷ 10⁹ |
| SSD 수요 | SSD(GB) = 일간 RAG 토큰 × 문서당 토큰 ÷ 10⁹ × 바이트/토큰 |
| 전력 수요 | 전력(MW) = GPU 수량 × TDP × 서버 오버헤드(1.3) × PUE(1.4) ÷ 10⁶ |
| 지표 | 수치 | 비고 |
| --- | --- | --- |
| 토큰 수요 | 88.5T tokens/day | ChatGPT·Claude·Gemini·오픈소스 합산 |
| 필요 GPU | 60만 개 (H100 기준) | 가동률 85% 가정 |
| HBM 수요 | 48.2 PB | H100 80GB 기준 |
| 전력 수요 | 768 MW | PUE 1.4 적용 |
| SSD 수요 (RAG) | 연간 ~50 EB 누적 | RAG 비율 30% 가정 |
| 시나리오 | 연도 | 토큰/일 | GPU 수요 | 전력(MW) |
| --- | --- | --- | --- | --- |
| Base | 2024 | 29.4T/day (실적) | 38만 GPU | 7.1GW |
| Base | 2025 | 88.5T/day (실적) | 60만 GPU | 7.7GW |
| Base | 2026 ★현재 | 265T/day | 180만 GPU | 23GW |
| Bull | 2025 | 132.7T/day (실적) | 90만 GPU | 11.5GW |
| Bull | 2026 ★현재 | 398T/day | 270만 GPU | 34.7GW |
| Bear | 2025 | 61.9T/day (실적) | 42만 GPU | 5.4GW |
| Bear | 2026 ★현재 | 132T/day | 89만 GPU | 11.5GW |
| 출처 | URL | 설명 |
| --- | --- | --- |
| NVIDIA 분기 실적 | https://investor.nvidia.com/financial-information/quarterly-results/default.aspx | GPU 출하량 및 데이터센터 매출 |
| Goldman Sachs 전력 분석 | https://www.goldmansachs.com/insights/articles/AI-poised-to-drive-160-increase-in-power-demand | AI 전력 수요 160% 증가 예측 |
| IDC GPU 시장 | https://www.idc.com/getdoc.jsp?containerId=prUS52540424 | GPU 시장 출하량 데이터 |
| 레이어 | 가동률 | 심각도 |
| --- | --- | --- |
| HBM 메모리 | 92% | 위험 |
| CoWoS 패키징 | 88% | 위험 |
| 전력/DC | 85% | 위험 |
| 네트워킹 | 78% | 높음 |
| GPU 서버 | 82% | 높음 |
| Foundry | 84% | 높음 |
| ASIC | 78% | 높음 |
| DRAM | 62% | 보통 |
| SSD | 42% | 낮음 |
| CPU | 48% | 낮음 |
| Edge_AI | 60% | 보통 |
| 시기 | 병목 레이어 | 예상 가동률 | 원인 |
| --- | --- | --- | --- |
| 현재 (2025 H1) | HBM | 95% | SK Hynix CoWoS 물량 부족, B200 수요 폭증 |
| 단기 (2025 H2) | CoWoS | 92% | TSMC CoWoS 캐파 80K wpm로 확대 예정 |
| 중기 (2026) | Power/Grid | 78%→90%+ | 데이터센터 전력 수요 2배 증가 |
| 장기 (2027) | Networking | 65%→85% | GB200 클러스터 확산으로 IB 수요 급증 |
| 출처 | URL | 설명 |
| --- | --- | --- |
| SK Hynix HBM | https://news.skhynix.com/hbm/ | HBM3e 생산 현황 및 공급 계획 |
| TSMC CoWoS | https://ir.tsmc.com/english/annualReports | CoWoS 패키징 캐파 확대 계획 |
| HBM 시장 규모 | https://www.precedenceresearch.com/high-bandwidth-memory-market | HBM 시장 $35B(2025E) → $55B(2026E) |
| 회사 | 2022 | 2023 | 2024 | 2025 | 2026E |
| --- | --- | --- | --- | --- | --- |
| Microsoft | $22B | $28B | $55B | $80B | - |
| Google | $25B | $32B | $52B | $75B | - |
| Amazon | $38B | $48B | $75B | $105B | - |
| Meta | $31B | $28B | $37B | $65B | - |
| xAI | - | - | $6B | $15B | - |
| 출처 | URL | 설명 |
| --- | --- | --- |
| Microsoft 실적발표 | https://www.microsoft.com/en-us/investor/earnings/fy-2025-fourth-quarter/press-release | 분기 CapEx 공시 |
| Google 실적발표 | https://abc.xyz/investor/ | 알파벳 IR 자료 |
| Amazon 실적발표 | https://ir.aboutamazon.com/ | AWS CapEx 공시 |
| Meta 실적발표 | https://investor.fb.com/ | Meta AI 투자 공시 |
| 투자자 | 피투자사 | 유형 | 설명 | 규모 |
| --- | --- | --- | --- | --- |
| NVIDIA | OpenAI | investment | NVIDIA, OpenAI에 최대 $1,000억 투자 합의 | $100B |
| NVIDIA | Nscale | investment | NVIDIA Nscale 투자 참여 | 미공개 |
| NVIDIA | Nebius | investment | NVIDIA Nebius 투자 참여 | 미공개 |
| Microsoft | OpenAI | investment | OpenAI 누적 투자 $130억+, Azure 독점 공급 | $13B+ |
| Microsoft | Mistral | investment | Mistral AI 투자 + Azure 파트너십 | $16M |
| Microsoft | Nebius | investment | Nebius AI 클라우드 투자 | 미공개 |
| OpenAI | Figure AI | vc | 피지컬 AI 로봇 스타트업 투자 | $675M |
| OpenAI | Anysphere | vc | Cursor IDE (AI 코딩) 투자 | 미공개 |
| OpenAI | Harvey AI | vc | 리걸 AI 스타트업 투자 | 미공개 |
| Google | Anthropic | investment | Google, Anthropic 최대 $20억 투자 | $2B |
| Amazon | Anthropic | investment | Amazon, Anthropic 최대 $40억 투자 | $4B |
| 공급사 | 수요사 | 공급 내용 | 구조 |
| --- | --- | --- | --- |
| SK Hynix | NVIDIA | HBM3e 50%+ 독점 공급, H200/B200 전용 | 독점 |
| TSMC | NVIDIA | 4nm CoWoS 패키징 + 칩 제조 (독점) | 독점 |
| NVIDIA | Microsoft | H100/B200 대량 공급 (데이터센터 매출 $150B/yr) | 경쟁 |
| NVIDIA | AWS | AWS GPU 인스턴스 핵심 공급 | 경쟁 |
| NVIDIA | Google | GCP GPU 클러스터 공급 | 경쟁 |
| NVIDIA | xAI | Colossus 클러스터 10만개+ GPU 공급 | 경쟁 |
| NVIDIA | Oracle | Oracle Cloud GPU 공급 | 경쟁 |
| NVIDIA | CoreWeave | GPU 클라우드 핵심 인프라 공급 | 경쟁 |
| AMD | OpenAI | AMD GPU 6GW 배포 합의, 주식 옵션 1.6억주 | 경쟁 |
| AMD | Microsoft | Azure MI300X 공급 | 경쟁 |
| Oracle | NVIDIA | Oracle, 수십억달러 규모 NVIDIA 칩 구매 | 경쟁 |
| Meta | NVIDIA | H100/B200 대규모 구매 ($65B CapEx의 핵심) | 경쟁 |
| 출처 | URL | 설명 |
| --- | --- | --- |
| NVIDIA-OpenAI 투자 | https://www.bloomberg.com/news/articles/2025-01-23/nvidia-agrees-to-invest-in-openai | NVIDIA $1,000억 투자 합의 |
| Microsoft-OpenAI | https://blogs.microsoft.com/blog/2023/01/23/microsoftandopenaiextendpartnership/ | $130억+ 누적 투자 |
| Google-Anthropic | https://www.blog.google/technology/ai/google-investment-anthropic/ | $20억 투자 |
| Amazon-Anthropic | https://www.aboutamazon.com/news/aws/amazon-anthropic-ai-investment | $40억 투자 |
| 단계 | 테마 | 현황 | 수혜 기업 | 투자 포인트 |
| --- | --- | --- | --- | --- |
| Phase 1 | GPU | 진행 중 | NVIDIA, AMD | GPU 수요 폭증기, 이미 주가 반영 |
| Phase 2 | HBM & 패키징 | 현재 | SK Hynix, TSMC CoWoS | 병목 심화, 메모리 업사이클 |
| Phase 3 | 전력 인프라 | 2026~ | Vertiv, Eaton, GE Vernova | DC 전력 수요 2배 증가 |
| Phase 4 | 엣지/Physical | 2027~ | 퀄컴, 브로드컴, 로봇 기업 | AI 단말 확산 |
| 기업 | 시그널 | 근거 | 투자 기간 |
| --- | --- | --- | --- |
| SK Hynix | Strong Buy | HBM3e 50% 점유율, GB200 전용 공급, 95% 가동률 | 6-18개월 |
| TSMC | Buy | CoWoS 독점, 캐파 확대 진행 중 | 6-24개월 |
| Vertiv | Buy | DC 전력/냉각 인프라 수요 2배 증가 | 12-24개월 |
| Broadcom | Buy | 네트워킹 칩 + ASIC 공동 개발 (Google/Meta) | 12-18개월 |
| NVIDIA | Hold | 주가 선반영, GPU 독점 지속 | 장기 보유 |
| Samsung | Watch | HBM3e 인증 통과 시 점유율 확대 가능 | 인증 결과 대기 |
| AMD | Watch | MI300X 점유율 확대 중, NVIDIA 격차 축소 모니터링 | 경쟁 추이 관찰 |
| 출처 | URL | 설명 |
| --- | --- | --- |
| SK Hynix HBM | https://news.skhynix.com/hbm/ | HBM 생산 및 점유율 |
| TSMC CoWoS | https://www.tsmc.com/english/dedicatedFoundry/technology/cowos | 패키징 캐파 확대 |
| Goldman 전력 분석 | https://www.goldmansachs.com/insights/articles/AI-poised-to-drive-160-increase-in-power-demand | 전력 인프라 투자 기회 |
| 시나리오 | 가정 | 토큰 성장률 | GPU 가동률 | 공급 환경 |
| --- | --- | --- | --- | --- |
| Base | 현 성장세 유지 | 연 3배 성장 | 가동률 85% | NAND/HBM 가격 안정 |
| Bull | AI 확산 가속화 | 연 4.5배 성장 | 가동률 90% | 공급 부족 심화 |
| Bear | 성장 둔화 | 연 2배 성장 | 가동률 75% | 수요 증가 둔화 |
| 연도 | 시나리오 | 토큰/일 | GPU 수요 | HBM 수요 | 전력(MW) |
| --- | --- | --- | --- | --- | --- |
| 2025 | Base (실적) | 88.5T/day | 60만 | 48.2PB | 768MW |
| 2025 | Base (실적) | 88.5T/day | 60만 | 48.2PB | 768MW |
| 2026 | Base ★현재 | 265T/day | 180만 | 144PB | 2,304MW |
| 2026 | Bull | 398T/day | 270만 | 216PB | 3,456MW |
| 2026 | Bear | 132T/day | 89만 | 72PB | 1,152MW |
| 2027 | Base (예측) | 530T/day | 360만 | 290PB | 4,608MW |
| 2027 | Base | 354T/day | 240만 | 192.8PB | 3,072MW |
| 시나리오 | 구분 | 기업 | 근거 |
| --- | --- | --- | --- |
| Bull | 수혜 | SK Hynix, TSMC, Vertiv, NVIDIA | HBM·패키징·전력 모두 초과 수요 |
| Bull | 피해 | 공급 확보 실패 AI 서비스 기업 | 인프라 병목으로 서비스 제한 |
| Base | 수혜 | SK Hynix, TSMC CoWoS | 지속적 병목 프리미엄 |
| Bear | 수혜 | AMD, Intel Gaudi | 대체 GPU 수요 증가 |
| Bear | 피해 | NVIDIA (고점 대비), HBM 증설 기업 | 공급 과잉 위험 |
| 출처 | URL | 설명 |
| --- | --- | --- |
| Sequoia AI 인프라 | https://www.sequoiacap.com/article/ais-600b-question/ | AI $600B 인프라 투자 분석 |
| IEA 전력 전망 | https://www.iea.org/reports/electricity-2024 | 2024-2026 DC 전력 수요 |
| IDC GPU 시장 | https://www.idc.com/getdoc.jsp?containerId=prUS52540424 | GPU 시장 출하량 예측 |