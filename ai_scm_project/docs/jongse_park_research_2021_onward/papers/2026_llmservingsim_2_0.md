# LLMServingSim 2.0: A Unified Simulator for Heterogeneous and Disaggregated LLM Serving Infrastructure

## Original English Notes

Venue: ISPASS 2026, Best Paper Award  
Sources: https://llmservingsim.ai/ and https://github.com/casys-kaist/LLMServingSim

LLMServingSim 2.0 is a unified simulator for heterogeneous and disaggregated LLM serving infrastructure. The project page describes production-fidelity modeling of TTFT, TPOT, and throughput, using a vLLM-based layerwise profiler. It supports GPU, CPU, CXL, and PIM tiers, tensor/pipeline/expert/data parallelism combinations, ShareGPT-style traces, and closed-loop agentic workloads.

## 한글 번역 요약

LLMServingSim 2.0은 이기종 하드웨어와 분리형 메모리/서빙 구조를 함께 다루는 LLM serving simulator다. 단순 GPU benchmark가 아니라 TTFT, TPOT, throughput, scheduler, parallelism, memory tier, trace를 함께 고려한다. 특히 agentic session과 tool-call workload까지 언급한다는 점이 중요하다.

## 박종세 교수 전문성 관점

박 교수님은 LLM serving을 단순 model inference가 아니라 datacenter-scale system problem으로 보는 전문가다. simulator, scheduler, memory hierarchy, hardware topology를 연결해 production-like serving behavior를 설명하는 쪽에 강점이 있다.

## 내 프로젝트 연결점

`tokens/sec/MW`를 public benchmark에서 바로 가져오면 production capacity를 과대평가할 수 있다. 이 논문은 benchmark와 실제 serving capacity 사이에 `serving realism factor` 또는 `simulation-calibrated workload fit factor`를 두는 근거가 된다.

