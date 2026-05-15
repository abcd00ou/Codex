# Source Quality Guide

source quality는 숫자보다 중요합니다. 낮은 품질의 source에서 온 숫자는 모델을 망칠 수 있습니다.

## Preferred Sources

- 회사 공식 블로그/뉴스룸
- SEC filing, annual report, earnings transcript
- cloud product documentation
- model card, GitHub official repo, technical report
- IEA, LBNL/DOE, CRS, EPRI, Uptime Institute, Epoch AI 등 기관/연구 자료
- arXiv 논문은 mechanism과 benchmark로 사용

## Warning Signs

- 날짜가 없음
- 원문 숫자가 아니라 재인용 숫자
- "reportedly", "rumored", "sources say"만 존재
- 단위가 불명확
- peak, planned, operational이 섞여 있음
- TWh/year와 GW를 구분하지 않음
- model owner와 host provider를 구분하지 않음

## Confidence Cap

| Source condition | Max confidence |
|---|---|
| 공식 source + 직접 숫자 | High |
| 공식 source + 해석 필요 | Medium |
| 논문 benchmark를 company proxy로 사용 | Medium-Low |
| 언론 보도 단독 | Low-Medium |
| anonymous/undated | Reject |
