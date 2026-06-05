# 논문 제목별 상세 독해본

저작권 기준: 이 파일은 논문 전문 원문이나 abstract 전문 번역을 저장하지 않습니다. 대신 논문 제목, 공식 source, abstract 수준의 한국어 의역 독해, 상세 독해, 그리고 프로젝트 연결점을 제공합니다.

## 2026

### Accelerator Polymorphism: Transcending Domain-Specific Architectures with Robotics

Source: https://jongse-park.github.io/publications/

Abstract 의역 독해: 이 논문은 로보틱스 workload를 통해 기존 domain-specific accelerator의 한계를 다시 보는 연구로 이해할 수 있습니다. 로보틱스는 perception, planning, control, sensor fusion, memory movement, real-time constraint가 섞인 workload입니다. 따라서 한 가지 연산에만 최적화된 accelerator는 실제 로봇 시스템에서 충분하지 않을 수 있습니다.

상세 독해: AI 반도체는 특정 모델이나 특정 operator에 맞춰 설계될수록 peak efficiency가 좋아집니다. 그러나 robotics workload는 환경에 따라 계산 구조가 바뀝니다. dense matrix multiplication, sparse planning, graph-like computation, control-loop computation, vision model inference가 함께 실행될 수 있습니다. 이 논문은 accelerator가 한 도메인에 고정되지 않고 여러 workload 형태에 맞춰 역할을 바꿀 수 있어야 한다는 문제의식을 담고 있습니다.

프로젝트 연결: ASIC efficiency uplift를 장기 forecast에 넣을 때 workload diversity penalty를 고려해야 합니다. LLM-only accelerator는 robotics/agentic/multimodal workload에서 효율이 낮아질 수 있습니다.

### A Simulator for LLM Inference Systems Exploiting CXL Memory Pools

Source: https://jongse-park.github.io/publications/

Abstract 의역 독해: LLM inference에서 HBM은 빠르지만 용량이 제한적입니다. CXL memory pool은 더 큰 memory capacity를 제공할 수 있지만 latency와 bandwidth penalty가 있습니다. 이 논문은 CXL memory를 활용하는 LLM serving system을 평가하기 위한 simulator 연구입니다.

상세 독해: Long-context LLM과 batched serving은 KV cache를 크게 만듭니다. HBM에 KV cache를 모두 넣지 못하면 CXL memory 같은 외부 memory tier를 고려하게 됩니다. 하지만 CXL은 HBM보다 느릴 수 있어 decode latency와 TPOT에 영향을 줍니다. 따라서 CXL의 가치는 단순 capacity 확장만으로 판단할 수 없고, cache placement, paging, scheduler, request trace와 함께 평가해야 합니다.

프로젝트 연결: HBM shortage를 CXL로 보완하는 scenario를 모델에 넣을 수 있습니다. 다만 `tokens/sec/MW`에는 CXL latency haircut을 반영해야 합니다.

### Cocoon: A System Architecture for Differentially Private Training with Correlated Noises

Source: https://jongse-park.github.io/publications/

Abstract 의역 독해: 이 논문은 differential privacy training을 효율적으로 수행하기 위한 system architecture를 다룹니다. Privacy 보장은 수학적 알고리즘만의 문제가 아니라 training pipeline, noise generation, synchronization, correctness, overhead management가 결합된 시스템 문제입니다.

상세 독해: 차등 프라이버시 학습은 개인 정보 보호를 위해 noise를 추가하거나 gradient 정보를 제한합니다. 이 과정은 학습 품질과 시스템 비용을 동시에 바꿉니다. OSDI 논문이라는 점을 고려하면, 단순 알고리즘 제안이 아니라 실제 distributed training system에서 privacy guarantee와 performance를 함께 달성하는 구조가 핵심일 가능성이 큽니다.

