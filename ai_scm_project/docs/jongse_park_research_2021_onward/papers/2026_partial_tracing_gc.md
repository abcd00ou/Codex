# Revisiting Partial Tracing for Safe, Efficient, and Concurrent Garbage Collection in Unmanaged Languages

## Source and Scope

Venue: PLDI 2026, to appear  
Source: https://jongse-park.github.io/publications/  
Copyright note: This note is a paraphrased research reading, not a reproduction of the original paper.

## Detailed English Reading

This PLDI paper revisits partial tracing for garbage collection in unmanaged languages. It is a programming-language and runtime systems paper rather than an AI accelerator paper. The technical problem is how to gain safety and concurrency benefits associated with tracing while working in environments that do not normally rely on managed runtimes.

The connection to the broader research profile is runtime efficiency under systems constraints. High-performance systems increasingly combine low-level languages, concurrency, and safety requirements. AI serving stacks also depend on complex low-level runtime components, although this paper is not specifically about LLM serving.

The important reading is that Professor Park’s work spans computer architecture, systems, and runtime safety. This breadth matters when evaluating production AI systems because end-to-end efficiency depends not only on accelerator kernels but also on runtime behavior, memory management, and concurrency.

## 상세 한글 독해 및 번역 요약

이 논문은 unmanaged language에서 partial tracing을 이용해 안전하고 효율적인 concurrent garbage collection을 가능하게 하는 연구다. AI 반도체나 LLM serving 논문은 아니지만, 시스템 런타임의 안전성과 효율을 다룬다는 점에서 박종세 교수님의 systems 연구 폭을 보여준다.

고성능 AI serving stack은 C++, CUDA, Python runtime, memory allocator, scheduler, RPC framework 등 여러 runtime layer 위에서 작동한다. 이런 환경에서 memory safety, concurrency, latency spike는 production stability와 tail latency에 영향을 줄 수 있다.

따라서 이 논문은 AI capacity 자체의 직접 근거라기보다는, 박 교수님이 low-level runtime과 architecture의 접점을 이해하는 연구자라는 점을 보여주는 자료다.

## 박종세 교수 전문성 관점

박 교수님은 accelerator architecture뿐 아니라 programming language/runtime systems에도 관여한다. 이는 end-to-end systems 관점의 강점이다.

## 내 프로젝트와의 연결점

내 프로젝트의 core model에는 직접 반영할 항목은 적다. 다만 production LLM serving의 tail latency와 stability를 논할 때 runtime overhead가 완전히 무시되는 것은 아니라는 보조 맥락이 된다.
