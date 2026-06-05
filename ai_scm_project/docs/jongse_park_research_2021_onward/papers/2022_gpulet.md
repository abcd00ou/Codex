# Serving Heterogeneous Machine Learning Models on Multi-GPU Servers with Spatio-Temporal Sharing

## Original English Notes

Venue: USENIX ATC 2022  
Source: https://jongse-park.github.io/files/paper/2022-atc-gpulet.pdf

This paper proposes GPUlets, virtual GPU resource slices, for serving heterogeneous ML models on multi-GPU servers. The scheduler searches across batch size, temporal sharing, and spatial sharing while satisfying SLO constraints and accounting for interference.

## 한글 번역 요약

이 논문은 multi-GPU server에서 여러 heterogeneous ML model을 SLO 내에서 serving하기 위한 scheduling framework다. GPU를 spatially partitioned virtual GPU, 즉 gpulet으로 나누고, batch size, temporal sharing, spatial sharing을 함께 탐색한다. concurrent model 간 interference도 고려한다.

## 박종세 교수 전문성 관점

박 교수님은 GPU serving capacity를 raw FLOPS가 아니라 SLO-constrained scheduling problem으로 본다.

## 내 프로젝트 연결점

`utilization`을 단순 평균으로 두면 production serving capacity를 잘못 볼 수 있다. SLO를 만족하는 throughput, interference-aware utilization, autoscaling overhead가 실제 tokens/sec/MW를 결정한다.

