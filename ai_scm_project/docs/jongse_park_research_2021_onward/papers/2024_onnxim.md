# ONNXim: A Fast, Cycle-level Multi-core NPU Simulator

## Original English Notes

Venue: IEEE Computer Architecture Letters, 2024  
Source: https://jongse-park.github.io/files/paper/2024-cal-onnxim.pdf

ONNXim is a fast cycle-level simulator for multi-core NPUs. It uses ONNX graphs as input, supports multi-core and multi-tenant scenarios, and models shared DRAM/NoC contention. The paper highlights dynamic input shape as important for LLM KV cache behavior.

## 한글 번역 요약

ONNXim은 ONNX graph를 입력으로 받아 multi-core NPU를 cycle-level로 빠르게 시뮬레이션하는 framework다. 여러 model이 동시에 실행되는 multi-tenant scenario와 DRAM/NoC contention을 다룬다. LLM generation에서 sequence length가 증가하며 KV cache shape이 바뀌는 점도 motivation으로 언급된다.

## 박종세 교수 전문성 관점

박 교수님은 NPU simulation에서 model portability, multi-tenancy, memory/interconnect contention을 중요하게 본다.

## 내 프로젝트 연결점

AI capacity model에서 accelerator 성능은 compute unit만이 아니라 DRAM/NoC contention과 multi-tenancy에 의해 결정된다. ONNXim은 다양한 model family를 동일 graph format으로 비교하는 methodology 후보가 된다.

