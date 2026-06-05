# Oaken: Fast and Efficient LLM Serving with Online-Offline Hybrid KV Cache Quantization

## Original English Notes

Venue: ISCA 2025  
Source: https://jongse-park.github.io/files/paper/2025-isca-oaken.pdf

Oaken targets the KV cache bottleneck in batched LLM serving. The paper argues that attention operations become memory-bandwidth-bound and that long context and large batches create severe KV cache capacity pressure. Oaken uses offline outlier thresholds and online scaling for KV cache quantization, plus hardware support for quantization/dequantization and memory management.

## 한글 번역 요약

Oaken은 LLM serving에서 KV cache가 만드는 memory bandwidth와 capacity 병목을 다룬다. 긴 context와 큰 batch size는 KV cache를 크게 만들고, HBM 용량과 bandwidth를 동시에 압박한다. Oaken은 offline threshold와 online scale을 결합한 hybrid quantization으로 accuracy 손실을 작게 유지하면서 throughput을 높이려 한다.

## 박종세 교수 전문성 관점

박 교수님은 LLM inference의 병목을 FLOPS보다 memory system, KV cache, data movement 중심으로 분석하는 전문가다.

## 내 프로젝트 연결점

`tokens/sec/MW`를 GPU generation만으로 설명하면 KV cache/context length 효과를 놓친다. HBM capacity, HBM bandwidth, KV cache bitwidth, average context length, batch size를 별도 sensitivity로 둬야 한다. Oaken은 HBM 수급과 LLM serving efficiency를 연결하는 핵심 근거다.

