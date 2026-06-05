# Cerberus: Triple Mode Acceleration of Sparse Matrix and Vector Multiplication

## Original English Notes

Venue: IEEE Transactions on Architecture and Code Optimization, 2024  
Source: https://jongse-park.github.io/publications/

Cerberus accelerates sparse matrix and vector multiplication using a triple-mode approach.

## 한글 번역 요약

Cerberus는 sparse matrix/vector multiplication을 가속하는 architecture 연구다. sparse computation은 MoE, graph, retrieval, scientific workload 등과 연결될 수 있다.

## 박종세 교수 전문성 관점

박 교수님의 연구는 dense transformer뿐 아니라 sparse computation과 irregular workload까지 포함한다.

## 내 프로젝트 연결점

MoE sparsity를 efficiency upside로 단순 처리하면 routing, memory movement, sparse kernel overhead를 놓칠 수 있다. sparse acceleration 연구는 MoE efficiency 가정의 근거와 한계를 잡는 데 도움이 된다.

