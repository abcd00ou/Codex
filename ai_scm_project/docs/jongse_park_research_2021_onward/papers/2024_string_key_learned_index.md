# Accelerating String-key Learned Index Structures via Memoization-based Incremental Training

## Original English Notes

Venue: VLDB 2024  
Source: https://jongse-park.github.io/publications/

This paper accelerates string-key learned index structures using memoization-based incremental training.

## 한글 번역 요약

이 논문은 learned index를 string-key 환경에서 더 빠르게 학습하고 업데이트하는 database systems 연구다. LLM inference capacity와 직접 연결되지는 않지만, indexing과 incremental training이라는 systems 관점이 있다.

## 박종세 교수 전문성 관점

박 교수님 연구에는 AI accelerator뿐 아니라 database/storage system과 learned systems도 포함된다.

## 내 프로젝트 연결점

RAG, vector DB, retrieval-heavy AI application은 model inference 외에도 indexing/storage/query cost를 만든다. 이 논문은 retrieval infrastructure가 AI serving stack의 일부라는 관점에서 연결된다.

