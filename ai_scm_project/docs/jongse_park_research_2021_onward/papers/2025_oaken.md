# Oaken: Fast and Efficient LLM Serving with Online-Offline Hybrid KV Cache Quantization

## Source and Scope

Venue: ISCA 2025  
Source: https://jongse-park.github.io/files/paper/2025-isca-oaken.pdf  
Copyright note: This note is a paraphrased research reading, not a reproduction of the original paper.

## Detailed English Reading

Oaken is a key paper for understanding the memory side of LLM serving. It starts from the observation that batched serving improves throughput for operations that can share weights across requests, but attention over KV cache remains difficult because each request carries its own history. As batch size and context length grow, the KV cache consumes large memory capacity and creates heavy memory bandwidth demand during generation.

The paper focuses on KV cache quantization. Prior quantization approaches often reduce bitwidth but pay high overhead for online outlier detection or mixed-precision handling. Oaken proposes a hybrid approach: thresholds are determined offline, while online scaling is used during serving. It also includes hardware modules for quantization, dequantization, and memory management so the algorithmic savings become system speedup.

The reported results in the paper summary include throughput improvement over an A100 baseline with small accuracy loss. The exact value is less important for this project than the mechanism: KV cache bitwidth, context length, batch size, and memory layout directly affect effective serving capacity.

## 상세 한글 독해 및 번역 요약

Oaken은 LLM serving에서 KV cache가 만드는 memory bottleneck을 정면으로 다루는 핵심 논문이다. LLM inference는 prefill과 generation으로 나뉘고, generation 단계에서는 이전 token들의 key/value activation을 KV cache에서 계속 읽는다. batch size가 커지고 context length가 길어질수록 KV cache는 HBM 용량과 bandwidth를 동시에 압박한다.

기존 KV cache quantization은 bitwidth를 줄여 memory footprint를 낮추지만, outlier detection이나 mixed precision 처리 비용이 커서 실제 serving speedup으로 이어지기 어렵다. Oaken은 offline에서 outlier threshold를 정하고 online에서는 scale을 적용하는 hybrid 방식을 사용한다. 또 quantization/dequantization engine과 memory management unit을 hardware로 설계해 algorithmic saving이 실제 throughput 향상으로 이어지도록 한다.

이 논문이 프로젝트에 중요한 이유는 GPU FLOPS보다 HBM capacity, HBM bandwidth, KV cache bitwidth, context length가 token capacity를 좌우할 수 있음을 보여주기 때문이다.

## 박종세 교수 전문성 관점

박 교수님은 LLM inference 병목을 compute가 아니라 memory system과 KV cache 중심으로 분석하고, algorithm-hardware co-design으로 해결책을 제시하는 전문가다.

## 내 프로젝트와의 연결점

`tokens/sec/MW` 계산에 context length와 KV cache quantization sensitivity를 넣어야 한다. HBM supply, memory bandwidth, batch size가 모두 capacity driver다. Oaken은 HBM deep dive와 token capacity model을 연결하는 가장 중요한 논문 중 하나다.
