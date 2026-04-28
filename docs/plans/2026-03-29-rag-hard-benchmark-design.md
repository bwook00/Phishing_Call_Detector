# RAG Hard Benchmark Design

**Goal:** Rebuild the RAG experiment so the main scorecard comes from a controlled hard benchmark where `original naive`, `masked naive`, and `masked advanced` separate cleanly.

**Context**
- Corpus is now aligned at 300 original rows and 300 masked rows with 1:1 `sample_id` coverage.
- The previous baseline was invalid because it mixed `1000` original corpus rows with `300` masked rows and allowed self-retrieval leakage.
- The user wants fast iteration and is willing to tune QA hardness and retrieval parameters aggressively, but the design still needs a defensible protocol.

## Decision

Use a three-layer evaluation flow:

1. `pilot-100`
- Fast tuning loop only.
- Used to adjust QA hardness and BM25 retrieval settings until `original naive` lands near `0.75~0.85` and `masked naive` near `0.45~0.6`.

2. `official-hard`
- Main reported benchmark.
- Fixed once the pilot loop reaches the target range.
- Used for all three systems, including `masked advanced`.

3. `full-3000`
- Archive-only reference.
- Not the main claim surface.

## Benchmark Construction Rules

### Common evaluation constraints
- Use the same `300`-row source corpus for original and masked runs.
- Exclude `retrieved sample_id == source_sample_id`.
- Exclude same pattern family retrieval when comparing real generalization rather than near-template reuse.
- Hold the evaluation subset fixed once promoted from pilot to official-hard.

### Hard QA selection principles
- `voicephishing`: prefer paraphrases and lower lexical overlap cases that remain structurally fraudulent but lose direct surface cues after masking.
- `bank_call`: prefer hard negatives that mention account checks, abnormal transactions, identity verification, security review, transaction restriction, or incident handling without crossing into explicit scam-only actions.
- `irrelevant`: keep only moderate difficulty call-center style negatives so they do not artificially inflate total accuracy.

### Pilot composition
- Start with `100` rows.
- Initial target mix: `40 voicephishing / 40 bank_call / 20 irrelevant`.
- Rank candidates with retrieval-based heuristics, not random sampling.

## Retrieval tuning policy

### `original naive`
- BM25 only.
- Query: raw scenario text.
- Start with `top-k=3`.
- Expect medium accuracy after self and same-pattern exclusion.

### `masked naive`
- BM25 only.
- Query and corpus both masked.
- Start with `top-k=1`.
- No query expansion, metadata search, or reranking.
- Expect visible collapse on hard negatives.

### `masked advanced`
- Same masked corpus and same benchmark.
- Recover with pattern extraction, hybrid retrieval, and reranking.

## Promotion criteria
- Keep iterating on `pilot-100` until:
  - `original naive` is between `0.75` and `0.85`
  - `masked naive` is between `0.45` and `0.6`
- Then freeze the benchmark selection logic and materialize `official-hard`.
- Only after that begin the `masked advanced` recovery pass.

## Risks
- If the benchmark is too easy, masked naive will stay too high.
- If the benchmark is too aggressive, both naive systems may collapse together and the recovery story weakens.
- If tuning uses the final benchmark repeatedly, the result becomes brittle; use the pilot for tuning and freeze the official set once acceptable.

## Immediate next step

Implement:
- benchmark builder script
- self/same-pattern exclusion in evaluation
- pilot subset output files
- quick loop for retrieval-only and batch-based scoring
