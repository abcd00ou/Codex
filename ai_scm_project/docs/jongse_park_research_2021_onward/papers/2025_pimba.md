# Pimba: A Processing-in-Memory Acceleration for Post-Transformer Large Language Model Serving

## Original English Notes

Venue: MICRO 2025  
Source: https://jongse-park.github.io/files/paper/2025-micro-pimba.pdf

Pimba studies post-transformer LLM serving, including state-space models, linear attention, and recurrent models. It observes that both transformer and post-transformer batched inference can be memory-bandwidth-bound. The proposed design combines Processing-in-Memory and MX-based quantization, with state-update processing units shared across banks.

## 한글 번역 요약

Pimba는 transformer 이후의 LLM 구조, 예를 들어 SSM, linear attention, RNN 계열 모델을 serving할 때의 병목을 다룬다. 핵심은 transformer attention뿐 아니라 post-transformer state update도 memory bandwidth 병목을 만든다는 점이다. PIM과 MX quantization을 결합해 generation throughput을 높이는 방향을 제시한다.

## 박종세 교수 전문성 관점

박 교수님은 현재 transformer LLM뿐 아니라 이후 모델 구조 변화까지 고려해 accelerator와 memory system을 설계하는 전문가다.

## 내 프로젝트 연결점

2026-2030 capacity model이 transformer-only 가정에 묶이면 위험하다. Mamba/linear attention 계열이 확산되면 KV cache 압력은 바뀔 수 있지만 memory bandwidth와 state update 병목은 남을 수 있다. GPU/ASIC/HBM 가정에 model architecture sensitivity가 필요하다.