프로젝트 연결: enterprise/private AI가 확대되면 training power efficiency가 일반 pretraining보다 낮아질 수 있습니다. training power share 내부에 secure/private training overhead를 별도 factor로 둘 수 있습니다.

### Revisiting Partial Tracing for Safe, Efficient, and Concurrent Garbage Collection in Unmanaged Languages

Source: https://jongse-park.github.io/publications/

Abstract 의역 독해: unmanaged language 환경에서 partial tracing을 이용해 memory safety와 concurrency를 개선하는 runtime systems 연구입니다. AI accelerator 논문은 아니지만 high-performance systems의 memory/runtime 문제를 다룹니다.

상세 독해: 고성능 시스템은 C/C++ 같은 unmanaged language를 많이 사용합니다. 이런 환경은 성능은 좋지만 memory safety 문제가 큽니다. Partial tracing은 일부 객체/메모리 영역만 추적해 안전성과 효율 사이의 균형을 잡으려는 접근입니다. Production AI serving stack도 low-level runtime 위에서 작동하므로 tail latency와 reliability 관점에서 간접적인 관련이 있습니다.

프로젝트 연결: 직접적인 capacity coefficient로 쓰기는 어렵지만, production serving efficiency가 accelerator만이 아니라 runtime stability와 memory management에도 의존한다는 배경 자료가 됩니다.

### LLMServingSim 2.0: A Unified Simulator for Heterogeneous and Disaggregated LLM Serving Infrastructure

Source: https://llmservingsim.ai/

Abstract 의역 독해: LLMServingSim 2.0은 GPU, CPU, CXL, PIM 같은 이기종 hardware와 tensor/pipeline/expert/data parallelism, disaggregated memory, agentic workload trace를 함께 다루는 LLM serving simulator입니다. 목표는 TTFT, TPOT, throughput 같은 production serving 지표를 더 현실적으로 평가하는 것입니다.

상세 독해: 이 논문은 LLM inference를 단일 GPU benchmark가 아니라 infrastructure-level serving problem으로 봅니다. 실제 LLM serving은 prefill/decode, KV cache, continuous batching, parallelism, memory tiering, network communication, request trace가 모두 얽혀 있습니다. LLMServingSim 2.0은 vLLM 기반 profiling과 serving simulation을 결합해 heterogeneous/disaggregated LLM infrastructure를 평가합니다.

프로젝트 연결: 현재 `tokens/sec/MW` 모델에서 가장 중요한 reference입니다. Public benchmark를 production token capacity로 바꾸기 전 simulator-calibrated serving factor가 필요합니다. 자세한 내용은 `llmservingsim_deep_dive.md`에 별도 정리했습니다.

### Neo: Real-Time On-Device 3D Gaussian Splatting with Reuse-and-Update Sorting Acceleration

Source: https://jongse-park.github.io/publications/

Abstract 의역 독해: 3D Gaussian Splatting을 온디바이스에서 실시간 처리하기 위한 acceleration 연구입니다. 3D rendering/understanding workload에서는 sorting, reuse, update, memory movement가 중요한 병목이 될 수 있습니다.

상세 독해: 이 논문은 text LLM과는 다른 spatial AI workload를 다룹니다. 3D/AR/robotics workload는 low latency, on-device power budget, graphics-like data structure, sensor update가 중요합니다. AI compute 수요가 text token에서 3D interactive workload로 확장될 때 필요한 architecture 방향을 보여줍니다.

프로젝트 연결: AI SCM 모델에서 edge NPU, mobile accelerator, spatial AI demand를 별도 축으로 볼 필요가 있습니다.

### Understanding the Performance Behaviors of End-to-End Protein Design Pipelines on GPUs

Source: https://jongse-park.github.io/publications/

Abstract 의역 독해: Protein design pipeline 전체가 GPU에서 어떤 성능 특성을 보이는지 분석하는 연구입니다. 단일 model kernel이 아니라 end-to-end pipeline의 병목을 보는 것이 핵심입니다.

