# Cadence — 190-word summary

**Cadence is an AI copilot for the Learn phase of the synthetic-biology Design–Build–Test–Learn (DBTL) cycle.** Four Claude-powered agents run the loop end to end; the Learn agent ingests Test-stage datasets, flags undefined, duplicated, and anomalous data tokens, and scores each with a *reproducible confidence index* that feeds fixes back into the next Design.

We validated it against a real study — Singhal, Allen, Gaddes, Baer & Demirel, *"Biomanufacturability of a Squid Ring Teeth Protein Library via Orthogonal High-Throughput Screening"* — whose thesis is that predictable biomanufacturing "runs through models learned from library-scale data." Given the per-bin summary behind the paper's Figures 5–6, the Learn agent reproduced its headline conclusions from the summary alone: FACS brightness saturates as a yield predictor (Cliff's δ +0.46 Low→Medium, −0.03 Medium→High), growth is not the bottleneck, and codon-adaptation index carries the residual signal (bin-mean CAI vs mCherry R² = 0.91). On a schema-faithful stand-in it also caught three data-integrity defects unprompted — a malformed column, an exact duplicate (r = 1.000), and a zero-variance feature.

The entire system — orchestration, bug fixes, the live run, and this write-up — was built with **Claude (Cowork)** in one session.
