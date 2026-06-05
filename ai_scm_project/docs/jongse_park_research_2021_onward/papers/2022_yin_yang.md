# Yin-Yang: Programming Abstraction for Cross-Domain Multi-Acceleration

## Original English Notes

Venue: IEEE Micro 2022  
Source: https://jongse-park.github.io/publications/

Yin-Yang proposes programming abstractions for cross-domain multi-acceleration.

## 한글 번역 요약

이 논문은 여러 domain의 accelerator를 함께 쓰기 위한 programming abstraction을 다룬다. accelerator가 많아질수록 hardware보다 software abstraction과 runtime이 병목이 될 수 있다.

## 박종세 교수 전문성 관점

박 교수님은 hardware만이 아니라 compiler/runtime/programming abstraction까지 포함한 full-stack acceleration을 연구한다.

## 내 프로젝트 연결점

GPU, TPU, Trainium, Maia, MTIA, PIM, CXL이 섞인 AI datacenter에서는 software stack이 efficiency를 좌우한다. purpose-built accelerator share가 늘어도 software maturity가 낮으면 effective capacity가 낮을 수 있다.

