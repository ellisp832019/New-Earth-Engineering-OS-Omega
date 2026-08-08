# Decision Centre Guide

The Decision Centre is the deterministic recommendation workspace for NEOS v0.8.

## What it does

- Shows the decision inbox
- Produces deterministic recommendations
- Compares architecture and implementation options
- Surfaces release readiness
- Ranks reuse, test priority, and technical debt work
- Runs scenario analysis before a change is committed
- Records accept, reject, and defer actions as operator choices

## What it does not do

- It does not replace operator judgment
- It does not silently mutate decisions
- It does not use AI to override the deterministic engine

## Typical flow

1. Open the Decision Centre in the desktop app.
2. Review the inbox and the recommended action.
3. Inspect supporting and opposing evidence.
4. Accept, reject, or defer the recommendation.
5. Re-run the view after the next scan or memory update.

