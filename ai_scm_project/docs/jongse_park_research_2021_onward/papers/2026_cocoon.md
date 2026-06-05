# Cocoon: A System Architecture for Differentially Private Training with Correlated Noises

## Original English Notes

Venue: OSDI 2026, to appear  
Source: https://jongse-park.github.io/publications/

This work targets differentially private training from a system architecture perspective. It is less directly about inference capacity, but it matters for the cost of secure or privacy-preserving AI training pipelines.

## 한글 번역 요약

이 논문은 correlated noise를 활용한 differential privacy training 시스템 아키텍처를 다룬다. inference serving보다는 학습 단계의 privacy, security, system overhead가 중심이다.

## 박종세 교수 전문성 관점

박 교수님의 연구 범위가 inference hardware에만 한정되지 않고, secure/privacy-preserving AI system architecture까지 포함함을 보여준다.

## 내 프로젝트 연결점

현재 프로젝트가 training power share와 inference power share를 나눌 때, privacy-preserving training은 일반 training보다 추가 연산과 시스템 overhead를 만들 수 있다. 상용 AI 기업이 privacy/security 요구가 높은 enterprise training을 확대하면 training-side power efficiency가 낮아질 수 있다.

