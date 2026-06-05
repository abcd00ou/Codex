# PyTorchSim: A Comprehensive, Fast, and Accurate NPU Simulation Framework

## Source and Scope

Venue: MICRO 2025  
Source: https://jongse-park.github.io/files/paper/2025-micro-pytorchsim.pdf  
Copyright note: This note is a paraphrased research reading, not a reproduction of the original paper.

## Detailed English Reading

PyTorchSim is a simulation framework for NPUs integrated with modern ML software infrastructure. It uses PyTorch 2 as the front end, lowers models through MLIR/LLVM, targets a RISC-V-based ISA with accelerator extensions, and combines instruction-level and tile-level simulation. The key trade-off is simulation speed versus accuracy. Full instruction-level simulation is accurate but too slow for broad design exploration. Tile-level simulation uses pre-characterized tile latencies while still modeling memory and interconnect behavior.

The paper reports large speedups over slower simulator baselines while maintaining useful accuracy against TPUv3. It also supports scenarios that matter for modern AI infrastructure: multi-model tenancy, sparse/dense heterogeneity, compiler optimizations, chiplet-aware scheduling, and training-related effects.

Its significance is methodological. It gives a way to evaluate NPU designs before silicon, and it connects model graphs, compiler lowering, ISA, memory system, and timing behavior.

## 상세 한글 독해 및 번역 요약

PyTorchSim은 NPU를 평가하기 위한 빠르고 정확한 simulation framework다. PyTorch 2에서 시작해 MLIR/LLVM lowering을 거쳐 RISC-V 기반 ISA와 accelerator extension으로 실행을 모델링한다. instruction-level simulation은 정확하지만 느리고, tile-level simulation은 훨씬 빠르다. PyTorchSim은 두 접근의 장점을 섞어 넓은 design space를 탐색하면서도 memory/interconnect 같은 중요한 병목은 보존하려 한다.

이 논문이 중요한 이유는 NPU나 ASIC 효율을 vendor claim만으로 판단하지 않고, model graph부터 compiler, ISA, memory system까지 연결해 검증할 수 있기 때문이다. 특히 multi-model tenancy와 chiplet-aware scheduling을 다룬다는 점은 datacenter AI capacity와 직접 연결된다.

요약하면 PyTorchSim은 purpose-built accelerator의 성능을 evidence-grade로 평가하기 위한 도구적 기반이다.

## 박종세 교수 전문성 관점

박 교수님은 accelerator design뿐 아니라 그 design을 검증하는 simulation/compiler stack까지 이해하는 full-stack architecture 연구자다.

## 내 프로젝트와의 연결점

내 프로젝트에서 TPU, Trainium, Maia, MTIA, LPU 같은 purpose-built accelerator의 tokens/sec/MW를 추정할 때 simulation fidelity 기준이 필요하다. PyTorchSim은 그런 기준을 세우는 reference가 된다.
