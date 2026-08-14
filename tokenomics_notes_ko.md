# Tokenomics 체크 포인트 (2026~2030)

확인했습니다. 기존 capacity→tokens 시뮬레이션에 tokenomics를 결합하려면 아래 3가지를 반드시 같이 봐야 합니다.

## 1) 수익 식
- `Revenue = Annual_Tokens / 1,000,000 × Blended_Price_per_1M_tokens`

## 2) 원가 식
- `COGS = Annual_Tokens / 1,000,000 × COGS_per_1M_tokens`
- `COGS_per_1M_tokens`에는 전력, 감가상각(또는 임대료), 네트워크, 오퍼레이션 인건비 등을 포함

## 3) 마진 식
- `Gross_Margin = (Price - COGS) / Price`

## 왜 중요한가
- 토큰 생성량이 커도 `Price` 하락 속도가 `COGS` 하락보다 빠르면 수익성 악화 가능
- 반대로 서빙 효율 개선(FP8/FP4, 배치 최적화, KV cache 최적화)으로 COGS를 빠르게 낮추면 마진 방어 가능

## 이번 추가 파일
- `tokenomics_extension_2026_2030.csv`
  - 기존 `yearly_capacity_token_simulation_2026_2030.csv`의 연간 토큰을 받아
  - 가격/원가 가정을 넣어 Revenue, COGS, Gross Profit, Gross Margin 계산

## 사용 팁
1. `Blended_Price`는 Enterprise/API/Consumer 믹스로 가중 평균
2. `COGS_per_1M`은 하드웨어 세대 전환(B200/GB200 등)에 따라 연도별 하락 가정
3. Base/Bull/Bear 3개 탭으로 가격하락률과 원가하락률 민감도 비교 권장