상세 독해: Scientific AI workload는 chat LLM과 다릅니다. Protein design은 모델 inference, sampling, scoring, relaxation, post-processing, orchestration이 함께 움직입니다. GPU utilization은 한 모델의 throughput보다 pipeline dependency, memory footprint, batch structure에 좌우될 수 있습니다.

프로젝트 연결: AI datacenter power가 모두 LLM output token에 쓰이지 않습니다. Scientific AI workload share를 분리해야 model-owner token capacity를 과대평가하지 않습니다.

## 2025

### LLMServingSim2.0: A Unified Simulator for Heterogeneous Hardware and Serving Techniques in LLM Infrastructure

Source: https://jongse-park.github.io/publications/

Abstract 의역 독해: LLM infrastructure를 heterogeneous hardware와 serving techniques가 결합된 system으로 평가하는 simulator 논문입니다. CAL 형식의 짧은 논문으로 LLMServingSim 2.0의 핵심 방향을 압축합니다.

상세 독해: 하드웨어만 빠르다고 production serving이 빠른 것은 아닙니다. Serving scheduler, batch policy, memory placement, parallelism, SLO target이 effective throughput을 바꿉니다. 이 논문은 이런 요소를 통합 simulator로 평가해야 한다는 문제의식을 담고 있습니다.

프로젝트 연결: InferenceX나 public benchmark를 capacity model에 넣을 때 benchmark와 production 사이의 simulation evidence layer를 둘 근거가 됩니다.

### Pimba: A Processing-in-Memory Acceleration for Post-Transformer Large Language Model Serving

Source: https://jongse-park.github.io/files/paper/2025-micro-pimba.pdf

Abstract 의역 독해: Transformer 이후의 LLM 구조, 예를 들어 SSM, linear attention, recurrent model을 serving할 때도 memory bandwidth 병목이 남는다는 점을 다룹니다. PIM과 MX quantization을 결합해 state update와 attention-like 연산을 가속합니다.

상세 독해: Post-transformer 모델은 KV cache 문제를 줄일 수 있지만 memory pressure를 없애지는 않습니다. State update, recurrent state, linear attention은 다른 형태의 memory-bound operation을 만듭니다. Pimba는 PIM을 이용해 memory 근처에서 연산을 수행하고, quantization으로 memory footprint를 줄입니다.

프로젝트 연결: 2026-2030 forecast에서 transformer-only 가정을 피해야 합니다. Model architecture sensitivity와 PIM adoption scenario가 필요합니다.

### PyTorchSim: A Comprehensive, Fast, and Accurate NPU Simulation Framework

Source: https://jongse-park.github.io/files/paper/2025-micro-pytorchsim.pdf

Abstract 의역 독해: PyTorch 2, MLIR/LLVM, RISC-V 기반 ISA, tile-level simulation을 결합해 NPU를 빠르고 정확하게 평가하는 framework입니다. Purpose-built accelerator를 검증하기 위한 simulation methodology입니다.

상세 독해: NPU/ASIC 설계는 실제 silicon이 나오기 전에 수많은 design choice를 평가해야 합니다. Instruction-level simulation은 정확하지만 느리고, coarse simulation은 빠르지만 부정확할 수 있습니다. PyTorchSim은 model graph에서 compiler lowering, ISA, memory/interconnect timing까지 연결해 design space를 탐색합니다.

프로젝트 연결: TPU, Trainium, Maia, MTIA, LPU 같은 purpose-built accelerator의 efficiency claim을 평가할 때 simulation fidelity 기준이 필요합니다.

### Deja Vu: Efficient Video-Language Query Engine with Learning-based Inter-Frame Computation Reuse

Source: https://jongse-park.github.io/files/paper/2025-vldb-dejavu.pdf

