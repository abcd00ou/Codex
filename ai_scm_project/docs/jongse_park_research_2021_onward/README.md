# Jongse Park Research Notes, 2021 Onward

이 폴더는 KAIST 박종세 교수님의 2021년 이후 논문을 논문별 Markdown으로 정리한 작업 폴더입니다.

저작권 때문에 논문 전문 원문을 복제하거나 전문 번역본을 만들지는 않습니다. 대신 각 논문마다 다음을 분리해 최대한 자세히 작성했습니다.

- `Detailed English Reading`: 원문 내용을 베끼지 않는 영어 상세 독해본
- `상세 한글 독해 및 번역 요약`: 원문 전문 번역이 아닌 한국어 상세 해설/번역 요약
- `박종세 교수 전문성 관점`: 논문을 통해 보이는 연구자의 전문 영역
- `내 프로젝트와의 연결점`: AI SCM 및 LLM token capacity 프로젝트와 연결되는 지점

## 박종세 교수님은 어떤 전문가인가

박종세 교수님의 2021년 이후 연구는 LLM inference serving, NPU/PIM/CXL/ASIC 기반 이기종 가속, AI workload simulator, memory-centric acceleration, secure AI architecture, video/multimodal/edge AI systems로 이어진다. 한마디로 정리하면 **AI workload를 hardware, software, memory, scheduler, simulator, security까지 포함한 end-to-end systems problem으로 분석하는 computer architecture 전문가**다.

특히 현재 프로젝트와 직접 맞닿는 전문성은 다음 네 가지다.

| 전문 영역 | 설명 | 프로젝트 의미 |
|---|---|---|
| LLM serving systems | TTFT, TPOT, throughput, batching, KV cache, parallelism, disaggregated serving을 함께 분석 | `tokens/sec/MW`를 public benchmark에서 production capacity로 변환하는 방법론 |
| Memory-centric acceleration | HBM bandwidth/capacity, KV cache, CXL, PIM, quantization을 중심으로 병목을 해석 | HBM, CXL, PIM, context length sensitivity를 supply-demand 모델에 반영 |
| Simulator methodology | LLMServingSim, PyTorchSim, ONNXim 등 fast/fidelity simulator 구축 | vendor benchmark와 실제 serving performance 사이의 evidence layer |
| Heterogeneous and edge AI | GPU/NPU/PIM/ASIC, video-language, continuous learning, robotics workload 분석 | text token capacity 밖의 multimodal/edge compute demand 확장 |

## 가장 먼저 볼 논문

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
