# Retrieval Reset Design

## Goal

Preserve the STT-transcript query constraint while making masked retrieval meaningfully worse before any LLM judge is involved.

## Constraints

- Query must remain the raw STT-style dialogue transcript, not a rewritten summary.
- Evaluation should better reflect realistic deployment, where exact duplicate retrieval is blocked but related scam-family retrieval is still allowed.
- We need a deterministic retrieval-first metric before retrying LLM-judged scoring.

## Decision

Shift the next benchmark iteration toward retrieval instrumentation and masking quality instead of more judge-prompt/model cycling.

## Design

### 1. Retrieval regimes

Add explicit retrieval regimes:

- `realistic`: exclude only the exact same sample
- `strict`: exclude the exact same sample and same family/pattern
- `custom`: preserve the current manual flag behavior

The primary benchmark will use `realistic`, while `strict` remains a supplementary stress setting.

### 2. Retrieval audit metadata

Record retrieval evidence per row so we can see whether masking changed retrieval before any judge step:

- top retrieved doc id
- top retrieved family
- same-family hit flag
- top-1 vs top-2 score margin
- retrieval regime used

### 3. Bundle masking

Keep existing placeholder masking, but add stronger bundle compression for identifier-rich phrases:

- institution + department bundle
- personal identifier bundle
- case / receipt / customer-id bundle

This should remove more of the rare lexical anchors that currently survive masking.

## Success criteria

On the next pilot:

1. Retrieval metadata should show a larger original-vs-masked separation on positive rows.
2. `realistic` mode should preserve more original positive recall than `strict`.
3. Judge experiments should be deferred until retrieval-only evidence improves.
