# Understanding the Performance Behaviors of End-to-End Protein Design Pipelines on GPUs

## Original English Notes

Venue: IEEE Computer Architecture Letters, 2026  
Source: https://jongse-park.github.io/publications/

This paper studies end-to-end protein design pipelines on GPUs. The focus is performance characterization rather than only a single model kernel.

## 한글 번역 요약

이 논문은 protein design pipeline 전체가 GPU에서 어떤 성능 특성을 보이는지 분석한다. LLM serving과는 다르지만, AI datacenter가 scientific AI workload를 함께 처리할 때 어떤 병목이 생기는지 이해하는 데 도움이 된다.

## 박종세 교수 전문성 관점

박 교수님은 AI workload를 개별 kernel이 아니라 end-to-end pipeline으로 분석하는 연구 방향을 가진다.

## 내 프로젝트 연결점

상용 datacenter capacity 중 LLM inference가 아닌 scientific AI, bio AI, simulation workload가 차지하는 share를 따로 분리해야 한다. 그렇지 않으면 전력/GPU capacity가 모두 token generation에 쓰인다고 과대 해석할 수 있다.

