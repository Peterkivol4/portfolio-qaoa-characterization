# Research Journal

## 2026-02-24

I started from the older portfolio-QAOA machinery because it already had the optimizer and reporting pieces I needed. What broke almost immediately was the story. I could make the code run, but I could not explain what a better result meant physically.

## 2026-03-08

The first `J1-J2` runs made the direction clearer. Low-depth QAOA would improve the energy and still leave `J2 = 0.3` and `J2 = 0.5` looking too similar in the learned angles and correlation errors. That was the point where `p` stopped feeling like “more layers” and started feeling like a resolution limit.

## 2026-03-22

I tried to preserve the old public identity for too long. The code still worked, but the README kept spending its first paragraphs apologising for being a portfolio benchmark that was no longer about portfolios. Renaming the package to `layerfield_qaoa` fixed that mismatch.

## 2026-04-16

I needed one example that made the whole idea concrete without a long abstract. The `J2 = 0.3` versus `J2 = 0.5` case became that anchor because `p = 1` still looks confused while `p = 3` starts to separate the two regimes in a way you can actually point at.

## 2026-05-05

I added the journal and the cross-repo notes because the repos finally read like one research thread instead of four unrelated dumps. LayerField is where the “what is this circuit actually resolving?” question started, and the other three only make sense if that part is visible.