Abstract 의역 독해: Video-language query에서 frame마다 반복되는 visual embedding 계산을 줄이기 위해 inter-frame computation reuse를 학습하는 system입니다. FLOP 절감이 실제 GPU speedup이 되도록 memory-compute compaction을 결합합니다.

상세 독해: VideoLM workload는 output text token보다 훨씬 많은 visual processing을 필요로 할 수 있습니다. 긴 영상에서 수천 frame을 처리하면 ViT embedding 비용이 커집니다. Deja Vu는 인접 frame의 유사성을 이용해 계산을 재사용합니다.

프로젝트 연결: Multimodal AI demand를 text output token으로만 보면 visual embedding compute를 놓칩니다. Video ingestion과 embedding generation을 별도 workload bucket으로 분리해야 합니다.

### Oaken: Fast and Efficient LLM Serving with Online-Offline Hybrid KV Cache Quantization

Source: https://jongse-park.github.io/files/paper/2025-isca-oaken.pdf

Abstract 의역 독해: LLM serving에서 KV cache가 HBM capacity와 bandwidth를 압박하는 문제를 hybrid quantization으로 완화하는 논문입니다. Offline threshold와 online scaling, hardware support를 결합해 accuracy loss를 작게 유지하면서 serving throughput을 높이려 합니다.

상세 독해: LLM generation 단계에서는 이전 token들의 key/value activation을 계속 읽어야 합니다. 긴 context와 큰 batch는 KV cache를 크게 만들고, HBM을 많이 차지합니다. 단순 quantization은 outlier 처리 비용과 accuracy 문제가 있습니다. Oaken은 offline/online을 나눠 outlier와 scale을 다루고, hardware module을 통해 실제 throughput 향상으로 연결합니다.

프로젝트 연결: `tokens/sec/MW`에는 context length, KV cache bitwidth, HBM GB, HBM bandwidth sensitivity가 필요합니다. HBM 수급과 token capacity를 연결하는 핵심 논문입니다.

### MixDiT: Accelerating Image Diffusion Transformer Inference with Mixed-Precision MX Quantization

Source: https://jongse-park.github.io/files/paper/2025-cal-mixdit.pdf

Abstract 의역 독해: Image Diffusion Transformer inference를 mixed-precision MX quantization으로 가속하는 논문입니다. 이미지 품질 손실을 줄이면서 반복 denoising 연산의 latency를 낮추는 것이 목표입니다.

상세 독해: Diffusion model은 여러 step을 반복해 이미지를 생성합니다. Text LLM decode와 다른 구조이며, GEMM-heavy하고 quality metric에 민감합니다. MixDiT는 중요한 outlier에는 높은 precision을 유지하고 나머지는 낮은 precision으로 처리합니다.

프로젝트 연결: Image generation workload는 output token이 아니라 image/sec, diffusion step, resolution, quality target 단위로 봐야 합니다.

## 2024

### LLMServingSim: A HW/SW Co-Simulation Infrastructure for LLM Inference Serving at Scale

Source: https://jongse-park.github.io/files/paper/2024-iiswc-llmservingsim.pdf

Abstract 의역 독해: LLM inference serving을 hardware/software co-simulation으로 빠르게 평가하는 infrastructure입니다. Autoregressive decoding의 dynamic behavior와 decoder block 반복성을 이용해 기존 simulator보다 빠르게 serving behavior를 추정합니다.

상세 독해: LLM serving은 request마다 sequence length가 달라지고, generation이 token-by-token으로 진행됩니다. 기존 accelerator simulator는 정확하지만 너무 느려 serving trace 전체를 평가하기 어렵습니다. LLMServingSim은 반복되는 decoder block과 iteration pattern을 활용해 simulation을 가속합니다. 실제 GPU serving behavior와 가까운 결과를 목표로 합니다.

프로젝트 연결: Public benchmark를 production capacity로 변환하는 데 필요한 핵심 methodology입니다. `commercial_workload_fit_factor`를 LLMServingSim식 serving realism factor로 바꿀 수 있습니다.

