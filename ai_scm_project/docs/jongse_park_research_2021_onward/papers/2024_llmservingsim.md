# LLMServingSim: A HW/SW Co-Simulation Infrastructure for LLM Inference Serving at Scale

## Original English Notes

Venue: IISWC 2024, Best Paper Award and Distinguished Artifact Award  
Source: https://jongse-park.github.io/files/paper/2024-iiswc-llmservingsim.pdf

LLMServingSim is a hardware/software co-simulation infrastructure for LLM serving. It addresses dynamic workload variation from autoregressive decoding and avoids repeated simulation by reusing results across decoder blocks and iterations. The paper reports close tracking of GPU serving behavior with under 14.7% error and much faster simulation than conventional accelerator simulators.

## 한글 번역 요약

LLMServingSim은 LLM inference serving을 대규모로 시뮬레이션하기 위한 HW/SW co-simulation 인프라다. autoregressive generation 때문에 workload가 iteration마다 달라지고, 기존 simulator는 너무 느리다는 문제를 해결한다. decoder block 반복성과 iteration-level 재사용을 이용해 더 빠르게 serving behavior를 예측한다.

## 박종세 교수 전문성 관점

박 교수님은 LLM serving을 "모델 하나를 빠르게 돌리는 문제"가 아니라 scheduler, accelerator, memory, trace, simulation speed가 결합된 systems problem으로 정식화한다.

## 내 프로젝트 연결점

현재 프로젝트의 `commercial_workload_fit_factor`는 이 논문을 바탕으로 세분화할 수 있다. public benchmark 대비 production serving haircut은 TTFT, TPOT, autoregressive dynamics, batching, context length, hardware heterogeneity를 반영해야 한다.

