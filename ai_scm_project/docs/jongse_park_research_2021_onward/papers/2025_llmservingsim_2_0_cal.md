# LLMServingSim2.0: A Unified Simulator for Heterogeneous Hardware and Serving Techniques in LLM Infrastructure

## Source and Scope

Venue: IEEE Computer Architecture Letters 2025  
Source: https://jongse-park.github.io/publications/  
Copyright note: This note is a paraphrased research reading, not a reproduction of the original paper.

## Detailed English Reading

This CAL paper is the compact journal-letter version of the LLMServingSim 2.0 direction. It frames LLM infrastructure as a joint problem of heterogeneous hardware and serving techniques. The important point is that hardware performance cannot be interpreted without the serving algorithm around it. Batching policy, parallelism, memory hierarchy, and workload trace all change the effective token throughput.

Compared with a full conference paper, a CAL paper is shorter, but the title and project context make the research intent clear. It formalizes a simulator that can compare hardware and software serving methods under a unified framework. This is exactly the missing layer between benchmark dashboards and real production capacity planning.

## 상세 한글 독해 및 번역 요약

이 논문은 LLMServingSim 2.0 방향을 짧은 CAL 형식으로 정리한 논문이다. 핵심은 LLM infrastructure를 heterogeneous hardware와 serving technique이 결합된 문제로 본다는 점이다. GPU, CPU, CXL, PIM 같은 하드웨어가 아무리 좋아도 batching, scheduler, parallelism, memory placement가 맞지 않으면 user-facing throughput은 낮아진다.

따라서 이 논문은 public benchmark와 production capacity 사이에 simulation framework가 필요하다는 메시지를 준다. 특히 LLM capacity forecast에서 hardware generation만 바꾸는 것은 부족하고 serving software의 효율 변화를 같이 봐야 한다.

## 박종세 교수 전문성 관점

박 교수님은 LLM serving을 HW/SW co-design과 simulator framework로 다루는 전문가다.

## 내 프로젝트와의 연결점

내 프로젝트의 benchmark ingestion layer에 `simulator-calibrated`라는 evidence tier를 추가할 근거가 된다. InferenceX 같은 public number를 그대로 쓰지 않고 serving model로 교정해야 한다.
