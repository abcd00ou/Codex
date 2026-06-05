# MixDiT: Accelerating Image Diffusion Transformer Inference with Mixed-Precision MX Quantization

## Source and Scope

Venue: IEEE Computer Architecture Letters 2025  
Source: https://jongse-park.github.io/files/paper/2025-cal-mixdit.pdf  
Copyright note: This note is a paraphrased research reading, not a reproduction of the original paper.

## Detailed English Reading

MixDiT targets Diffusion Transformer inference for image generation. Diffusion models perform repeated denoising steps, and transformer-based diffusion models rely heavily on GEMM operations. The paper proposes mixed-precision MX quantization for activation tensors, keeping higher precision for magnitude-based outliers and using hardware support for precision-flexible multiplication and MX conversion.

The systems insight is that quantization must preserve output quality while translating into actual latency reduction. Diffusion workloads are sensitive to quality metrics, so simple aggressive quantization can be unacceptable. MixDiT uses mixed precision to protect important values while reducing cost elsewhere.

For AI infrastructure, this paper shows that image generation demand has a different performance profile from text generation. It is iterative, GEMM-heavy, and quality-sensitive in a different way from autoregressive token decode.

## 상세 한글 독해 및 번역 요약

MixDiT는 image Diffusion Transformer inference를 mixed-precision MX quantization으로 가속하는 논문이다. Diffusion model은 noise를 여러 step에 걸쳐 제거하며 이미지를 생성한다. Transformer 기반 diffusion은 반복적인 GEMM 연산이 많아서 latency가 길다.

논문은 activation tensor를 낮은 precision으로 줄이되, magnitude가 큰 outlier에는 더 높은 precision을 적용한다. 그리고 이런 mixed precision 연산이 실제 속도 향상으로 이어지도록 precision-flexible accelerator를 설계한다. 중요한 점은 FID 같은 품질 지표를 망가뜨리지 않으면서 speedup을 얻으려는 것이다.

이 논문은 text LLM token capacity와 image generation capacity가 서로 다른 workload라는 점을 보여준다.

## 박종세 교수 전문성 관점

박 교수님은 LLM뿐 아니라 diffusion transformer에서도 precision과 hardware co-design을 연구한다.

## 내 프로젝트와의 연결점

AI SCM 모델에 image generation demand bucket을 별도로 둘 수 있다. text output tokens/sec/MW만으로는 diffusion step, image resolution, quality target, batch pattern을 설명할 수 없다.