### Accelerating String-key Learned Index Structures via Memoization-based Incremental Training

Source: https://jongse-park.github.io/publications/

Abstract 의역 독해: String-key learned index를 memoization과 incremental training으로 더 빠르게 만드는 database systems 연구입니다.

상세 독해: LLM serving과 직접 관련은 낮지만, learned systems와 data infrastructure 관점에서 중요합니다. Retrieval, RAG, vector DB, indexing workload는 AI application stack에서 점점 커지고 있습니다.

프로젝트 연결: AI serving stack에는 model inference 외에도 retrieval/indexing/storage 비용이 있습니다.

### DaCapo: Accelerating Continuous Learning in Autonomous Systems for Video Analytics

Source: https://jongse-park.github.io/files/paper/2024-isca-dacapo.pdf

Abstract 의역 독해: Autonomous video analytics에서 inference, labeling, retraining을 함께 수행하는 continuous learning system을 가속하는 논문입니다. Low-power edge 환경에서 accuracy와 adaptation을 유지하는 것이 핵심입니다.

상세 독해: 자율 시스템은 환경 변화 때문에 모델을 계속 업데이트해야 합니다. 단순 inference만으로 충분하지 않고 teacher labeling, student retraining, drift adaptation이 필요합니다. DaCapo는 precision-flexible, spatially partitionable accelerator와 resource allocation을 통해 이 과정을 효율화합니다.

프로젝트 연결: Training과 inference의 경계가 흐려지는 continuous learning workload를 별도 category로 둘 수 있습니다.

### LVS: A Learned Video Storage for Fast and Efficient Video Understanding

Source: https://jongse-park.github.io/publications/

Abstract 의역 독해: Video understanding을 빠르고 효율적으로 만들기 위해 storage 자체를 learned 방식으로 설계하는 연구입니다.

상세 독해: Video AI는 모델 inference보다 data access와 storage layout이 병목이 될 수 있습니다. 어떤 frame과 feature를 어떻게 저장하고 꺼내는지가 overall performance를 결정합니다.

프로젝트 연결: Multimodal AI는 GPU뿐 아니라 storage, networking, memory hierarchy 수요를 키웁니다.

### NeuPIMs: NPU-PIM Heterogeneous Acceleration for Batched LLM Inferencing

Source: https://jongse-park.github.io/files/paper/2024-asplos-neupims.pdf

Abstract 의역 독해: Batched LLM inference에서 GEMM-heavy 연산은 NPU가, GEMV-heavy attention 연산은 PIM이 유리하다는 관찰을 바탕으로 NPU-PIM heterogeneous acceleration을 제안합니다.

상세 독해: LLM decoder block 안에서도 연산 성격이 다릅니다. QKV generation과 FFN은 dense matrix multiplication이 많아 NPU가 적합합니다. Attention의 일부는 memory bandwidth 중심의 GEMV가 되어 PIM이 유리합니다. NeuPIMs는 dual row buffer와 sub-batch interleaving으로 NPU와 PIM이 동시에 일하도록 설계합니다.

프로젝트 연결: GPU/HBM/PIM 수요를 workload phase별로 나눠야 합니다. PIM은 GPU 대체재가 아니라 decode/attention memory bottleneck 보완재로 봐야 합니다.

### Tandem Processor: Grappling with Emerging Operators in Neural Networks

Source: https://jongse-park.github.io/publications/

Abstract 의역 독해: Neural network에서 새롭게 등장하는 operator들을 기존 accelerator가 잘 처리하지 못하는 문제를 다룹니다.

상세 독해: AI 모델은 계속 변합니다. Transformer, MoE, SSM, sparse operator, custom activation 등이 등장하면 fixed-function accelerator가 금방 낡을 수 있습니다. Tandem Processor는 emerging operators에 대응하는 architecture 문제를 다룹니다.

