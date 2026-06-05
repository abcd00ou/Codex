# Accelerator Polymorphism: Transcending Domain-Specific Architectures with Robotics

## Source and Scope

Venue: ISCA 2026, to appear  
Source: https://jongse-park.github.io/publications/  
Copyright note: This note is a paraphrased research reading, not a reproduction of the original paper.

## Detailed English Reading

The title points to a problem that is becoming central in AI hardware: domain-specific accelerators work well when the workload is stable, but robotics combines many changing kernels and control regimes. A robot workload can include perception, localization, mapping, planning, grasping, language-conditioned control, sensor fusion, and hard real-time deadlines. These workloads do not behave like a single datacenter transformer inference job. The likely thrust is that an accelerator should be polymorphic, meaning it can adapt its execution structure to multiple computational shapes without losing too much efficiency.

For the research landscape, this paper sits at the boundary between accelerator specialization and generality. The older AI hardware narrative rewarded narrow specialization. Robotics challenges that narrative because the useful computation shifts over time and depends on the physical environment. A system that is excellent for dense GEMM may struggle with sparse perception, graph-like planning, control loops, and synchronization-heavy pipelines. The paper therefore appears to ask how accelerator architectures can transcend a single domain-specific template.

Because the publication page marks the paper as to appear and no full paper was available from the listing at the time of this note, the reading is based on the title, venue, author context, and the broader pattern of the group’s work.

## 상세 한글 독해 및 번역 요약

이 논문은 아직 상세 본문이 공개되지 않은 to appear 논문이므로, 현재 파일은 원문 전문 해석이 아니라 제목과 연구 맥락 기반의 상세 독해다. 핵심은 로보틱스 workload가 기존 domain-specific accelerator의 한계를 드러낸다는 점이다. 로봇은 카메라와 센서 입력을 받아 perception을 수행하고, 공간을 이해하고, 행동을 계획하고, 제어를 실행하며, 때로는 language model이나 vision-language model과 연결된다. 이 과정은 하나의 규칙적인 행렬곱 workload가 아니라 여러 계산 패턴이 계속 바뀌는 시스템이다.

따라서 이 논문이 말하는 accelerator polymorphism은 한 가지 연산만 빠르게 하는 것이 아니라, 다양한 연산 형태에 맞춰 accelerator의 역할이나 구성이 바뀌는 능력으로 이해할 수 있다. AI 반도체가 LLM inference에만 최적화되어 있을 때는 tokens/sec/W가 좋아 보일 수 있지만, robotics/agentic workload에서는 latency, control-loop stability, irregular memory access, sensor fusion 같은 요소가 중요해진다.

요약하면 이 논문은 박종세 교수님의 연구가 LLM serving뿐 아니라 미래형 embodied AI workload까지 확장되고 있음을 보여준다.

## 박종세 교수 전문성 관점

박 교수님은 특정 모델 하나에 맞춘 accelerator가 아니라, 변화하는 AI workload에 대응하는 architecture design을 다룰 수 있는 연구자다. LLM, video, robotics, memory system, simulator를 모두 묶어 보는 full-stack computer architecture 전문성이 드러난다.

## 내 프로젝트와의 연결점

AI SCM 프로젝트에서 ASIC 효율을 높게 두는 가정은 workload가 안정적이라는 전제를 갖는다. 그러나 robotics, autonomous agent, multimodal interaction이 커지면 fixed-function accelerator의 효율은 낮아질 수 있다. 장기 GPU/ASIC mix에는 workload diversity penalty 또는 polymorphic accelerator premium이라는 변수를 둘 수 있다.
