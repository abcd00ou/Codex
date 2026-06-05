# Accelerator Polymorphism: Transcending Domain-Specific Architectures with Robotics

## Original English Notes

Venue: ISCA 2026, to appear  
Source: https://jongse-park.github.io/publications/

This paper appears to study how accelerator architectures can move beyond narrow domain-specific assumptions. Robotics is a useful stress case because it mixes perception, planning, control, memory movement, and real-time constraints instead of running a single clean neural-network kernel.

## 한글 번역 요약

이 논문은 특정 도메인에만 최적화된 가속기가 실제 로보틱스처럼 여러 종류의 연산과 시스템 제약이 섞인 환경에서 얼마나 잘 버틸 수 있는지를 다루는 연구로 보인다. 공개 목록 기준으로는 아직 상세 본문이 공개되지 않았으므로, 현재 정리는 연구 방향 중심이다.

## 박종세 교수 전문성 관점

박 교수님의 연구가 LLM inference에만 머무르지 않고, 여러 AI workload를 수용하는 범용적/다형적 accelerator 설계로 확장되고 있음을 보여준다.

## 내 프로젝트 연결점

현재 AI SCM 모델에서 ASIC 효율을 높게 가정할 때, workload가 LLM-only가 아니라 robotics/agentic/multimodal workload로 넓어지면 fixed-function accelerator의 효율이 낮아질 수 있다. 이 논문은 accelerator mix 가정에 "workload diversity penalty"를 추가할 때 참고할 수 있다.

