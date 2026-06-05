# PyTorchSim: A Comprehensive, Fast, and Accurate NPU Simulation Framework

## Original English Notes

Venue: MICRO 2025  
Source: https://jongse-park.github.io/files/paper/2025-micro-pytorchsim.pdf

PyTorchSim integrates PyTorch 2, MLIR/LLVM lowering, a RISC-V-based ISA, Gem5/Spike execution, and tile-level simulation. It aims to support fast and accurate NPU design exploration across inference, training, multi-tenancy, compiler optimization, chiplet-aware scheduling, and sparse/dense scenarios.

## 한글 번역 요약

PyTorchSim은 NPU를 빠르고 정확하게 평가하기 위한 simulation framework다. instruction-level simulation은 정확하지만 느리기 때문에, tile-level latency와 cycle-accurate DRAM/interconnect modeling을 결합한다. public summary 기준으로 Accel-Sim 대비 최대 139배 빠르고 TPUv3 대비 MAE 11.5% 수준의 정확도를 보고한다.

## 박종세 교수 전문성 관점

박 교수님은 새로운 accelerator를 주장하는 데서 멈추지 않고, 그 accelerator를 검증할 수 있는 simulator와 compiler/runtime flow까지 연구한다.

## 내 프로젝트 연결점

purpose-built accelerator의 tokens/sec/MW가 공개되지 않을 때, 단순 vendor claim 대신 simulation fidelity 기준이 필요하다. PyTorchSim은 ASIC/NPU 효율 가정을 검증하는 reference methodology로 쓸 수 있다.