프로젝트 연결: ASIC efficiency uplift에는 operator drift risk를 반영해야 합니다.

### ONNXim: A Fast, Cycle-level Multi-core NPU Simulator

Source: https://jongse-park.github.io/files/paper/2024-cal-onnxim.pdf

Abstract 의역 독해: ONNX graph를 입력으로 받아 multi-core NPU를 cycle-level로 빠르게 시뮬레이션하는 framework입니다. Multi-tenancy, DRAM/NoC contention, dynamic shape를 고려합니다.

상세 독해: NPU performance는 compute core만으로 결정되지 않습니다. 여러 model이 동시에 실행되면 DRAM과 NoC에서 contention이 생깁니다. ONNXim은 model graph level에서 이런 bottleneck을 빠르게 평가합니다.

프로젝트 연결: Purpose-built accelerator의 capacity를 계산할 때 multi-tenancy와 memory/interconnect contention을 반영해야 합니다.

### LPU: A Latency-optimized and Highly Scalable Processor for Large Language Model Inference

Source: https://jongse-park.github.io/files/paper/2024-ieee_micro-lpu.pdf

Abstract 의역 독해: LLM inference의 latency와 scalability를 목표로 하는 LPU processor 논문입니다. Memory bandwidth utilization과 multi-device synchronization이 중요합니다.

상세 독해: LLM generation은 작은 vector input으로 큰 weight를 반복적으로 읽는 memory-bound 성격을 가집니다. LPU는 GPU보다 LLM inference에 특화된 dataflow와 synchronization 구조를 통해 latency와 energy efficiency를 개선하려는 ASIC입니다.

프로젝트 연결: Purpose-built accelerator가 GPU 대비 얼마나 효율적일지 판단하는 reference입니다. 단, model size, context length, software maturity에 따라 uplift가 달라집니다.

### Cerberus: Triple Mode Acceleration of Sparse Matrix and Vector Multiplication

Source: https://jongse-park.github.io/publications/

Abstract 의역 독해: Sparse matrix/vector multiplication을 여러 mode로 가속하는 architecture 연구입니다.

상세 독해: Sparse workload는 dense GEMM과 달리 memory access가 불규칙하고 utilization이 낮아질 수 있습니다. MoE, graph, retrieval, scientific AI에서 sparse computation이 중요해질 수 있습니다.

프로젝트 연결: MoE sparsity를 단순 efficiency upside로 두면 안 됩니다. Sparse routing과 memory movement overhead를 봐야 합니다.

## 2023

### Bit Fusion: Bit-Level Dynamically Composable Architecture for Accelerating Deep Neural Network

Source: https://jongse-park.github.io/publications/

Abstract 의역 독해: Bit-level에서 precision을 동적으로 조합해 DNN acceleration 효율을 높이는 architecture입니다. 2023 retrospective 선정은 이 연구 방향의 장기적 중요성을 보여줍니다.

상세 독해: AI workload는 항상 같은 precision을 필요로 하지 않습니다. 일부 layer나 value는 낮은 precision으로 충분하고, 일부는 높은 precision이 필요합니다. Bit Fusion은 hardware가 bitwidth를 유연하게 조합하도록 해 efficiency를 높입니다.

프로젝트 연결: FP8, FP4, INT4, MX adoption은 tokens/sec/MW와 energy efficiency를 바꿉니다.

### General-Purpose Code Acceleration with Limited-Precision Analog Computation

Source: https://jongse-park.github.io/publications/

Abstract 의역 독해: Limited-precision analog computation으로 general-purpose code를 가속하는 과거 연구의 retrospective입니다.

상세 독해: Approximate/analog computation은 정확도를 조금 희생하거나 제한된 precision을 활용해 에너지 효율을 높이는 방향입니다. AI accelerator efficiency의 장기 trajectory를 이해하는 데 배경이 됩니다.

