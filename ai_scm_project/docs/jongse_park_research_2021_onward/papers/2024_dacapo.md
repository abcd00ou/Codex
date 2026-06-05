# DaCapo: Accelerating Continuous Learning in Autonomous Systems for Video Analytics

## Original English Notes

Venue: ISCA 2024, Distinguished Artifact Award  
Source: https://jongse-park.github.io/files/paper/2024-isca-dacapo.pdf

DaCapo accelerates continuous learning for autonomous video analytics. It considers inference, labeling, and retraining together on constrained autonomous systems, using a spatially partitionable and precision-flexible accelerator plus spatiotemporal resource allocation.

## 한글 번역 요약

DaCapo는 자율 시스템에서 video analytics를 계속 학습시키는 문제를 다룬다. lightweight student inference, teacher labeling, retraining이 동시에 필요하고, GPU 같은 고전력 장비를 쓰기 어렵다는 점이 핵심이다. 공간적으로 나눌 수 있고 precision을 유연하게 바꿀 수 있는 accelerator와 resource allocation을 제안한다.

## 박종세 교수 전문성 관점

박 교수님은 AI workload를 inference 하나로 보지 않고, labeling, retraining, drift adaptation까지 포함한 full lifecycle system으로 본다.

## 내 프로젝트 연결점

향후 AI demand는 training/inference로 깔끔하게 나뉘지 않을 수 있다. edge/autonomous AI는 inference 중에도 labeling/retraining을 수행하므로, `training_power_share`와 `inference_power_share` 사이에 continuous learning category가 필요할 수 있다.

