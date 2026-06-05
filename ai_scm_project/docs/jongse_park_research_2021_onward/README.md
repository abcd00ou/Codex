# Jongse Park Research Notes, 2021 Onward

이 폴더는 KAIST 박종세 교수님의 2021년 이후 논문을 논문별 Markdown으로 정리한 작업 폴더입니다.

범위는 publications page에 공개된 2021-2026년 논문입니다. 각 파일은 원문 제목과 영어 핵심 노트, 한글 번역 요약, 그리고 현재 프로젝트와의 연결점만 담습니다. 교수님께 드릴 질문 리스트는 의도적으로 제외했습니다.

## 왜 이 연구자가 중요한가

박종세 교수님의 최근 연구는 LLM inference serving, NPU/PIM/CXL/ASIC 기반 이기종 가속, AI workload simulator, edge/video/multimodal AI systems에 집중되어 있습니다. 이 조합은 현재 프로젝트가 다루는 GPU, HBM, CoWoS, 전력, networking, token capacity, serving efficiency 가정과 직접 맞닿아 있습니다.

핵심 전문성은 다음과 같습니다.

| 전문 영역 | 의미 | 프로젝트 연결 |
|---|---|---|
| LLM inference systems | LLM serving의 TTFT, TPOT, throughput, KV cache, batching, scheduler 병목을 시스템 관점에서 분석 | `llm_token_capacity_project`의 `tokens/sec/MW`, workload fit factor, inference power share 검증 |
| Hardware/software co-design | 알고리즘, runtime, accelerator, memory system을 같이 설계 | `ai_scm_project`의 GPU/HBM/PIM/CXL/ASIC 병목 레이어 세분화 |
| Simulation methodology | LLMServingSim, PyTorchSim, ONNXim처럼 빠르면서도 fidelity가 있는 simulator 구축 | public benchmark를 production serving capacity로 바꾸는 중간 검증 계층 |
| Memory-centric acceleration | KV cache, HBM bandwidth/capacity, PIM, CXL memory pool, quantization을 중심으로 inference 병목 완화 | HBM 수급, memory bandwidth, context length sensitivity 반영 |
| Multimodal/edge AI | video-language, continuous learning, robotics, 3D workload를 edge/datacenter 관점에서 분석 | text output token만으로는 설명되지 않는 AI compute demand 확장 |

## 읽는 순서

1. `papers/2024_llmservingsim.md`
2. `papers/2026_llmservingsim_2_0.md`
3. `papers/2025_oaken.md`
4. `papers/2024_neupims.md`
5. `papers/2025_pimba.md`
6. `papers/2025_pytorchsim.md`
7. `papers/2024_onnxim.md`
8. `papers/2024_lpu.md`
9. `papers/2022_gpulet.md`
10. `papers/2021_slo_aware_scheduler.md`

## Source

- Publications page: https://jongse-park.github.io/publications/
- LLMServingSim website: https://llmservingsim.ai/
- LLMServingSim code: https://github.com/casys-kaist/LLMServingSim

