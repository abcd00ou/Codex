# A Simulator for LLM Inference Systems Exploiting CXL Memory Pools

## Original English Notes

Venue: IEEE Computer Architecture Letters, 2026, to appear  
Source: https://jongse-park.github.io/publications/

The title indicates a simulator for LLM inference systems that use CXL memory pools. The likely system question is how far lower-cost or pooled memory can supplement scarce HBM capacity without breaking inference latency and throughput.

## 한글 번역 요약

이 논문은 CXL 메모리 풀을 활용하는 LLM inference 시스템을 시뮬레이션하는 연구다. LLM serving에서는 KV cache와 long-context workload 때문에 HBM 용량이 빠르게 부족해질 수 있다. CXL은 memory capacity를 확장할 수 있지만, latency와 bandwidth 측면에서 HBM과 동일하지 않기 때문에 serving 성능을 별도로 검증해야 한다.

## 박종세 교수 전문성 관점

박 교수님의 연구가 GPU/NPU 자체뿐 아니라 memory disaggregation, CXL, memory hierarchy까지 포함하는 LLM serving infrastructure 연구임을 보여준다.

## 내 프로젝트 연결점

`llm_token_capacity_project`에서 HBM capacity를 단순 GPU 세대별 proxy로만 다루면 부족하다. CXL memory pool은 HBM shortage 완화 수단이지만 `tokens/sec/MW`, TTFT, TPOT, SLO에 haircut을 줄 수 있다. HBM/CXL tiering sensitivity를 별도 가정으로 둘 가치가 있다.

