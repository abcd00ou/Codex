# Tandem Processor: Grappling with Emerging Operators in Neural Networks

## Original English Notes

Venue: ASPLOS 2024, Honorable Mention in IEEE Micro Top Picks  
Source: https://jongse-park.github.io/publications/

Tandem Processor addresses emerging neural-network operators that are not well served by conventional accelerator assumptions.

## 한글 번역 요약

이 논문은 neural network에서 새롭게 등장하는 operator들을 기존 accelerator가 잘 처리하지 못하는 문제를 다룬다. AI model architecture가 계속 바뀌면 fixed-function accelerator는 높은 효율을 유지하기 어렵다.

## 박종세 교수 전문성 관점

박 교수님은 AI accelerator를 특정 세대 model에 맞추는 것보다, 변화하는 operator set에 대응하는 architecture 문제를 연구한다.

## 내 프로젝트 연결점

ASIC efficiency uplift를 장기적으로 높게 두려면 operator drift risk를 고려해야 한다. transformer 이후 workload가 확산되면 specialized accelerator의 effective utilization이 낮아질 수 있다.

