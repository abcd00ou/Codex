# 2026~2030 연간 토큰 생성 시뮬레이션용 Capacity Sensing 기준

## 중요
- 이 파일의 수치는 **공개되지 않은 계약 용량을 추정한 베이스라인 가정값**입니다.
- 실제값이 아니라 시뮬레이션 시작점이며, 분기별로 업데이트해야 합니다.

## 왜 CAGR 방식인가
- 회사별 절대 capacity는 비공개인 경우가 많아, 단일 연도 점추정보다
  `Base_2026 + CAGR`가 시나리오 비교/민감도 분석에 유리합니다.

## 기본 로직
1. `Cap_y = Cap_(y-1) * (1 + CAGR)`
2. `Tokens_y = Cap_y × Inference_Allocation × tok/s × U × D × SLO × 31,536,000`

## 현재 템플릿에서 넣어둔 sensing 가정 해석
- OpenAI/Anthropic/DeepSeek: 고성장 구간 가정(CAGR 상대적으로 높음)
- Google/Meta/Microsoft: 대형 인프라로 절대량 크지만 CAGR은 중고성장
- Alibaba/Tencent: 보수적 성장 가정
- ByteDance: 고성장 가정

## 업데이트 방법 (권장)
- 분기마다 아래 3개를 갱신:
  1) Base capacity (GPUeq)
  2) CAGR
  3) Weighted tok/s (새 HW/새 서빙스택 반영)
