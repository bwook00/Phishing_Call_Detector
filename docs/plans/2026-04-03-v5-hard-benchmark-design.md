# V5 Hard Benchmark Design

**Goal:** Recover `voicephishing` recall in original naive RAG while keeping `bank_call` suspicious enough that masked naive RAG still degrades.

## Problem

`reinforced_v4` made the positive class too retrieval-strict:

- original accuracy: `0.66`
- hard-masked accuracy: `0.66`
- original `voicephishing` accuracy: `2 / 34`

The main failure was not that masked recovered too much, but that both conditions collapsed on the positive class.

## Decision

Add a new `v5` generation profile to the QA regeneration script instead of overwriting the current prompt rules.

This keeps old experiments reproducible and lets new runs opt into a narrower set of prompt instructions tuned for the next benchmark iteration.

## V5 Rules

### Voicephishing

- Keep the first several turns plausibly legitimate.
- Do not make the opening so clean that the dialogue reads like a normal bank helpdesk call.
- By the middle or later turns, require at least one clear scam-action anchor such as app install, link-driven verification, code disclosure, remote control, transfer guidance, or security-account movement.
- Preserve rich identifiers and protection-workflow language so original retrieval can still lock onto the right family.

### Bank call

- Keep strong “asset protection / abnormal access / temporary restriction” language.
- Keep the call suspicious and pressure-inducing.
- Explicitly forbid scam-only actions more aggressively than before:
  - no app install
  - no link click
  - no OTP / approval code readback
  - no third-party transfer
  - no “safe account”
  - no remote control or screen share
- Keep the requested next step inside a legitimate channel such as branch visit, official app check, callback verification, or internal review wait.

### Irrelevant

- Leave mostly unchanged.
- Keep operational tension, but stay outside financial fraud behavior.

## Implementation

- Add `--prompt-profile` to `regenerate_hard_qa_dataset.py`
- Keep current prompt text as `v4`
- Add `v5` branch with stronger positive anchors and stricter negative guardrails
- Extend tests so prompt rendering is locked for both old and new profiles

## Verification

- Run unit tests for prompt generation
- Dry-run prompt previews for `v5`
- Generate a small `v5` pilot set after code is stable
