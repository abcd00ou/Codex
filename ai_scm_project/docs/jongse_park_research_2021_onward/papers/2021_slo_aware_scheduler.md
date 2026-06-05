# SLO-aware Inference Scheduler for Heterogeneous Processors in Edge Platforms

## Original English Notes

Venue: ACM Transactions on Architecture and Code Optimization, 2021  
Source: https://jongse-park.github.io/files/paper/2021-taco-edgeduler.pdf

This paper proposes SLO-aware scheduling for ML inference on heterogeneous edge platforms with CPU, GPU, DSP, and other accelerators. It uses pre-profiled model behavior, routes requests to suitable processors, and slices models at layer boundaries to reduce blocking from non-preemptive accelerators.

## 한글 번역 요약

이 논문은 edge platform에서 여러 ML model을 heterogeneous processor에 배치하면서 SLO를 만족시키는 scheduler를 다룬다. ML inference는 model별 실행 특성을 미리 profiling할 수 있고, GPU/DSP의 preemption 한계를 layer-level slicing으로 완화할 수 있다는 점이 핵심이다.

## 박종세 교수 전문성 관점

박 교수님은 inference serving의 핵심을 latency SLO, heterogeneity, profiling, scheduling으로 보는 연구 흐름을 2021년부터 이어왔다.

## 내 프로젝트 연결점

LLM datacenter serving에서도 같은 원리가 반복된다. raw throughput보다 SLO-aware throughput이 중요하다. `tokens/sec/MW` 가정은 latency 목표와 tail behavior를 반영해야 한다.