프로젝트 연결: 장기 efficiency upside를 digital GPU scaling만으로 보지 않고 analog/approximate computing 가능성까지 열어둘 수 있습니다.

### Hardware Hardened Sandbox Enclaves for Trusted Serverless Computing

Source: https://jongse-park.github.io/publications/

Abstract 의역 독해: Serverless computing에서 hardware-hardened sandbox enclave로 trusted execution을 지원하는 연구입니다.

상세 독해: Multi-tenant cloud에서는 isolation과 security가 중요합니다. Hardware enclave는 보안을 제공하지만 overhead를 만들 수 있습니다. AI serving도 multi-tenant enterprise workload가 커질수록 비슷한 문제가 생깁니다.

프로젝트 연결: Confidential AI와 secure serving은 latency/utilization overhead를 만들 수 있습니다.

### FlexBlock: A Flexible DNN Training Accelerator with Multi-Mode Block Floating Point Support

Source: https://jongse-park.github.io/publications/

Abstract 의역 독해: Multi-mode block floating point를 지원하는 flexible DNN training accelerator입니다.

상세 독해: Training은 inference와 다르게 gradient, optimizer state, activation 저장이 필요합니다. Precision format은 training stability와 efficiency를 동시에 좌우합니다. FlexBlock은 block floating point를 여러 mode로 지원해 효율과 유연성을 확보하려는 방향입니다.

프로젝트 연결: Training power efficiency는 inference와 별도 logic으로 다뤄야 합니다.

### HAMMER: Hardware-friendly Approximate Computing for Self-attention with Mean-redistribution and Linearization

Source: https://jongse-park.github.io/publications/

Abstract 의역 독해: Self-attention을 hardware-friendly하게 근사해 transformer 계산 비용을 줄이는 연구입니다.

상세 독해: Attention은 transformer의 핵심이지만 long-context에서 비용이 커집니다. Approximation은 계산량을 줄일 수 있지만 accuracy와 model quality risk가 있습니다. HAMMER는 attention approximation을 hardware 관점에서 실용적으로 만드는 방향입니다.

프로젝트 연결: Long-context efficiency upside는 attention approximation adoption 여부에 따라 달라질 수 있습니다.

## 2022

### Tunable Memory Protection for Secure Neural Processing Units

Source: https://jongse-park.github.io/publications/

Abstract 의역 독해: Secure NPU를 위해 memory protection 수준을 조절할 수 있게 하는 연구입니다.

상세 독해: Accelerator security는 memory protection과 performance overhead 사이의 균형 문제입니다. 보안을 강화하면 metadata, checking, encryption overhead가 생길 수 있습니다.

프로젝트 연결: Enterprise confidential AI에서 security overhead를 capacity haircut으로 볼 수 있습니다.

### Supporting Dynamic Translation Granularity for Hybrid Memory Systems

Source: https://jongse-park.github.io/publications/

Abstract 의역 독해: Hybrid memory system에서 address translation granularity를 동적으로 조절하는 연구입니다.

상세 독해: HBM, DDR, CXL 같은 memory tier가 섞이면 page size와 address translation 정책이 성능에 영향을 줍니다. Large page는 overhead를 줄일 수 있지만 fragmentation 문제가 있고, small page는 유연하지만 metadata/translation cost가 큽니다.

프로젝트 연결: CXL/HBM tiering을 모델링할 때 capacity뿐 아니라 translation overhead도 봐야 합니다.

### CoVA: Exploiting Compressed-Domain Analysis to Accelerate Video Analytics

Source: https://jongse-park.github.io/publications/

Abstract 의역 독해: Video를 완전히 decode하지 않고 compressed-domain 정보를 활용해 video analytics를 가속하는 연구입니다.

상세 독해: Video workload에서는 decoding과 data movement가 큰 비용입니다. CoVA는 압축된 표현 안에 이미 있는 정보를 활용해 불필요한 decode/compute를 줄이려는 접근입니다.

