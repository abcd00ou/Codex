# Revisiting Partial Tracing for Safe, Efficient, and Concurrent Garbage Collection in Unmanaged Languages

## Original English Notes

Venue: PLDI 2026, to appear  
Source: https://jongse-park.github.io/publications/

This paper revisits partial tracing for garbage collection in unmanaged languages, with emphasis on safety, efficiency, and concurrency.

## 한글 번역 요약

이 논문은 unmanaged language 환경에서 garbage collection을 더 안전하고 효율적이며 concurrent하게 만드는 partial tracing 기법을 재검토한다. AI hardware 논문은 아니지만 runtime, memory safety, concurrency라는 systems 연구 축에 해당한다.

## 박종세 교수 전문성 관점

박 교수님 연구가 computer architecture와 systems runtime 전반을 포괄한다는 점을 보여준다.

## 내 프로젝트 연결점

LLM serving runtime은 고성능 C++/CUDA/Rust/Python stack 위에서 돌아간다. memory safety나 runtime overhead가 직접적인 capacity driver는 아니지만, production serving reliability와 tail latency에는 영향을 줄 수 있다.

