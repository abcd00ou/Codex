# LLMServingSim2.0: A Unified Simulator for Heterogeneous Hardware and Serving Techniques in LLM Infrastructure

## Original English Notes

Venue: IEEE Computer Architecture Letters, 2025  
Source: https://jongse-park.github.io/publications/

This is the CAL version of LLMServingSim 2.0. It frames LLM infrastructure as a serving-system problem involving heterogeneous hardware and multiple serving techniques.

## 한글 번역 요약

이 논문은 LLMServingSim 2.0의 compact version으로 볼 수 있다. LLM inference capacity를 GPU 한 장의 raw throughput이 아니라 serving techniques, hardware heterogeneity, memory tier, scheduling이 결합된 시스템 성능으로 본다.

## 박종세 교수 전문성 관점

박 교수님은 LLM serving simulator를 반복적으로 확장하며, 논문뿐 아니라 website/code artifact까지 공개하는 systems research 스타일을 갖고 있다.

## 내 프로젝트 연결점

`InferenceX` 같은 public benchmark를 capacity model에 넣을 때, 이 논문 계열은 "benchmark result", "simulated serving result", "production telemetry"를 구분해야 한다는 근거가 된다.

