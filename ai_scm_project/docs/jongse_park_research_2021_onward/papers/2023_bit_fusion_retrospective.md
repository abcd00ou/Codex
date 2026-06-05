# Bit Fusion: Bit-Level Dynamically Composable Architecture for Accelerating Deep Neural Network

## Original English Notes

Venue: ISCA 2023 Retrospective  
Source: https://jongse-park.github.io/publications/

This is a retrospective recognition of the earlier Bit Fusion work. The key idea is bit-level dynamic composability for DNN acceleration.

## 한글 번역 요약

Bit Fusion은 precision을 workload에 맞춰 동적으로 조합하는 accelerator architecture다. 2023년 ISCA retrospective에 선정되었다는 점은 precision-flexible architecture가 장기적으로 중요한 연구 방향임을 보여준다.

## 박종세 교수 전문성 관점

박 교수님은 오래전부터 precision flexibility와 accelerator composability를 연구해 왔다.

## 내 프로젝트 연결점

FP8, FP4, INT4, MX 같은 precision 변화는 GPU/ASIC throughput과 energy efficiency를 크게 바꾼다. GPU 세대별 tokens/sec/MW 가정에는 precision adoption sensitivity가 필요하다.

