# MixDiT: Accelerating Image Diffusion Transformer Inference with Mixed-Precision MX Quantization

## Original English Notes

Venue: IEEE Computer Architecture Letters, 2025  
Source: https://jongse-park.github.io/files/paper/2025-cal-mixdit.pdf

MixDiT accelerates Diffusion Transformer inference using mixed-precision MX quantization. It applies higher precision selectively to magnitude-based outliers and uses accelerator support for precision-flexible multiplication and MX conversion.

## 한글 번역 요약

MixDiT는 image generation에서 쓰이는 Diffusion Transformer의 반복 inference를 MX mixed-precision quantization으로 가속한다. text LLM과 달리 diffusion workload는 반복 denoising과 GEMM-heavy 연산이 중요하다.

## 박종세 교수 전문성 관점

박 교수님은 LLM뿐 아니라 diffusion transformer까지 포함해 transformer 계열 workload 전반의 precision/hardware co-design을 연구한다.

## 내 프로젝트 연결점

AI demand를 text token capacity만으로 계산하면 image generation workload를 과소평가할 수 있다. 이미지 생성은 output token과 다른 단위의 demand bucket, 예를 들어 image/sec/MW 또는 diffusion step/sec/MW가 필요하다.

