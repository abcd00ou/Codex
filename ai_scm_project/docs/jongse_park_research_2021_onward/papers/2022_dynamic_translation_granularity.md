# Supporting Dynamic Translation Granularity for Hybrid Memory Systems

## Original English Notes

Venue: ICCD 2022  
Source: https://jongse-park.github.io/publications/

This paper studies dynamic translation granularity in hybrid memory systems.

## 한글 번역 요약

이 논문은 hybrid memory system에서 address translation granularity를 동적으로 지원하는 방법을 다룬다. 여러 memory tier가 섞일 때 page size, translation, mapping이 성능에 영향을 준다.

## 박종세 교수 전문성 관점

박 교수님의 memory system 연구는 이후 CXL/PIM/HBM/KV cache 논의와 이어지는 기반이다.

## 내 프로젝트 연결점

LLM serving에서 HBM, DDR, CXL이 섞이면 capacity만 늘어나는 것이 아니라 memory mapping과 address translation overhead가 생긴다. CXL memory pool 가정에 latency/translation penalty를 둘 필요가 있다.

