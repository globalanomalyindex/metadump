# Identify the task, ladder it from discipline to specifics, and distill references

The manual workflow this skill automates went like this. Before prompting, the owner asked an agent to turn a style ("Apple's UI"), along with screenshots and sources, into a meta dump. The dump held brand-agnostic descriptions, numbers, cited sources, patterns noticed, UI and UX principles, tiered keywords and anti-keywords, and dos and don'ts. It let another agent understand, recreate and imagine the feel without copying anything. Builds up to 0.4.0 started at the artifact instead. Asked for a shopping component, they wrote about product cards and never wrote down what a UX or UI practitioner knows that applies. That knowledge lived in separate rule-based skills, or nowhere.

We decided that charting starts by **identifying the task**: what it is and the disciplines it belongs to. It then lays a **task ladder** from those disciplines down to this task's specifics (UX and UI design → e-commerce interfaces → product cards and carts → this component → its values). Every rung gets keywords, descriptors, principles, sources, and dos and don'ts. The top rungs get a **discipline primer**: named principles, laws, heuristics, standards and common mistakes, from the model's own knowledge and confirmed against sources. References are **distilled**: turned into brand-agnostic measurements, descriptions, patterns and principles, never copied. The ladder lives in `essence.task`, sections follow it top to bottom, and finalize warns when it's missing (`no_task_ladder`).

We rejected:
- relying on separate design or engineering skills for discipline knowledge, because they're hard-set rules outside the dump, they don't adapt to the task, and they don't exist for most disciplines;
- a fixed list of disciplines per domain, because the ladder has to fit the task (a REST endpoint, a short story and a carton have different top rungs);
- quoting references verbatim, because the point is understanding a feel without copying it.

## Consequences

- Every dump gets at least one primer-style research ticket. At lite, the two research tickets split into one for the discipline rungs and one for the specific rungs.
- Discipline knowledge from the model's weights enters as `inferred` (tier 2 at most, per ADR 0005). Sourced principles can be `researched` and tier 1 only when the user's request makes them central.
- Brand names appear in sources and influences, not in reusable descriptions.
