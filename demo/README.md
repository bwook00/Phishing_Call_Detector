# Live Call Simulation Demo

This folder contains a no-STT browser demo for the final voicephishing RAG project.

## File

- `live-call-simulation.html`

## What it demonstrates

The demo simulates a phone call where transcript chunks appear over time. It does **not** perform speech recognition. It assumes an STT system has already produced transcript text, then demonstrates transcript-based RAG detection under privacy masking.

It shows:

- Original RAG
- Masked RAG
- Masked Advanced RAG
- Risk chips for app/link install, verification-code request, urgency, and normal-procedure bypass
- A positive voicephishing path ending in `YES`
- A normal bank-call hard-negative path ending in `NO`
- Final 1000-row benchmark metrics

## How to open

Open the file directly in a browser:

```text
demo/live-call-simulation.html
```

No server is required.

## Scope note

This is a deterministic, precomputed simulation for presentation/video purposes. It is a frozen demo artifact, not a production live detector.

It does not use:

- STT engine
- microphone
- audio upload
- OpenAI API
- network calls
- runtime data loading

The project scope is transcript-based RAG detection, not speech recognition.
