# Interference-Aware DNN Serving on Heterogeneous Processors in Edge Systems

## Original English Notes

Venue: ICCD 2024  
Source: https://jongse-park.github.io/publications/

This work studies DNN serving on heterogeneous edge processors while accounting for interference among concurrent workloads.

## 한글 번역 요약

이 논문은 edge system에서 서로 다른 DNN workload가 동시에 실행될 때 생기는 간섭을 고려한 serving을 다룬다. 여러 processor와 workload가 섞이면 평균 latency만으로는 SLO를 설명하기 어렵다.

## 박종세 교수 전문성 관점

박 교수님의 scheduling 연구는 datacenter뿐 아니라 edge heterogeneous processor 환경까지 이어진다.

## 내 프로젝트 연결점

production inference utilization은 단순 평균 GPU utilization이 아니라 interference와 SLO를 만족하는 schedulable utilization이어야 한다. utilization sensitivity를 해석할 때 참고할 수 있다.

