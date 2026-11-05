# A/B test 3 results: compact shopping component, Haiku everything

Arms: **A** = task only; **B** = task + metadump 0.3.0 (lite, with discovery)

## Blind grader scores (0-10; 4 runs per arm x 3 graders = 12 scores per arm)

| arm | overall | compact | minimal | modern | usability | craft | mean rank (1-4) | overall per run |
|---|---|---|---|---|---|---|---|---|
| A | **7.17** | 7.42 | 6.0 | 6.92 | 8.33 | 6.0 | 1.67 | 7.33, 8.33, 7.0, 6.0 |
| B | **5.58** | 5.83 | 7.92 | 5.75 | 5.67 | 5.33 | 3.33 | 5.33, 5.33, 6.0, 5.67 |

## Head to head (same grader, same block, overall)

- **B vs A**: 2 wins, 20 losses, 2 ties (win rate 0.12)

Grader agreement: mean pairwise Pearson r = 0.52.

## Does it work? (headless Chrome: click the main shopping action, click +, check 390 px)

| arm | works | action found | action changes page | qty control | qty changes | no overflow at 390 px | JS errors | unnamed buttons |
|---|---|---|---|---|---|---|---|---|
| A | **4/4** | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 | 0 | 2 |
| B | **4/4** | 4/4 | 4/4 | 0/4 | 0/4 | 4/4 | 0 | 0 |

## Cost per build run (Haiku)

| arm | runs | mean tokens | mean seconds | mean tool calls |
|---|---|---|---|---|
| A | 4 | 85153 | 50.8 | 3.2 |
| B | 4 | 123018 | 169.7 | 13.8 |

Dump build (one-off, Haiku main loop and workers): 144911 tokens reported for the main loop, 556 s.
