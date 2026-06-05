# Cocoon: A System Architecture for Differentially Private Training with Correlated Noises

## Source and Scope

Venue: OSDI 2026, to appear  
Source: https://jongse-park.github.io/publications/  
Copyright note: This note is a paraphrased research reading, not a reproduction of the original paper.

## Detailed English Reading

Cocoon studies system architecture for differentially private training with correlated noises. Differential privacy is not just a mathematical privacy layer; it changes the system cost of training. Private training may require additional noise generation, accounting, synchronization, and careful pipeline design. When the privacy mechanism is correlated across computations, the system must preserve both statistical guarantees and execution efficiency.

This paper is less directly tied to LLM inference serving than the LLMServingSim or Oaken work. Its importance is that it broadens the view of AI infrastructure. Some future AI workloads will be constrained by privacy, security, and compliance, not only by raw throughput. A system architecture paper in OSDI implies attention to implementation, distributed execution, overhead management, and correctness guarantees.

For an AI infrastructure model, this type of work is a reminder that training power is not a single homogeneous bucket. Privacy-preserving training can impose extra work and different bottlenecks from ordinary pretraining or post-training.

## 상세 한글 독해 및 번역 요약

Cocoon은 correlated noise를 사용하는 differential privacy training system architecture를 다루는 논문이다. 차등 프라이버시 학습은 단순히 학습 loss에 noise를 넣는 문제가 아니라, privacy accounting, noise generation, distributed synchronization, correctness guarantee, training throughput을 함께 다뤄야 하는 시스템 문제다.

이 논문은 LLM inference serving과 직접 연결되지는 않는다. 그러나 상용 AI 인프라 관점에서는 중요하다. 앞으로 기업 고객, 의료, 금융, 공공 영역에서 privacy-preserving training이나 confidential fine-tuning 수요가 커질 수 있다. 이런 workload는 일반 training보다 더 많은 overhead와 복잡한 시스템 제약을 가질 수 있다.

따라서 이 논문은 박종세 교수님의 연구가 inference accelerator뿐 아니라 secure/private AI system architecture까지 확장된다는 것을 보여준다.

## 박종세 교수 전문성 관점

박 교수님은 성능 중심 computer architecture뿐 아니라 privacy, security, correctness가 결합된 AI system 문제도 다루는 연구자다.

## 내 프로젝트와의 연결점

내 프로젝트에서 training power share를 하나의 단순 비율로 두면 privacy-preserving training의 비용을 설명하기 어렵다. enterprise/private AI가 커질 경우 training efficiency haircut 또는 secure training overhead category를 추가할 수 있다.
