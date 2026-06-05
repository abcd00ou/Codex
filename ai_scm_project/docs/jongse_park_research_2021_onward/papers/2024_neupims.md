# NeuPIMs: NPU-PIM Heterogeneous Acceleration for Batched LLM Inferencing

## Original English Notes

Venue: ASPLOS 2024  
Source: https://jongse-park.github.io/files/paper/2024-asplos-neupims.pdf

NeuPIMs observes that batched LLM inference mixes GEMM-heavy QKV/FFN operations and GEMV-heavy attention operations. NPUs are strong for GEMM, while PIM is well suited to memory-bandwidth-heavy GEMV. NeuPIMs uses dual row buffers and runtime sub-batch interleaving to enable concurrent NPU and PIM execution.

## 한글 번역 요약

NeuPIMs는 LLM decoder block을 GEMM과 GEMV로 나눠 본다. QKV generation과 FFN은 NPU가 잘 처리하지만, attention의 GEMV는 memory bandwidth가 중요해 PIM이 유리하다. dual row buffer와 sub-batch interleaving으로 NPU와 PIM을 동시에 활용한다.

## 박종세 교수 전문성 관점

박 교수님은 LLM serving 병목을 layer/operator 수준으로 분해하고, 그에 맞는 heterogeneous acceleration을 설계하는 전문가다.

## 내 프로젝트 연결점

GPU/HBM 수요를 하나의 숫자로 보면 안 된다. prefill/decode, GEMM/GEMV, attention/FFN, memory movement별 bottleneck이 다르다. PIM은 GPU 대체재라기보다 memory-bound decode/attention offload로 모델링하는 편이 타당하다.

