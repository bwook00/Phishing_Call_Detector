# QA Redesign Notes

## Why the QA set had to change

The original QA set was not appropriate for the new RAG comparison goal.

Problems found:
- the earlier baseline used mismatched corpus sizes (`original 1000` vs `masked 300`)
- self-retrieval and near-template leakage inflated retrieval quality
- the prior classification prompt exposed the full target text, so a strong model could answer correctly without relying on retrieval
- the negative classes contained too many easy cases, making `masked naive` hard to push into the intended failure band

## New goal

Keep the class counts:
- `voicephishing = 1000`
- `bank_call = 1000`
- `irrelevant = 1000`

But redesign the internal composition so retrieval quality differences become visible.

## New QA generation strategy

### 1. Voicephishing
- Use the aligned `300`-row original corpus as the seed source.
- Generate multiple paraphrased variants per seed row.
- Preserve fraud structure while reducing shallow lexical overlap.
- Hard variants delay obvious scam cues and look more like legitimate verification calls.

### 2. Bank call
- Generate hard negatives that sound like real bank support.
- Explicitly include overlap terms such as:
  - account checks
  - unusual transaction review
  - identity verification
  - security inspection
  - transfer limits
  - temporary holds
- Explicitly forbid scam-only actions such as:
  - remote-app installation
  - third-party transfer
  - safety-account transfer
  - family isolation guidance
  - prosecution/police impersonation

### 3. Irrelevant
- Keep call-center style conversations.
- Reduce trivial everyday chatter.
- Favor service flows that still look like structured support conversations without financial-fraud signals.

## Model choice

Default generation model:
- `gpt-5.4-mini`

Fallback:
- `gpt-5-mini`

Reason:
- the project now prioritizes high-quality first-pass generation over the cheapest possible token cost
- account-level model availability was confirmed before selecting the default

## Implementation surface

Main generator:
- [regenerate_hard_qa_dataset.py](/Users/kimbwook/PycharmProjects/Phishing_Call_Detector/regenerate_hard_qa_dataset.py)

Key properties:
- deterministic spec generation for all 3000 rows
- OpenAI Responses API integration without requiring the local `openai` package
- source-type specific prompts
- dialogue normalization capped at `18` turns for cost and consistency

## What changed from the previous local-only rebuild

Previous rebuild:
- mostly local template and rewrite logic
- good for volume, weaker for targeted hard-negative design

New rebuild:
- explicit difficulty planning
- explicit hard-negative rules
- LLM generation with constrained prompts
- designed to support the intended naive vs masked-naive gap before advanced recovery work