프로젝트 연결: Video AI capacity에는 codec, storage, preprocessing 비용이 포함되어야 합니다.

### Serving Heterogeneous Machine Learning Models on Multi-GPU Servers with Spatio-Temporal Sharing

Source: https://jongse-park.github.io/files/paper/2022-atc-gpulet.pdf

Abstract 의역 독해: Multi-GPU server에서 heterogeneous ML model을 SLO 안에서 serving하기 위해 GPU를 spatial/temporal하게 공유하는 scheduler 연구입니다. GPUlet이라는 virtual GPU slice 개념이 핵심입니다.

상세 독해: 여러 model을 같은 GPU server에서 serving하면 각 model의 latency, batch behavior, resource need가 다릅니다. GPUlet은 GPU resource를 나눠 spatial sharing을 가능하게 하고, scheduler는 batch size와 temporal sharing을 함께 탐색합니다. Interference 예측과 SLO 만족이 중요합니다.

프로젝트 연결: Production utilization은 단순 GPU 사용률이 아니라 SLO-constrained schedulable utilization입니다.

### TNPU: Supporting Trusted Execution with Tree-less Integrity Protection for Neural Processing Unit

Source: https://jongse-park.github.io/publications/

Abstract 의역 독해: NPU에서 trusted execution을 지원하기 위한 integrity protection architecture입니다.

상세 독해: NPU가 민감한 model과 data를 처리할 때 integrity protection이 필요합니다. 보안 구조는 memory overhead와 performance overhead를 만들 수 있습니다.

프로젝트 연결: Secure AI serving scenario에서 tokens/sec/MW haircut을 고려할 수 있습니다.

### Yin-Yang: Programming Abstraction for Cross-Domain Multi-Acceleration

Source: https://jongse-park.github.io/publications/

Abstract 의역 독해: 여러 domain accelerator를 함께 쓰기 위한 programming abstraction 연구입니다.

상세 독해: GPU, NPU, DSP, FPGA, ASIC이 섞이면 programmer와 runtime이 복잡해집니다. 좋은 abstraction이 없으면 hardware는 있어도 실제 application이 효율적으로 쓰기 어렵습니다.

프로젝트 연결: Purpose-built accelerator share가 높아져도 software maturity가 낮으면 effective capacity가 낮습니다.

## 2021

### Common Counters: Compressed Encryption Counters for Secure GPU Memory

Source: https://jongse-park.github.io/publications/

Abstract 의역 독해: Secure GPU memory에서 encryption counter overhead를 줄이는 연구입니다.

상세 독해: GPU memory를 암호화하면 counter metadata가 필요하고, 이것이 memory capacity와 bandwidth에 overhead를 줄 수 있습니다. Common Counters는 counter를 압축하거나 공유해 overhead를 줄이는 방향으로 이해할 수 있습니다.

프로젝트 연결: Confidential GPU memory가 보편화되면 HBM effective capacity와 bandwidth가 줄어들 수 있습니다.

### SLO-aware Inference Scheduler for Heterogeneous Processors in Edge Platforms

Source: https://jongse-park.github.io/files/paper/2021-taco-edgeduler.pdf

Abstract 의역 독해: CPU, GPU, DSP 등 heterogeneous edge processor에서 ML inference request를 SLO에 맞춰 scheduling하는 연구입니다. Model profiling과 layer-level slicing을 활용합니다.

상세 독해: Edge platform은 resource가 제한되어 있고, processor마다 잘하는 workload가 다릅니다. Scheduler는 model별 latency/energy profile을 알고 있어야 하며, non-preemptive accelerator에서 긴 작업이 다른 요청을 막지 않도록 slicing이 필요합니다. 이 관점은 datacenter LLM serving에도 이어집니다.

프로젝트 연결: AI capacity는 raw throughput이 아니라 SLO를 만족하는 throughput입니다. TTFT/TPOT와 utilization을 함께 봐야 합니다.
