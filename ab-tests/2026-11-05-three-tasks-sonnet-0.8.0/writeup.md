# A/B test 17: metadump 0.8.0, the best-scoring version, retested on Sonnet 5.5 at medium

0.8.0 scored best of all versions on these three tasks in test 12, with everything on Haiku 5.5 at medium: 7.50 vs 6.33, pooled p = 0.045. The plugin went back to it (ADR 0017), and test 17 retests it with Sonnet 5.5 at medium:
- **Plugin:** 0.8.0, restored exactly;
- **Dumps:** test 12's 0.8.0 dumps;
- **Prompts:** test 12's dump-arm prompt;
- **Builds and graders:** fresh on both arms, all Sonnet.

Pre-registration: `design.md`. Tables: `results.md`.

## Results

| task | A overall | B overall | B vs A (won–lost–tied) | p | variety A | variety B |
|---|---|---|---|---|---|---|
| button | **8.08** | 5.75 | 0–23–1 | 0.029 | **5.33** | 3.33 |
| haiku | 5.25 | **7.50** | 20–2–2 | 0.086 | 1.33 | **5.00** |
| toast | **7.33** | 6.62 | 8–15–1 | 0.29 | **4.00** | 2.00 |

Pooled: 28 wins, 40 losses, 4 ties (p = 0.65).

## Expectations

1. **B ≥ A overall on at least 2 of 3 tasks. No:** the haiku only.
2. **B variety ≥ A on at least 2 of 3. No:** the haiku only.
3. **Pooled, B wins more than it loses. No:** 28 to 40.

## What happened

**The haiku won again, as it has on every Sonnet test.**
- The prompt-only haiku were the same nacreous poem four times ("mother-of-pearl", "hold the dusk", "long after the sun").
- The dump haiku put a lens cloud over a ridge, pearl along one edge over creaking ice, mother-of-pearl over lake ice, and a gale running through a lens cloud.
- They scored freshness 7.42 vs 4.58 and form 9.00 vs 6.58.

**The button lost every pairing but one, and it is test 12's old failure on a stronger model.**
- All four dump buttons reused the 0.8.0 dump's curves (3.5 each; three curves shared by all four).
- Graders called them "polite rather than dreamlike" and "a faint glow and sheen pass that barely reads as ethereal". Dreamlike scored 4.25 vs 8.50.
- Sonnet's prompt-only buttons went big: an iridescent drift, an aurora with rising motes, a pointer-following mist.
- This is what 0.8.1 (no single curves) and 0.11.0 (no tamed worn paths) were built to fix, but neither beat 0.8.0 overall.

**The toast lost on variety and craft.** The dump toasts converged (variety 2.00 vs 4.00) and scored lower on craft (6.42 vs 7.42). They led on usability (7.25 vs 6.67).

## Across the Sonnet tests

| test | version | pooled (won–lost–tied) | p | more varied on |
|---|---|---|---|---|
| 15 | 0.10.0, a hand | 30–32–10 | 0.55 | 2 of 3 |
| 16 | 0.11.0, amplify, dumps rebuilt | 27–39–6 | 0.72 | 3 of 3 |
| 17 | 0.8.0 | 28–40–4 | 0.65 | 1 of 3 |

On Sonnet, no version beats prompt-only overall on these three tasks. Every version won the haiku by a wide margin: 21–1–2, 18–6–0 and 20–2–2. On the two UI tasks Sonnet alone is strong, and a dump that pulls toward restraint or packs in more than fits costs more than it adds.

On Haiku (tests 12 to 14) the dump side won overall every time, with pooled win rates from 0.64 to 0.69. The dump helps a small model more than a strong one, except on writing, where it helps both.

## Caveats

- n = 4 per arm per task, one dump per task (Haiku-built while the builders are Sonnet), LLM graders.
- One prompt-only button (A-r3) showed no hover change in the automated capture; graders still rated it 7.33.
- The impeccable design hook commented on HTML files inside builder sessions in both arms.
