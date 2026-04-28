# E2E Identifier-Filtered-Flow Results Checkpoint

## Scope
This checkpoint records the first full end-to-end RAG run that achieved a strong original/masked separation on the full binary benchmark.

## Configuration
- QA set: `data/reinforced_v5_binary_qa_67.csv`
- Corpus pair:
  - original: `data/voicephishing_corpus_v2.csv`
  - masked: `data/voicephishing_corpus_masked_strong_v2.csv`
- Retrieval regime: `realistic`
- `top_k=1`
- Judge model: `gpt-4o-mini`
- Prompt mode: `identifier-filtered-flow`
- Execution path: OpenAI Batch API on `/v1/responses`

## Key judge behavior
The successful change was not a pure wording tweak. The effective decision policy became:
1. Keep the user query as raw STT dialogue.
2. Retrieve as before.
3. Before handing evidence to the judge, hide any retrieved context that shares **no identifier anchors** with the query.
4. If every retrieved context is filtered out, replace the judge prompt with a policy-no prompt.
5. Otherwise, let the judge inspect only the surviving contexts plus the filtered evidence summary.

## Full 67-row E2E results
### Overall accuracy
- Original: **0.9104477612**
- Masked: **0.5074626866**

### By class
- Original
  - `voicephishing`: **0.8823529412**
  - `bank_call`: **0.9393939394**
- Masked
  - `voicephishing`: **0.2058823529**
  - `bank_call`: **0.8181818182**

## Artifacts
### Retrieval CSVs
- `data/full67_v6_original_identifier_filtered_flow_retrieval.csv`
- `data/full67_v6_masked_identifier_filtered_flow_retrieval.csv`

### Batch request JSONL
- `data/full67_v6_original_identifier_filtered_flow_batch_requests.jsonl`
- `data/full67_v6_masked_identifier_filtered_flow_batch_requests.jsonl`

### Batch output JSONL
- `data/full67_v6_original_identifier_filtered_flow_batch_output.jsonl`
- `data/full67_v6_masked_identifier_filtered_flow_batch_output.jsonl`

### Final merged CSVs
- `data/full67_v6_original_identifier_filtered_flow_results.csv`
- `data/full67_v6_masked_identifier_filtered_flow_results.csv`

## Interpretation
This is the first full end-to-end result in this repo that clearly preserves a high original score while pushing masked close to the earlier target band.

The crucial shift was to make the judge **see only identifier-supported retrieval evidence**, instead of letting it free-ride on scam actions from retrieval hits that had no lexical bridge back to the raw query.

## Remaining caveat
This is still an engineered inference policy, not a naive raw-context-only RAG judge. Any report should state that the e2e judge uses **identifier-filtered retrieval evidence** before final classification.
