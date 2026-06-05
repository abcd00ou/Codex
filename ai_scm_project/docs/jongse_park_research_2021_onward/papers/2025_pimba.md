# Pimba: A Processing-in-Memory Acceleration for Post-Transformer Large Language Model Serving

## Source and Scope

Venue: MICRO 2025  
Source: https://jongse-park.github.io/files/paper/2025-micro-pimba.pdf  
Copyright note: This note is a paraphrased research reading, not a reproduction of the original paper.

## Detailed English Reading

Pimba studies serving for post-transformer LLMs such as state-space models, linear attention, and recurrent architectures. The paper’s key framing is that the transformer is not the final form of LLM architecture. As context length grows, researchers are exploring alternatives with different state and attention behavior. Yet the paper finds that these alternatives can still be memory-bandwidth-bound under batched inference.

The proposed direction combines Processing-in-Memory with LLM quantization, especially MX-style low-precision arithmetic. The design introduces state-update processing units that can handle state update and attention-like operations efficiently. This matters because post-transformer models reduce or reshape the KV cache problem, but they do not eliminate data movement and memory pressure.

The broader message is that future LLM hardware must be architecture-aware but not transformer-locked. Serving systems need to support both current transformer models and emerging post-transformer models in a unified or at least adaptable way.

## 상세 한글 독해 및 번역 요약

Pimba는 post-transformer LLM serving을 다룬다. 여기서 post-transformer는 SSM, linear attention, RNN 계열처럼 기존 transformer attention 구조를 대체하거나 보완하려는 모델을 의미한다. 중요한 점은 이런 모델이 KV cache 문제를 완전히 없애는 것이 아니라, state update라는 다른 형태의 memory-bound 연산을 만든다는 점이다.

논문은 PIM과 quantization을 결합한다. PIM은 memory 근처에서 연산을 수행해 data movement를 줄이는 방향이고, MX quantization은 낮은 precision으로 memory footprint와 arithmetic cost를 줄이는 방향이다. Pimba는 두 방향을 함께 써서 transformer와 post-transformer를 모두 지원하려는 accelerator 설계를 제시한다.

이 논문은 2026-2030 AI capacity forecast에서 중요한 의미가 있다. 미래 모델이 transformer에서 벗어나더라도 memory bandwidth 병목은 계속 남을 가능성이 크다. 단지 병목의 형태가 attention/KV cache에서 state update로 바뀔 수 있다.

## 박종세 교수 전문성 관점

박 교수님은 모델 구조 변화와 accelerator design을 함께 보는 연구자다. transformer 이후 workload까지 연구 범위를 확장하고 있다.

## 내 프로젝트와의 연결점

GPU/HBM/ASIC mix를 transformer-only 가정으로 두면 장기 forecast가 약하다. Pimba는 post-transformer adoption scenario, PIM relevance, MX precision adoption을 모델에 넣을 근거가 된다.
