# 2026-03-23 Session Memory

## Context
Project topic is a voice-phishing RAG study focused on how PII masking affects retrieval quality and whether advanced retrieval can recover performance.

## Agreed Experiment Setup
1. Baseline: Naive RAG on original data with intact PII.
2. Masked baseline: Naive RAG on data with names, addresses, account details, and similar PII masked.
3. Advanced masked system: masked data plus pattern extraction, hybrid search, and reranking.

Target claims:
- Setup 2 should perform noticeably worse than setup 1.
- Setup 3 should recover to near setup 1 performance.

## Data Direction
- All data is text-based, assuming STT has already happened.
- Focus is Korean voice-phishing patterns.
- Synthetic generation will be based on real-world Korean scam patterns.
- PII should be intentionally present in original seed data so masking removes meaningful retrieval cues.
- PII should be realistic but fictional, not real people's sensitive information.

## Saved Project Plan
Saved at:
- `docs/plans/2026-03-19-voicephishing-rag-plan.md`

The plan includes:
- weekly roadmap
- corpus / QA generation direction
- baseline, masked, and advanced RAG stages
- reporting and paper-writing phase

## Generated Seed Files
Short seed scenarios:
- `data/voicephishing_pattern_scenarios.csv`

Full professor-review scenarios:
- `data/voicephishing_pattern_scenarios_full.csv`

Copies were also placed in `~/Downloads/`.

## Seed Data Design Decisions
- Separate short seed CSV and full-scenario CSV were kept intentionally.
- Full scenarios start from the first contact, not mid-conversation.
- Scenarios were rewritten to feel more realistic in Korean context.
- Real Korean institutions and familiar entity names were used.
- Each row includes:
  - pattern metadata
  - PII field types
  - fraud signal tags
  - reference URLs

## Pattern Set Covered
- institution impersonation
- isolation / confinement guidance
- child / family impersonation
- kidnapping / AI-voice coercion
- refinance-loan scam
- advance-fee requirement
- malicious app / remote control install
- card delivery impersonation
- court-mail / registered-mail impersonation
- smishing / quishing linked delivery scam

## Reference URL Policy
- Unstable links were removed.
- Only more stable confirmed URLs remain in the CSVs.
- Important note for future explanation: scenarios are realistic reconstructions based on official warning materials, not raw real victim transcripts.

## Recommended Next Steps
- Add `realism_notes` column for professor review if needed.
- Build normal bank-call counterpart scenarios in the same full format.
- Create masked versions of the same seed files.
- Define pattern extraction schema for advanced RAG.

## Important Caveat
This file is a local project memory note, not a true platform-level conversation transcript.
