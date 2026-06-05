# Deja Vu: Efficient Video-Language Query Engine with Learning-based Inter-Frame Computation Reuse

## Original English Notes

Venue: VLDB 2025  
Source: https://jongse-park.github.io/files/paper/2025-vldb-dejavu.pdf

Deja Vu targets Video-Language Model query systems. It reduces repeated ViT embedding generation across many video frames by learning inter-frame reuse opportunities and using memory-compute compaction so FLOP savings translate into speedup.

## 한글 번역 요약

Deja Vu는 VideoLM이 많은 video frame을 반복적으로 ViT에 통과시키는 병목을 줄이는 query engine이다. 프레임 사이의 유사성을 학습해 계산을 재사용하고, GPU에서 실제 성능 향상으로 이어지도록 memory-compute compaction을 결합한다.

## 박종세 교수 전문성 관점

박 교수님은 LLM text serving뿐 아니라 video-language workload를 database/query system 관점에서도 다룬다.

## 내 프로젝트 연결점

멀티모달 AI는 output token만으로 capacity를 설명하기 어렵다. visual embedding generation, frame sampling, storage bandwidth, reuse ratio가 별도 compute driver가 된다. Gemini/GPT-4o류 멀티모달 surface를 모델링할 때 text token capacity와 분리할 필요가 있다.

