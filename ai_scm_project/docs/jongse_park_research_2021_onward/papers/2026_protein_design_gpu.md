# Understanding the Performance Behaviors of End-to-End Protein Design Pipelines on GPUs

## Source and Scope

Venue: IEEE Computer Architecture Letters 2026  
Source: https://jongse-park.github.io/publications/  
Copyright note: This note is a paraphrased research reading, not a reproduction of the original paper.

## Detailed English Reading

This paper characterizes end-to-end protein design pipelines on GPUs. The phrase end-to-end is important. Many benchmark studies isolate a single model or kernel, while real scientific AI pipelines combine model inference, sampling, relaxation, scoring, data transformation, and orchestration.

Protein design workloads are different from chat LLM serving. They may be batch-heavy, pipeline-heavy, and scientific-computing-heavy. GPU utilization may be determined by data preparation, model ensemble behavior, memory footprint, and pipeline dependencies rather than by a single transformer decode loop.

For the research profile, this work shows that Professor Park’s group studies AI workload behavior beyond commercial LLM services. It is part of a broader effort to understand how different AI applications stress hardware in distinct ways.

## 상세 한글 독해 및 번역 요약

이 논문은 protein design pipeline 전체가 GPU에서 어떤 성능 특성을 보이는지 분석한다. 제목에서 end-to-end라는 표현이 중요하다. 실제 scientific AI는 모델 하나만 실행하는 것이 아니라, 입력 생성, 모델 추론, 후보 샘플링, 구조 평가, scoring, 후처리, 반복 orchestration이 함께 움직인다.

이런 workload는 LLM serving과 다르다. chat LLM은 TTFT, TPOT, KV cache, batch scheduling이 핵심이지만, protein design은 pipeline dependency, GPU batch efficiency, memory footprint, model ensemble, scientific post-processing이 중요할 수 있다.

이 논문은 박종세 교수님의 AI systems 연구가 LLM뿐 아니라 scientific AI workload로도 확장된다는 점을 보여준다.

## 박종세 교수 전문성 관점

박 교수님은 AI workload를 application pipeline 단위로 characterizing하는 연구를 수행한다. 이는 단일 benchmark를 넘어선 system-level 성능 분석 역량을 의미한다.

## 내 프로젝트와의 연결점

AI datacenter 전력이 모두 LLM token generation에 쓰이는 것은 아니다. Bio AI, scientific AI, simulation AI가 GPU capacity를 소모하면 `model owner token capacity`와 `total AI compute demand`를 분리해야 한다.
