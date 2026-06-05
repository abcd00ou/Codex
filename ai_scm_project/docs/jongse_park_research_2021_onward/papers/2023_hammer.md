# HAMMER: Hardware-friendly Approximate Computing for Self-attention with Mean-redistribution and Linearization

## Original English Notes

Venue: IEEE Computer Architecture Letters, 2023  
Source: https://jongse-park.github.io/publications/

HAMMER proposes hardware-friendly approximate computing for self-attention using mean redistribution and linearization.

## 한글 번역 요약

HAMMER는 self-attention을 hardware-friendly하게 근사해 계산 비용을 줄이는 연구다. attention은 LLM inference의 핵심 병목이므로, 정확도와 효율 사이의 trade-off가 중요하다.

## 박종세 교수 전문성 관점

박 교수님은 transformer attention 자체를 algorithm-hardware co-design 관점에서 줄이는 연구도 수행한다.

## 내 프로젝트 연결점

long-context inference의 bottleneck은 attention과 KV cache다. attention approximation이 실제 상용 품질을 유지할 수 있다면 tokens/sec/MW upside가 생길 수 있지만, quality risk와 adoption uncertainty를 분리해야 한다.

