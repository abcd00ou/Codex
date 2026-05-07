# Agentic Coding Notes

This reference captures the workflow philosophy behind the `agentic-coding-workflow` skill.

## Core Observations

LLM coding agents changed the balance from mostly manual coding plus autocomplete to mostly agent-directed coding plus human edits, review, and touchups. The useful primitive is no longer only line-level completion; it is large “code actions” directed in natural language.

This creates a workflow where the engineer programs partly in English: describing what should exist, what success looks like, and what constraints matter. This can feel strange, but the leverage is too useful to ignore.

## IDEs and Agent Fallibility

The current “no IDE needed” and “agent swarm” hype is too strong. Models still make mistakes. The mistakes are less often syntax errors and more often conceptual errors similar to a hasty junior engineer:

- wrong assumptions made on the user’s behalf
- insufficient clarification
- poor confusion management
- missing tradeoffs
- too much agreement
- overcomplicated APIs and abstractions
- dead code left behind
- incidental edits to unrelated comments or code

The recommended posture is to keep a large IDE or review surface open and watch the agent closely, kindly but skeptically.

## Tenacity

Agents have unusual stamina. They can keep trying, debugging, and looping long after a person would pause. This stamina is a real productivity primitive, but it needs guardrails and success criteria.

## Speedup vs Expansion

The speedup is not only doing the same work faster. The larger change is expansion:

- coding things that previously were not worth the effort
- approaching code outside one’s direct expertise
- lowering the cost of exploration

## Leverage Pattern

Agents are strongest when given goals and success criteria:

```text
Write the naive correct version -> test it -> optimize while preserving correctness.
```

Prefer declarative prompts: tell the agent what must be true at the end, not every mechanical step.

## Fun and Atrophy

Agentic coding can make programming more fun because fill-in-the-blanks drudgery drops away and creative direction remains. But manual code generation skill may atrophy. Reading and discriminating code remain essential and should be practiced deliberately.

## Risks

Expect a “slop” wave: more generated code, generated content, weak research, and productivity theater. Counter this with evidence, tests, reviews, and explicit confidence labels.

## Open Questions

- Does the ratio between average and maximum engineer productivity grow?
- Do generalists outperform specialists when LLMs cover more micro-level fill-in-the-blanks?
- What will future LLM coding feel like: strategy game, factory game, or musical performance?
- How much of society is bottlenecked by digital knowledge work?

## TLDR

LLM coding agents crossed a coherence threshold around late 2025. The intelligence now feels ahead of the surrounding tools, workflows, and organizational processes. The best response is not blind delegation, but a new workflow: natural-language direction, lightweight planning, tight verification, explicit evidence, and careful simplification.
