<!-- converted from study_cowos_packaging_lv2_20260326.docx -->


[Lv.2 심화] CoWoS & 첨단 패키징 심층 분석
Advanced Packaging — 패키징이 AI 공급망의 병목이 된 이유
대상: 반도체 마케팅 종사자  |  기준일: 2026-03-24  |  난이도: 기술 기초 → 중급
본 문서는 CoWoS(Chip-on-Wafer-on-Substrate) 및 첨단 패키징 기술을 반도체 마케팅 관점에서 이해하기 위한 심층 학습 자료입니다. TSMC 독점 구조, 공급 병목, 수혜 기업 분석, 투자 시사점을 비즈니스 언어로 풀어 설명합니다.

# 1장. 왜 패키징이 병목인가
2023년부터 AI 반도체 공급망에서 가장 많이 언급되는 단어 중 하나가 'CoWoS 부족'입니다. GPU를 만드는 TSMC는 최첨단 파운드리인데, 왜 갑자기 '패키징'이 병목이 되었을까요? 답을 이해하려면 반도체 칩이 어떤 한계에 부딪혔는지부터 알아야 합니다.
## 1.1 무어의 법칙 한계와 'More than Moore'
[개념] 무어의 법칙(Moore's Law): 인텔 공동창업자 고든 무어가 1965년 제안. '트랜지스터 집적도가 2년마다 2배 증가한다.' 이 법칙이 2016년 이후 사실상 정체됨 — 물리적 한계(원자 크기)에 도달했기 때문.
[개념] More than Moore: 칩 하나를 더 미세하게 만드는 대신, 여러 칩을 하나의 패키지에 효율적으로 통합해 성능을 높이는 전략. 칩렛(Chiplet) 아키텍처, 2.5D/3D 패키징이 이 흐름의 핵심.
[마케터 관점] 마케터 비유: 무어의 법칙 = '아파트 층수 높이기'. 이제 한계. More than Moore = '같은 땅에 여러 건물을 연결 통로로 묶기'. CoWoS는 이 '연결 통로'를 만드는 기술입니다.
## 1.2 칩 면적 한계와 칩렛 아키텍처
단일 칩 크기에는 물리적 한계(레티클 한계, ~858mm²)가 있습니다. H100 GPU = 814mm², B200 GPU = 1개 다이로는 불가 → 2개 다이 연결. 이처럼 여러 다이를 하나의 패키지로 묶는 것이 칩렛 전략이며, 이를 구현하는 핵심 기술이 CoWoS입니다.

[마케터 관점] 마케팅 시사점: 칩이 발전할수록 패키징 기술 의존도가 높아집니다. 즉 TSMC의 CoWoS 없이는 NVIDIA의 차세대 GPU가 나올 수 없는 구조. 패키징 = AI 공급망의 숨은 지배자.
### 참고자료


# 2장. 2.5D/3D 패키징 기술 원리
첨단 패키징은 크게 2.5D와 3D로 나뉩니다. 이 차이를 이해하면 CoWoS가 왜 특별한지, 삼성·인텔이 왜 TSMC를 따라잡기 어려운지 명확해집니다.
## 2.1 인터포저(Interposer)란?
[개념] 인터포저(Interposer): GPU 다이와 HBM 스택을 연결하는 '중간 기판'. 실리콘 또는 유리/유기물로 만들며, 수천 개의 미세 배선이 내장되어 있음. 마치 USB 허브처럼, 여러 칩을 하나의 고속 연결망으로 묶어주는 역할.
[개념] 2.5D 패키징: GPU와 HBM을 인터포저 위에 '수평으로' 나란히 배치. 칩들이 물리적으로 가까워 신호 손실이 극소화됨. CoWoS가 대표적 2.5D 기술. (숫자 '2.5'는 완전한 3D 적층은 아니지만, 2D 보드보다 진보했다는 의미)
[개념] 3D 패키징(SoIC): 칩을 수직으로 직접 적층. TSMC의 SoIC(System-on-Integrated-Chips) 기술. HBM 자체가 이미 DRAM 다이를 수직 적층한 3D 구조. SoIC-R(레이어드), SoIC-P(플레이스드) 두 종류.

## 2.2 TSV와 마이크로 범프
[개념] TSV(Through-Silicon Via, 관통 실리콘 비아): 실리콘 칩을 수직으로 뚫는 미세 전도성 구멍(지름 5-10μm). HBM 내부 DRAM 다이들을 수직으로 연결하는 핵심 기술. 만들기 매우 어렵고 비쌈 → 진입장벽의 원천.
[개념] 마이크로 범프(Micro Bump): 인터포저 위에서 GPU와 HBM을 연결하는 미세 솔더 볼. H100의 경우 GPU-인터포저 간 10만 개 이상의 범프가 연결됨. 범프 피치(간격)가 좁을수록 더 많은 신호선 → 더 높은 대역폭.
[마케터 관점] 기술 어려움이 곧 비즈니스 가격 결정력: CoWoS 패키징 비용은 H100 기준 ~$1,000~1,500/장. 웨이퍼 제조비 대비 10-15% 수준이지만, 이 공정 없이는 GPU 출하 불가. TSMC는 이 독점 위치를 이용해 2024년 CoWoS 단가 20%+ 인상.
### 참고자료


# 3장. CoWoS 독점 구조 — TSMC만 가능한 이유
반도체 패키징 시장에는 ASE, Amkor, SPIL 같은 OSAT(외주 반도체 후공정) 기업들이 있습니다. 그런데 왜 NVIDIA는 반드시 TSMC에서 CoWoS를 해야 할까요? 이 독점 구조를 이해하는 것이 투자 분석의 핵심입니다.
## 3.1 OSAT vs TSMC — 무엇이 다른가
[개념] OSAT(Outsourced Semiconductor Assembly and Test): 반도체 칩 조립·테스트 전문 기업 (ASE, Amkor, SPIL 등). 일반 패키징(와이어 본딩, 플립칩)은 가능하나, CoWoS처럼 실리콘 인터포저 제작 + 첨단 공정 통합은 불가.
[개념] TSMC가 CoWoS를 독점하는 이유: ① 실리콘 인터포저 자체가 파운드리 공정(미세 배선 리소그래피)으로 제작됨 — TSMC만 보유. ② GPU 웨이퍼와 인터포저를 같은 팹에서 연속 공정으로 처리 가능 (CoW = Chip-on-Wafer 단계). ③ SoIC 기술은 TSMC 독자 R&D 결과 (삼성 X-Cube, 인텔 Foveros와 유사하나 양산 선행).

## 3.2 CoWoS-S / CoWoS-L / CoWoS-R 차이
TSMC CoWoS는 용도와 인터포저 소재에 따라 세 가지 변형이 있습니다. 이 차이를 알아야 고객사별 적용 현황과 미래 로드맵을 이해할 수 있습니다.

[마케터 관점] 투자 포인트: CoWoS-L로의 전환 = 단가 하락 없이 면적 확대. TSMC는 동일한 CoWoS 캐파(wpm)로 더 큰 패키지를 처리하게 되어 캐파 부족이 더 심화됩니다. 2024-2025년 CoWoS-L 전환 가속이 '갭 악화' 요인.
### 참고자료


# 4장. 공급 현황 & 병목 데이터
CoWoS 공급 부족이 얼마나 심각한지 수치로 확인합니다. 데이터를 보면 왜 TSMC가 2027년까지 강력한 가격 결정력을 유지하는지 이해됩니다.
## 4.1 TSMC CoWoS 캐파 확대 이력 (2023-2026)

[계산 예제] CoWoS-S → CoWoS-L 전환 시 캐파 희석 효과 계산:
  CoWoS-S: 1 웨이퍼당 GPU 1.5~2개 (작은 패키지)
  CoWoS-L: 1 웨이퍼당 GPU 0.7~1개 (큰 패키지, B200 기준)
  → 동일한 wpm 대비 실질 GPU 생산량 약 30-50% 감소
  '캐파가 늘어도 GPU 공급이 안 늘어보이는' 이유
## 4.2 18개월 리드타임의 의미
[개념] CoWoS 캐파 증설 리드타임: 투자 결정 → 장비 발주 → 설치·검증 → 양산까지 약 18개월. TSMC가 2024년 1월에 투자를 결정하면 빨라야 2025년 중반에 캐파 반영. 이 구조적 지연이 '공급 부족의 지속성'을 보장합니다.
[주의] 리스크: 수요가 예상보다 빨리 둔화될 경우, 18개월 후 완공되는 캐파가 과잉이 될 수 있음. 2026년 이후 CoWoS 캐파 과잉 전환 여부가 핵심 모니터링 포인트.

[마케터 관점] TSMC 전체 매출(2024 $90B+) 대비 CoWoS는 아직 ~4-5% 수준. 그러나 성장률이 전사 평균(15%)의 3-4배. '작지만 빠른 성장 엔진' → TSMC 밸류에이션 리레이팅 요인.
### 참고자료


# 5장. 경쟁 구도 — 삼성·인텔·TSMC 비교
TSMC의 CoWoS 독점이 영원할까요? 삼성과 인텔도 유사 기술을 개발 중입니다. 경쟁 기술의 현황과 한계를 정확히 파악해야 TSMC의 해자(Moat)가 얼마나 지속될지 판단할 수 있습니다.

## 5.1 삼성 FOPLP의 한계
[개념] FOPLP(Fan-Out Panel Level Packaging): 사각형 패널(유리/플라스틱) 위에 칩을 배치. 비용이 낮고 대형 패널 활용 가능. 단, 실리콘 인터포저 대비 신호 밀도 낮음. NVIDIA H100/B200 수준의 고속 인터페이스(수천 GB/s) 구현 어려움.
[마케터 관점] TSMC 독점의 핵심: NVIDIA GPU처럼 극도로 높은 대역폭(~수 TB/s)이 필요한 제품은 실리콘 인터포저가 필수. 삼성 FOPLP는 저비용 시장(웨어러블, IoT)에는 적합하나 AI GPU 시장에서 TSMC를 대체하기 어려움. 2026-2027년까지 현 구도 유지 전망.
## 5.2 인텔 EMIB의 위치
[개념] EMIB(Embedded Multi-die Interconnect Bridge): 기판 내부에 소형 실리콘 브릿지를 삽입. CoWoS-S처럼 전체 실리콘 인터포저를 사용하지 않아 비용 절감. 인텔 Gaudi 3 AI 가속기, Meteor Lake CPU에 적용. 단, 독립 파운드리 서비스로 NVIDIA 같은 고객에 제공하기엔 수율·신뢰성 과제 존재.
### 참고자료


# 6장. 수혜 기업 분석
CoWoS 공급망은 TSMC만의 이야기가 아닙니다. 기판, 소재, 장비, 조립 등 수십 개 기업이 연계되어 있습니다. 각 레이어의 수혜 기업과 투자 포인트를 정리합니다.
## 6.1 직접 수혜 기업 — 패키징 서비스

## 6.2 소재 & 기판 — 국내 수혜 기업

[마케터 관점] 국내 소재 기업 투자 포인트: 심텍과 이녹스첨단소재는 CoWoS 기판·소재의 국내 최대 공급사입니다. TSMC CoWoS 캐파 확장이 직접 수주 증가로 이어지는 구조. 단, TSMC 공급사 승인(Qualification) 여부 확인이 필수.
### 참고자료


# 7장. 투자 시사점 — 캐파 확장 vs 수요 갭 분석
CoWoS 투자 분석의 핵심은 단 하나: '수요가 공급을 얼마나, 얼마나 오래 초과하는가?' 이 갭이 클수록 TSMC와 공급망의 수익성이 높습니다.
## 7.1 수요-공급 갭 정량 분석 (2025-2027)

[계산 예제] CoWoS 갭이 TSMC 매출에 미치는 영향 계산:
  2025 부족분 45K wpm × $1,200/장(CoWoS 단가) × 12개월
  = 45,000 × $1,200 × 12 = $648M 미충족 수요 (TSMC 기준)
  → 실제로는 수요 초과분만큼 TSMC가 단가를 올릴 여력 발생
  2024년 실제 CoWoS 단가 인상: ~20% (보도 기준)
## 7.2 투자 타임라인 — 매수·매도 시그널

[마케터 관점] 마케터의 강점 활용: 반도체 마케팅 담당자는 고객사 구매 동향을 가장 빨리 캐치합니다. CoWoS 리드타임 변화(단축/연장)는 TSMC 공급-수요 균형의 선행지표입니다. 현장 정보 → 투자 판단으로 연결하는 훈련을 해보세요.
### 참고자료


# 심화 분석
이 섹션은 Level 2 심화 과정으로, CoWoS-L vs CoWoS-R 구조적 차이 상세 분석과 TSMC 수율 개선에 따른 경제성 분석을 다룹니다.
## CoWoS-L vs CoWoS-R 구조적 차이 상세
CoWoS-L(Large)과 CoWoS-R(RDL)은 모두 대면적 패키징을 지원하지만, 인터포저 소재와 제조 방식에서 근본적으로 다릅니다.

CoWoS-L의 핵심: TSMC SoIC 브릿지칩이 GPU와 HBM 사이 고대역폭 연결 담당. 실리콘 브릿지는 마이크로범프 밀도를 높여 HBM I/O 2048-bit 구현. CoWoS-R의 장점: RDL 기반으로 포토리소 공정만으로 제작 → 원가 경쟁력. 단점: 실리콘 브릿지 없어 연결 밀도 한계 → 차세대 HBM 인터페이스 적용 시 도전.
## TSMC 수율 개선 경제성 분석
CoWoS 수율은 패키징 비용 구조의 핵심입니다. 수율 1% 개선이 TSMC 영업이익에 미치는 영향을 계산합니다.

수율 1% 개선의 가치 계산: 연간 생산량 100K wpm × 25장/m² 기준 = 2.5M 기판/년. 수율 1% 개선 → 25,000개 추가 양품 → $9,000 × 25,000 = $225M 추가 매출 효과. TSMC CoWoS 사업부 영업이익률 40-45% 가정 → 수율 1% = $90-100M 이익 증가. 투자 시사점: TSMC의 CoWoS 수율 공시는 없으나, 기판 단가 변화 추적으로 간접 추정 가능.
# 8장. 복습 문제 — 능동적 학습
페인만 기법: 아래 질문에 '상대방에게 설명하듯' 답할 수 있으면 이해한 것입니다. 막히는 부분이 있으면 해당 장으로 돌아가서 다시 읽으세요.
## 복습 문제 (능동적 학습)
아래 질문에 먼저 스스로 답해보고, 힌트를 확인하세요. 답을 '설명할 수 있으면' 이해한 것입니다 (페인만 기법).
Q1. 무어의 법칙이 한계에 달한 상황에서 반도체 성능을 높이는 두 가지 방향은 무엇이고, CoWoS는 그 중 어느 방향에 해당하는지 설명하세요.
힌트: 1장 참고. 'More than Moore' 개념과 칩렛 아키텍처를 활용하세요.
유형: 개념 이해 (기술 방향성)

Q2. CoWoS-S, CoWoS-L, CoWoS-R의 차이를 인터포저 소재와 적용 제품 기준으로 설명하고, B200가 CoWoS-L을 사용하는 이유를 면적 관점에서 설명하세요.
힌트: 3장 참고. 레티클 한계(858mm²)와 B200 다이 크기를 연결해 보세요.
유형: 기술 심화 (제품 적용)

Q3. TSMC가 CoWoS를 독점하는 이유를 OSAT와의 기술적 차이 관점에서 3가지로 설명하세요.
힌트: 3장 참고. 실리콘 인터포저 제작, CoW 공정, SoIC 기술을 중심으로.
유형: 경쟁 분석 (진입장벽)

Q4. 2025년 CoWoS 수요를 85K wpm 공급으로 충족하지 못하는 상황에서 TSMC의 CoWoS 단가 협상력이 왜 강한지 경제학 원리로 설명하세요.
힌트: 4장 참고. 수요-공급 갭, 리드타임, 대체재 부재 3요소를 사용하세요.
유형: 비즈니스 분석 (가격 결정력)

Q5. 심텍(Simmtech)이 CoWoS 공급망에서 어떤 역할을 하며, CoWoS 캐파 확장이 심텍 매출에 어떻게 연결되는지 공급망 흐름으로 설명하세요.
힌트: 6장 참고. TSMC CoWoS 캐파 → 기판 수요 → 심텍 수주 흐름을 추적하세요.
유형: 공급망 분석 (수혜 연결)

Q6. 2027년 CoWoS 수요-공급이 균형에 도달할 경우, TSMC·심텍·이녹스첨단소재 각각에 어떤 영향이 있을지 강도와 타이밍 차이를 구분해 분석하세요.
힌트: 7장 참고. 가격 결정력 변화, 수주 잔고, 선행/후행 영향을 고려하세요.
유형: 투자 분석 (시나리오 사고)

## 정답 가이드 (핵심 포인트)
[Q1 핵심] ① 계속 미세화: 3nm → 2nm (More Moore). ② 여러 칩 통합: 칩렛 + 첨단 패키징 (More than Moore). CoWoS = ②에 해당. 여러 다이를 하나의 패키지로 통합해 성능 향상.
[Q2 핵심] CoWoS-S: 실리콘 인터포저, 고밀도 (H100). CoWoS-L: 유기물+브릿지, 면적 2-4배 (B200). CoWoS-R: RDL 기반, 가장 넓은 면적 (Rubin). B200 이유: 단일 다이로 레티클 한계 초과 → 대면적 패키징 필요.
[Q3 핵심] ① 실리콘 인터포저 자체가 파운드리 공정 → OSAT 불가. ② CoW(칩-온-웨이퍼) 단계에서 웨이퍼 상태로 처리 → 팹 내 통합 필수. ③ SoIC 3D 기술은 TSMC 독자 개발 → 특허·Know-how 장벽.
[Q4 핵심] 수요 > 공급 (45K wpm 갭) + 리드타임 18개월 (단기 증설 불가) + 대체재 없음 (삼성 FOPLP 불가) = 완전 독점적 공급자 지위. 경제학: 공급 비탄력적 + 수요 탄력성 낮음 → 가격 인상 전가 가능.
[Q5 핵심] TSMC CoWoS 캐파 확장 결정 → 기판(Substrate) 주문 발주 → 심텍 수주 증가. CoWoS 기판 단가 = 일반 PKG 기판 대비 3-5배. 심텍은 TSMC의 공급사 승인(Qual)을 보유 중 → 직접 수혜 구조.
[Q6 핵심] TSMC: 즉시 영향. 단가 인상 불가 → 매출 증가율 둔화. 심텍: 1-2분기 후 영향. TSMC 신규 주문 감소 → 매출 타격. 이녹스: 6개월 이상 후행. 완성품 생산 감소 → 소재 수요 감소. 타이밍: TSMC > 심텍 > 이녹스 순으로 영향 도달.

# 종합 참고문헌

| 제품 | 다이 구성 | 패키징 방식 | 메모리 |
| --- | --- | --- | --- |
| H100 (2022) | 단일 다이 814mm² | CoWoS-S (단일 GPU + HBM 4~6개) | 80GB HBM3 |
| H200 (2024) | 단일 다이 814mm² | CoWoS-S (HBM3e 6개) | 141GB HBM3e |
| B200 (2024) | 단일 다이 <814mm² | CoWoS-L (면적 확대) | 192GB HBM3e |
| GB200 NVL72 | GPU 72개 + NVSwitch | 랙 레벨 CoWoS 통합 | 1랙 1MW |
| Rubin (2026E) | 2개 다이 칩렛 | CoWoS-R (RDL 기반) | HBM4 탑재 예정 |
| 출처 | URL | 설명 | 연도 |
| --- | --- | --- | --- |
| TSMC — CoWoS Technology Overview | https://pr.tsmc.com/english/news/3141 | CoWoS-S / CoWoS-L / CoWoS-R 구조 차이, 인터포저 소재, 적용 제품 정보 | 2024 |
| NVIDIA GB200 NVL72 Product Brief | https://www.nvidia.com/en-us/data-center/gb200-nvl72/ | GB200 NVL72 랙 구성: GPU 72개 + NVSwitch + CoWoS, 1MW 전력 소비 | 2024 |
| Yole Développement — Advanced Packaging 2024 | https://www.yolegroup.com/product/report/advanced-packaging-2024/ | 2.5D/3D 패키징 시장 규모, 기술별 점유율, 2028년까지 성장 전망 | 2024 |
| 기술 | 구조 | 비용 | 특징 | 적용 사례 |
| --- | --- | --- | --- | --- |
| 2D 패키징
(기존 방식) | PCB 기판 위에 칩 배치 | 저비용 | 신호 경로 길어 저속 | 일반 CPU/DRAM |
| 2.5D (CoWoS) | 실리콘 인터포저 위 수평 배치 | 중간 | 고속(~수 TB/s), 저전력 | H100, B200, AMD MI300X |
| 3D (SoIC-R/P) | 칩 위에 칩 직접 적층 | 고비용 | 초고밀도, 최단 신호 경로 | HBM 내부, 미래 GPU |
| 하이브리드
(CoWoS+SoIC) | 2.5D 인터포저 + 3D 적층 혼합 | 최고 | 최고 성능·밀도 | Rubin, 2027E~ |
| 출처 | URL | 설명 | 연도 |
| --- | --- | --- | --- |
| IEEE ECTC — CoWoS Technology Papers (2022-2024) | https://ectc.net/ | CoWoS 공정 세부 구조, TSV, RDL 인터포저 기술 논문 모음 | 2022-2024 |
| TechInsights — CoWoS Die Analysis | https://www.techinsights.com/blog/cowos-advanced-packaging-analysis | H100 패키지 분해 분석: CoWoS-S 구조, 인터포저 면적, HBM 배치 실측 데이터 | 2024 |
| SemiAnalysis — CoWoS Deep Dive | https://www.semianalysis.com/p/cowos-deep-dive | TSMC CoWoS 독점 구조, OSAT 대비 기술 장벽, 수요-공급 갭 정량 분석 | 2024 |
| 항목 | TSMC CoWoS | OSAT (ASE/Amkor 등) |
| --- | --- | --- |
| 실리콘 인터포저 제작 | ○ (자사 파운드리 활용) | ✕ (파운드리 설비 없음) |
| CoW (칩-온-웨이퍼) 공정 | ○ 독점 | ✕ 불가 |
| SoIC 3D 적층 | ○ SoIC-R, SoIC-P | ✕ 또는 초기 단계 |
| 일반 플립칩 패키징 | ○ 가능 | ○ 주력 사업 |
| 2.5D 유기물 기판 패키징 | 제한적 | ○ (삼성 FOPLP 등) |
| 주요 고객 | NVIDIA, AMD, Apple | 퀄컴, TI, 브로드컴 |
| CoWoS 단가(H100 기준) | ~$1,000-1,500/장 | 해당 없음 |
| 종류 | 인터포저 소재 | 주요 적용 제품 | 특징 | 상용화 현황 |
| --- | --- | --- | --- | --- |
| CoWoS-S
(Silicon) | 실리콘 인터포저
(가장 고밀도) | H100, H200, MI300X | 최고 성능·고비용
단일 GPU+HBM 연결 | 현재 주력 |
| CoWoS-L
(Local bridge + Organic) | 유기물 기판 + 실리콘 브릿지
(면적 확장 가능) | B200, 대면적 AI 칩 | CoWoS-S보다 면적 2~4배
비용 약 20-30% 절감 | 2024~2025 성장 |
| CoWoS-R
(RDL = Redistribution Layer) | RDL(재배선층) 기반 인터포저
(유연한 설계) | Rubin (2026E+), 차세대 GPU | 최대 면적, 복잡한 칩렛
연결에 최적화 | 2026~ 도입 예정 |
| 출처 | URL | 설명 | 연도 |
| --- | --- | --- | --- |
| TSMC Annual Report 2024 | https://investor.tsmc.com/english/annual-reports | CoWoS 매출 기여, 첨단 패키징 사업부 성장, 캐파 투자 계획 공시 | 2024 |
| TSMC — CoWoS Technology Overview | https://pr.tsmc.com/english/news/3141 | CoWoS-S / CoWoS-L / CoWoS-R 구조 차이, 인터포저 소재, 적용 제품 정보 | 2024 |
| SemiAnalysis — CoWoS Deep Dive | https://www.semianalysis.com/p/cowos-deep-dive | TSMC CoWoS 독점 구조, OSAT 대비 기술 장벽, 수요-공급 갭 정량 분석 | 2024 |
| 연도 | 월 캐파(WPM) | GPU 패키징 가능 추정 | 시장 상황 |
| --- | --- | --- | --- |
| 2023 | ~35,000 wpm | GPU H100 기준 ~50만 개/년 | 수요 대비 심각 부족
NVIDIA H100 리드타임 52주 |
| 2024 | ~50,000 wpm | GPU H100/H200 기준 ~80만 개/년 | 부족 지속
B200 전환으로 실질 캐파 더 타이트 |
| 2025 | ~85,000 wpm | GPU B200 기준 ~120만 개/년 추정 | 증설 가속
여전히 수요 > 공급 |
| 2026E | ~120,000 wpm | GPU ~200만 개/년 추정 | 목표치
달성 여부 불확실 |
| 연도 | TSMC CoWoS 추정 매출 | 비고 |
| --- | --- | --- |
| 2023 | ~$2B | 전체 매출 3.7% 수준, 빠른 성장 초기 |
| 2024 | ~$4B | YoY +100%, 첨단 패키징이 핵심 성장 엔진 |
| 2025E | ~$6B | YoY +50%, CoWoS-L 비중 확대 |
| 2026E | ~$10B | YoY +67%, Rubin 전환 효과 반영 시 |
| 출처 | URL | 설명 | 연도 |
| --- | --- | --- | --- |
| TSMC Annual Report 2024 | https://investor.tsmc.com/english/annual-reports | CoWoS 매출 기여, 첨단 패키징 사업부 성장, 캐파 투자 계획 공시 | 2024 |
| Morgan Stanley — CoWoS Capacity Report 2024 | https://www.morganstanley.com/ideas/ai-semiconductor-advanced-packaging | CoWoS 캐파 확대 일정, 2025-2026 수요-공급 갭 추정, 가격 전망 | 2024 |
| SemiAnalysis — CoWoS Deep Dive | https://www.semianalysis.com/p/cowos-deep-dive | TSMC CoWoS 독점 구조, OSAT 대비 기술 장벽, 수요-공급 갭 정량 분석 | 2024 |
| 기술 | 인터포저 방식 | 기술 성숙도 | 주요 고객/제품 | 현황 |
| --- | --- | --- | --- | --- |
| TSMC CoWoS
(CoWoS-S/L/R) | 실리콘 인터포저
(CoWoS-S) | ★★★★★ | H100/H200/B200
Rubin(예정) | 양산 1위
리드타임 18개월 병목 |
| 삼성 FOPLP
(Fan-Out Panel Level) | 유기물 패널
(실리콘 인터포저 아님) | ★★★ | 자사 Exynos
일부 AI 칩 | TSMC 대비 기술 격차
NVIDIA 채택 없음 |
| 인텔 EMIB
(Embedded Multi-die
Interconnect Bridge) | 실리콘 브릿지
(소형 인서트 방식) | ★★★★ | Intel Ponte Vecchio
Gaudi 3 | 기술 성숙도 ↑
단 고객 제한적 |
| TSMC SoIC
(SoIC-R, SoIC-P) | 3D 직접 본딩 | ★★★★★ | HBM 내부
차세대 GPU | 최첨단 3D 기술
2.5D 이후 단계 |
| 삼성 X-Cube | 3D 적층 | ★★★ | 자사 HBM 일부 | 양산 초기
TSMC 대비 후발 |
| 출처 | URL | 설명 | 연도 |
| --- | --- | --- | --- |
| SemiAnalysis — CoWoS Deep Dive | https://www.semianalysis.com/p/cowos-deep-dive | TSMC CoWoS 독점 구조, OSAT 대비 기술 장벽, 수요-공급 갭 정량 분석 | 2024 |
| TSMC — CoWoS Technology Overview | https://pr.tsmc.com/english/news/3141 | CoWoS-S / CoWoS-L / CoWoS-R 구조 차이, 인터포저 소재, 적용 제품 정보 | 2024 |
| Yole Développement — Advanced Packaging 2024 | https://www.yolegroup.com/product/report/advanced-packaging-2024/ | 2.5D/3D 패키징 시장 규모, 기술별 점유율, 2028년까지 성장 전망 | 2024 |
| 기업 | 역할 | 매출/규모 | CoWoS 관련 포지션 | 투자 시그널 |
| --- | --- | --- | --- | --- |
| TSMC | CoWoS 독점 패키징 | 2024 CoWoS 매출 ~$4B
YoY+100% 성장 | CoWoS 점유율 ~90%
가격 결정력 최강 | ✓ 최우선 수혜 |
| ASE Technology | OSAT 1위 (일반 패키징) | 연 매출 $20B+
고급 패키징 전환 중 | CoWoS 직접 경쟁 불가
단 2.5D 주변부 수혜 | △ 간접 수혜 |
| Amkor Technology | OSAT 2위 | 연 매출 $7B
Advanced Packaging 성장 중 | Apple, Google
고급 패키징 수주 | △ 간접 수혜 |
| SPIL (日月光子公司) | ASE 자회사, OSAT | ASE 그룹 내 편입 | 범용 패키징 전문 | ○ 시장 성장 편승 |
| 기업 | CoWoS 공급망 역할 | 현황 | 수혜 논리 | 투자 매력 |
| --- | --- | --- | --- | --- |
| 심텍 (Simmtech) | CoWoS용 PKG 기판(Substrate) 공급 | 고부가 기판 비중 확대
2024 매출 ~1.2조원 | CoWoS 기판 단가 일반比 3-5배
공급 타이트 지속 | ★★★ |
| 이녹스첨단소재 | HBM/CoWoS용 접착 필름
(ABF, 언더필 소재) | 고부가 소재 매출 성장
2024 YoY +30%+ | AI 패키징 소재 수요 구조적 증가
원가 협상력 보유 | ★★★ |
| 해성디에스 | 리드프레임 및 기판 소재 | AI 서버 기판 수요 증가 수혜 | 고부가 제품 비중 확대 | ★★ |
| ISC | 반도체 테스트 소켓
(CoWoS 완성품 테스트용) | AI GPU 테스트 소켓 단가↑ | CoWoS 검사·테스트 장비 수요 | ★★ |
| 출처 | URL | 설명 | 연도 |
| --- | --- | --- | --- |
| ASE Technology Holding — FY2024 Earnings Call | https://www.aseglobal.com/en/investor-relations/ | ASE 첨단 패키징 매출 비중, CoWoS 관련 기회, OSAT 경쟁 대응 전략 | 2024 |
| Amkor Technology — FY2024 Earnings Call | https://ir.amkor.com/ | Amkor 2.5D 패키징 수주, 대형 CSP 고객 확보, 투자 계획 | 2024 |
| 심텍 — IR 자료 및 사업보고서 | https://www.simmtech.com/ir/ | CoWoS 기판(Substrate) 공급사로서 수혜, 고부가 PKG 기판 성장 계획 | 2024 |
| 이녹스첨단소재 — IR 자료 | https://www.innoxam.com/ir/ | HBM/CoWoS용 접착 소재(ABF, 언더필) 공급 현황 및 성장 전략 | 2024 |
| 연도 | TSMC CoWoS 공급(추정) | 수요(추정) | 갭 | 시장 상황 |
| --- | --- | --- | --- | --- |
| 2025 | ~85K wpm | ~130K wpm (B200/GB200 수요 급증) | ~45K wpm 부족 (공급 대비 -53%) | 심각한 부족
리드타임 30-40주 |
| 2026E | ~120K wpm | ~160K wpm (Rubin 선행 + GB200 지속) | ~40K wpm 부족 (공급 대비 -33%) | 여전히 부족
단 완화 추세 |
| 2027E | ~170K wpm (추정) | ~170-180K wpm | 균형 또는 소폭 부족 | 2027 균형점 도달 가능성
가격 압력 시작 전망 |
| 시그널 이벤트 | 투자 행동 | 근거 |
| --- | --- | --- |
| TSMC CoWoS 캐파 부족 뉴스
(고객사 AI GPU 리드타임 연장) | 매수 강화 | 공급 병목 지속 → 가격·마진 상승 |
| NVIDIA 다음 세대 GPU 발표
(Rubin, 2026E) | 매수 유지 | CoWoS-R 수요 신규 창출 → 갭 연장 |
| TSMC CoWoS 캐파 계획치 초과 달성 뉴스 | 중립 → 비중 축소 검토 | 갭 축소 시작 → 가격 결정력 약화 예고 |
| 경쟁사(삼성) AI GPU CoWoS 대체 기술 양산 뉴스 | 비중 축소 | TSMC 독점 해체 리스크 |
| AI 투자 둔화 뉴스
(빅테크 CapEx 축소) | 즉시 비중 축소 | 수요 전제 붕괴 |
| Simmtech/이녹스 TSMC Qual 획득 뉴스 | 매수 | 공급망 내 점유율 확보 → 매출 가시성 ↑ |
| 출처 | URL | 설명 | 연도 |
| --- | --- | --- | --- |
| Morgan Stanley — CoWoS Capacity Report 2024 | https://www.morganstanley.com/ideas/ai-semiconductor-advanced-packaging | CoWoS 캐파 확대 일정, 2025-2026 수요-공급 갭 추정, 가격 전망 | 2024 |
| TSMC Annual Report 2024 | https://investor.tsmc.com/english/annual-reports | CoWoS 매출 기여, 첨단 패키징 사업부 성장, 캐파 투자 계획 공시 | 2024 |
| Yole Développement — Advanced Packaging 2024 | https://www.yolegroup.com/product/report/advanced-packaging-2024/ | 2.5D/3D 패키징 시장 규모, 기술별 점유율, 2028년까지 성장 전망 | 2024 |
| 타입 | 인터포저 소재 | 최대 패키지 면적 | 주요 적용 제품 | 특징 | 기판 단가 |
| --- | --- | --- | --- | --- | --- |
| CoWoS-S | 실리콘 인터포저 | 858mm² 이하 | H100, A100 | 고밀도 배선 가능, 비용 높음 | ~$3,000-4,000/기판 |
| CoWoS-L | 실리콘 브릿지 + 유기 기판 | 레티클 한계 초과 가능 (1,800-2,500mm²) | B200, GB200 | 대면적 가능, 브릿지로 고속 연결 유지 | ~$5,000-7,000/기판 |
| CoWoS-R | RDL(재배선층) 인터포저 | 최대 4,000mm² 이상 가능 | Rubin (2026+) | 가장 넓은 면적, 실리콘 없어 비용 낮음 | ~$3,500-5,000/기판 (예상) |
| 시기 | CoWoS 수율 | 기판 원가 | 불량 손실/기판 | 유효 수익/기판 | 비고 |
| --- | --- | --- | --- | --- | --- |
| 2022 초기 | 60-65% | $10,000/기판 | $3,500-4,000 | $6,000-6,500 | 신규 도입 초기 학습 곡선 |
| 2023 | 72-75% | $9,500/기판 | $2,375-2,660 | $6,840-7,125 | 캐파 확장하며 수율 개선 |
| 2024 | 78-82% | $9,200/기판 | $1,656-2,024 | $7,176-7,544 | 양산 안정화 |
| 2025E | 83-87% | $9,000/기판 | $1,170-1,530 | $7,470-7,830 | 성숙 공정 진입 |
| 2026E | 86-90% | $8,800/기판 | $880-1,232 | $7,568-7,920 | 수율 한계 도달 |
| 출처명 | URL | 설명 | 연도 |
| --- | --- | --- | --- |
| TSMC Annual Report 2024 | https://investor.tsmc.com/english/annual-reports | CoWoS 매출 기여, 첨단 패키징 사업부 성장, 캐파 투자 계획 공시 | 2024 |
| TSMC — CoWoS Technology Overview | https://pr.tsmc.com/english/news/3141 | CoWoS-S / CoWoS-L / CoWoS-R 구조 차이, 인터포저 소재, 적용 제품 정보 | 2024 |
| Yole Développement — Advanced Packaging 2024 | https://www.yolegroup.com/product/report/advanced-packaging-2024/ | 2.5D/3D 패키징 시장 규모, 기술별 점유율, 2028년까지 성장 전망 | 2024 |
| IEEE ECTC — CoWoS Technology Papers (2022-2024) | https://ectc.net/ | CoWoS 공정 세부 구조, TSV, RDL 인터포저 기술 논문 모음 | 2022-2024 |
| SemiAnalysis — CoWoS Deep Dive | https://www.semianalysis.com/p/cowos-deep-dive | TSMC CoWoS 독점 구조, OSAT 대비 기술 장벽, 수요-공급 갭 정량 분석 | 2024 |
| Morgan Stanley — CoWoS Capacity Report 2024 | https://www.morganstanley.com/ideas/ai-semiconductor-advanced-packaging | CoWoS 캐파 확대 일정, 2025-2026 수요-공급 갭 추정, 가격 전망 | 2024 |
| ASE Technology Holding — FY2024 Earnings Call | https://www.aseglobal.com/en/investor-relations/ | ASE 첨단 패키징 매출 비중, CoWoS 관련 기회, OSAT 경쟁 대응 전략 | 2024 |
| Amkor Technology — FY2024 Earnings Call | https://ir.amkor.com/ | Amkor 2.5D 패키징 수주, 대형 CSP 고객 확보, 투자 계획 | 2024 |
| NVIDIA GB200 NVL72 Product Brief | https://www.nvidia.com/en-us/data-center/gb200-nvl72/ | GB200 NVL72 랙 구성: GPU 72개 + NVSwitch + CoWoS, 1MW 전력 소비 | 2024 |
| TechInsights — CoWoS Die Analysis | https://www.techinsights.com/blog/cowos-advanced-packaging-analysis | H100 패키지 분해 분석: CoWoS-S 구조, 인터포저 면적, HBM 배치 실측 데이터 | 2024 |
| 심텍 — IR 자료 및 사업보고서 | https://www.simmtech.com/ir/ | CoWoS 기판(Substrate) 공급사로서 수혜, 고부가 PKG 기판 성장 계획 | 2024 |
| 이녹스첨단소재 — IR 자료 | https://www.innoxam.com/ir/ | HBM/CoWoS용 접착 소재(ABF, 언더필) 공급 현황 및 성장 전략 | 2024 |