# Deja Vu: Efficient Video-Language Query Engine with Learning-based Inter-Frame Computation Reuse

## Source and Scope

Venue: VLDB 2025  
Source: https://jongse-park.github.io/files/paper/2025-vldb-dejavu.pdf  
Copyright note: This note is a paraphrased research reading, not a reproduction of the original paper.

## Detailed English Reading

Deja Vu studies video-language query systems. Modern VideoLM pipelines often use Vision Transformers to generate embeddings for many frames. A long video sampled at even a modest frame rate creates thousands of frame-level inference calls. The paper’s idea is to exploit similarity across adjacent frames. Instead of recomputing visual embeddings independently for every frame, the system learns where computation can be reused and then uses memory-compute compaction to translate theoretical FLOP savings into real speedup.

The system perspective is important. Many ML optimizations reduce FLOPs on paper but fail to improve GPU runtime because memory layout, batching, and kernel execution overheads dominate. Deja Vu addresses that gap by coupling model-level reuse with systems-level compaction.

This paper is outside text LLM serving, but it is highly relevant to multimodal AI infrastructure. Video-language workloads can consume enormous compute before any text output token is produced.

## 상세 한글 독해 및 번역 요약

Deja Vu는 VideoLM query engine을 위한 연구다. VideoLM은 video frame에서 visual embedding을 만들고, 그 embedding을 기반으로 retrieval, question answering, grounding 같은 작업을 수행한다. 문제는 video frame 수가 매우 많다는 점이다. 한 시간짜리 영상을 낮은 FPS로 sampling해도 수천 개 frame이 생기며, 각 frame마다 ViT inference를 돌리면 비용이 매우 크다.

논문은 인접 frame 사이의 유사성을 이용한다. 매 frame을 독립적으로 계산하지 않고, 어떤 계산을 재사용할 수 있는지 학습한다. 또한 FLOP 절감이 실제 GPU speedup으로 이어지도록 memory-compute compaction을 결합한다.

이 논문은 멀티모달 AI capacity를 이해하는 데 중요하다. 사용자가 받는 output token은 적어 보여도, 그 전에 video embedding generation에서 막대한 compute가 소모될 수 있다.

## 박종세 교수 전문성 관점

박 교수님은 AI model inference뿐 아니라 database/query engine 관점의 video-language system까지 연구한다.

## 내 프로젝트와의 연결점

LLM token capacity 프로젝트가 text output token만 계산하면 multimodal compute burden을 놓친다. video ingestion, visual embedding, frame reuse ratio, storage bandwidth를 별도 demand layer로 둬야 한다.
