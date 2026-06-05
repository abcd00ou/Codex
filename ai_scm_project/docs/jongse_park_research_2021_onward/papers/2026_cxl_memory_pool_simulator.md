# A Simulator for LLM Inference Systems Exploiting CXL Memory Pools

## Source and Scope

Venue: IEEE Computer Architecture Letters 2026, to appear  
Source: https://jongse-park.github.io/publications/  
Copyright note: This note is a paraphrased research reading, not a reproduction of the original paper.

## Detailed English Reading

The paper title indicates a simulator for LLM inference systems that exploit CXL memory pools. The central system problem is straightforward: LLM serving is increasingly constrained by memory capacity and bandwidth, especially during long-context generation and batched serving. HBM is fast but expensive and capacity-limited. CXL-attached memory can expand the memory pool, but it introduces a different latency and bandwidth profile. A simulator is needed because the trade-off cannot be read directly from peak bandwidth numbers.

In LLM inference, KV cache grows with sequence length and batch size. When the cache does not fit comfortably in HBM, the serving system can either scale out to more GPUs, compress the cache, page the cache, or use a tiered memory system. CXL memory pools belong to the tiered/disaggregated memory direction. The value proposition is capacity elasticity and possibly better fleet utilization. The risk is that decode latency, tail latency, and token throughput suffer if the serving path frequently touches slower memory.

This work likely connects to the LLMServingSim line of research. It suggests that the CASYS group is not only studying accelerators but also the memory hierarchy and disaggregated infrastructure around LLM serving.

## 상세 한글 독해 및 번역 요약

이 논문은 CXL memory pool을 활용하는 LLM inference system을 시뮬레이션하는 연구다. LLM serving에서 memory pool이 중요한 이유는 KV cache 때문이다. 모델이 긴 context를 처리하거나 많은 request를 batch로 처리하면 key/value activation을 계속 저장해야 하고, 이 cache가 HBM 용량을 압박한다. HBM은 빠르지만 비싸고 용량이 제한적이므로 CXL 기반 외부/공유 memory tier를 쓰는 아이디어가 등장한다.

하지만 CXL memory를 붙인다고 capacity 문제가 자동으로 해결되는 것은 아니다. LLM generation은 token을 순차적으로 생성하므로 decode 단계의 latency와 tail latency가 매우 중요하다. 느린 memory tier에서 KV cache를 자주 읽으면 TTFT나 TPOT가 악화될 수 있고, throughput도 낮아질 수 있다. 따라서 CXL memory pool은 단순한 메모리 증설이 아니라 serving scheduler, cache placement, paging policy, request batching과 함께 평가해야 한다.

이 논문은 LLM inference capacity가 GPU 개수만의 함수가 아니라 HBM, CXL, memory tiering, data movement의 함수라는 점을 분명히 해준다.

## 박종세 교수 전문성 관점

박 교수님은 LLM serving에서 accelerator die 자체보다 memory hierarchy와 disaggregated infrastructure까지 보는 전문가다. CXL, PIM, HBM, KV cache를 함께 다루는 능력이 핵심이다.

## 내 프로젝트와의 연결점

LLM token capacity 모델에서 HBM 부족을 단순히 더 많은 GPU 구매로만 연결하면 부족하다. CXL memory pool은 capex와 capacity를 바꿀 수 있지만 latency haircut을 만든다. `tokens/sec/MW`에는 HBM-only, HBM+CXL, CXL-heavy 같은 memory-tier scenario가 필요하다.
