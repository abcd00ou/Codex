# Neo: Real-Time On-Device 3D Gaussian Splatting with Reuse-and-Update Sorting Acceleration

## Source and Scope

Venue: ASPLOS 2026  
Source: https://jongse-park.github.io/publications/  
Copyright note: This note is a paraphrased research reading, not a reproduction of the original paper.

## Detailed English Reading

Neo targets real-time on-device 3D Gaussian Splatting. 3D Gaussian Splatting is a rendering and scene representation technique that has become important for real-time 3D perception and generation. The title highlights reuse-and-update sorting acceleration, suggesting that a key bottleneck is not only arithmetic but also ordering, data reuse, and dynamic update behavior.

The systems significance is that AI workloads are expanding beyond text tokens and image pixels into spatial, interactive, and on-device computation. These workloads have different latency and energy constraints from datacenter LLM serving. They also require tight integration between graphics-like data structures, neural representations, memory movement, and possibly sensor-driven updates.

For Professor Park’s research profile, this paper shows a move into real-time embodied or spatial AI systems. It complements the LLM serving work by covering another frontier of AI compute demand.

## 상세 한글 독해 및 번역 요약

Neo는 온디바이스에서 3D Gaussian Splatting을 실시간으로 처리하기 위한 acceleration 연구다. 3D Gaussian Splatting은 3D scene을 표현하고 rendering하는 방식으로, AR, robotics, spatial computing, interactive AI에서 중요해질 수 있다.

제목에 reuse-and-update sorting acceleration이 들어간다는 점이 중요하다. 이는 단순히 많은 FLOPS를 쓰는 문제가 아니라, 3D 요소의 정렬, 재사용, 업데이트, memory movement가 병목이 될 수 있음을 의미한다. 즉, LLM처럼 token을 생성하는 workload와는 다른 성격의 compute demand다.

이 논문은 박종세 교수님의 연구가 datacenter LLM serving에서 on-device spatial AI까지 확장된다는 점을 보여준다. 앞으로 AI 반도체 수요는 text inference accelerator뿐 아니라 3D/AR/robotics용 low-latency accelerator로도 확대될 수 있다.

## 박종세 교수 전문성 관점

박 교수님은 real-time on-device AI와 spatial computing workload까지 다룬다. 이는 architecture 연구의 응용 범위가 넓다는 신호다.

## 내 프로젝트와의 연결점

AI SCM 모델에서 future AI demand를 token generation만으로 설명하면 spatial AI 수요를 놓친다. edge NPU, mobile accelerator, memory bandwidth, graphics/AI hybrid pipeline을 별도 수요 축으로 봐야 한다.
