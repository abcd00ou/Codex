# 박종세 교수 연구 독해 노트, 2021년 이후

이 폴더는 KAIST 박종세 교수님의 2021년 이후 논문을 한곳에서 읽기 쉽게 정리한 자료입니다.

사용자 요청에 따라 기존의 논문별 개별 파일은 삭제했고, 논문 제목 중심의 통합 파일로 다시 구성했습니다.

## 파일 구성

| 파일 | 내용 |
|---|---|
| `papers_by_title.md` | 2021년 이후 논문을 제목별로 정리한 최대한 자세한 독해본 |
| `technical_terms_and_structure.md` | 기술 용어, LLM serving 구조, accelerator/memory/scheduler 개념 설명 |
| `llmservingsim_deep_dive.md` | LLMServingSim과 LLMServingSim 2.0 상세 독해 |
| `llmservingsim_benchmark_integration.md` | InferenceX benchmark를 LLMServingSim 2.0으로 고도화하기 위한 구조와 수집 데이터 |
| `pdf_study_pack_for_tps_per_mw.md` | 로컬 PDF를 다시 읽고 TPS/MW 근거 보강 관점에서 만든 공부자료와 도구 개발 계획 |
| `original_sources.md` | 원문 제목과 공식 링크 모음 |
| `source_index.md` | 연도별 논문 목록 |

## 저작권 처리 기준

논문 전문 원문을 복제하거나 abstract 전문을 그대로 번역해 저장하지 않습니다. 대신 다음 방식으로 정리합니다.

- 원문 저장: 논문 제목, venue, 공식 PDF/프로젝트 링크 저장
- Abstract: 전문 번역이 아니라 원문 내용을 베끼지 않는 자세한 한국어 의역 독해
- 본문: section-by-section에 가까운 상세 독해와 구조 설명
- 기술 용어: 처음 읽는 사람이 이해할 수 있도록 별도 파일에 설명

## 박종세 교수님은 어떤 전문가인가

박종세 교수님은 AI workload를 단순한 모델 실행이 아니라 hardware, software, memory, scheduler, simulator, security가 결합된 end-to-end system으로 분석하는 computer architecture/system researcher입니다.

특히 현재 프로젝트와 직접 맞닿는 축은 네 가지입니다.

1. LLM inference serving: TTFT, TPOT, throughput, batching, KV cache, parallelism, scheduler.
2. Memory-centric acceleration: HBM, KV cache, CXL, PIM, memory bandwidth/capacity.
3. Simulator methodology: LLMServingSim, PyTorchSim, ONNXim처럼 빠르면서도 근거 있는 simulator.
4. Heterogeneous/multimodal AI: GPU, NPU, PIM, ASIC, edge processor, video-language, robotics workload.

## 내 프로젝트와의 핵심 연결

현재 `AI SCM` 및 `LLM Token Capacity` 프로젝트는 GPU, HBM, CoWoS, 전력, networking, token throughput을 다룹니다. 박종세 교수님의 연구는 이 프로젝트에서 가장 약해지기 쉬운 부분, 즉 public benchmark를 production token capacity로 바꿀 때 필요한 system-level correction을 보강합니다.

가장 중요한 메시지는 다음입니다.

- `tokens/sec/MW`는 GPU peak benchmark가 아니라 serving system metric이다.
- HBM capacity와 bandwidth는 LLM inference의 핵심 병목이다.
- KV cache, context length, batch size, scheduler가 token capacity를 크게 바꾼다.
- PIM, CXL, ASIC은 GPU 대체라기보다 병목별 보완재로 봐야 한다.
- text output token만으로 multimodal AI demand를 설명하면 compute 부담을 과소평가한다.
