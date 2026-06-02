# 1000-row Hard Benchmark Sanity Check

## 1. Label balance

| source_type | ground_truth | count |
| --- | --- | --- |
| bank_call | no | 500 |
| voicephishing | yes | 500 |


## 2. Length / token / line statistics

| source_type | count | char_mean | char_median | char_q25 | char_q75 | token_mean | token_median | token_q25 | token_q75 | line_mean | line_median | line_q25 | line_q75 | unique_source_samples | unique_families |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bank_call | 500 | 1367.798 | 1363.0 | 1243.0 | 1451.5 | 251.892 | 245.0 | 233.0 | 270.0 | 17.058 | 18.0 | 17.0 | 18.0 | 33 | 1 |
| voicephishing | 500 | 751.996 | 773.0 | 655.75 | 840.0 | 136.05 | 134.0 | 121.0 | 151.0 | 17.184 | 18.0 | 18.0 | 18.0 | 34 | 2 |


## 3. Pipeline performance summary

| pipeline | count | accuracy | voicephishing_accuracy | bank_call_accuracy | yes_pred_ratio |
| --- | --- | --- | --- | --- | --- |
| retrieval_original_naive | 1000 | 0.821 | 0.704 | 0.938 | 0.383 |
| retrieval_masked_naive | 1000 | 0.541 | 0.144 | 0.938 | 0.103 |
| retrieval_masked_advanced | 1000 | 0.911 | 0.884 | 0.938 | 0.473 |
| e2e_original | 1000 | 0.894 | 0.9 | 0.888 | 0.506 |
| e2e_masked | 1000 | 0.513 | 0.206 | 0.82 | 0.193 |
| e2e_masked_advanced | 1000 | 0.953 | 0.944 | 0.962 | 0.491 |


## 4. Score distribution by pipeline

| pipeline | source_type | count | score_mean | score_median | score_q25 | score_q75 | accuracy | yes_pred_ratio |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| retrieval_original_naive | bank_call | 500 | 44.8895 | 45.4151 | 36.6529 | 51.5998 | 0.938 | 0.062 |
| retrieval_original_naive | voicephishing | 500 | 69.3595 | 69.0807 | 59.8889 | 75.3356 | 0.704 | 0.704 |
| retrieval_masked_naive | bank_call | 500 | 38.1506 | 37.7712 | 29.6486 | 44.2889 | 0.938 | 0.062 |
| retrieval_masked_naive | voicephishing | 500 | 52.6347 | 52.8176 | 43.0706 | 56.5491 | 0.144 | 0.144 |
| retrieval_masked_advanced | bank_call | 500 | 38.0952 | 33.7502 | 21.8645 | 46.7881 | 0.938 | 0.062 |
| retrieval_masked_advanced | voicephishing | 500 | 122.0833 | 124.0004 | 98.1277 | 139.1923 | 0.884 | 0.884 |
| e2e_original | bank_call | 500 | 86.5495 | 88.5362 | 78.259 | 95.6122 | 0.888 | 0.112 |
| e2e_original | voicephishing | 500 | 69.6135 | 69.2584 | 59.8889 | 77.8739 | 0.9 | 0.9 |
| e2e_masked | bank_call | 500 | 79.8106 | 79.7349 | 69.8645 | 89.2889 | 0.82 | 0.18 |
| e2e_masked | voicephishing | 500 | 52.8887 | 52.8176 | 44.729 | 56.4536 | 0.206 | 0.206 |
| e2e_masked_advanced | bank_call | 500 | 58.4092 | 56.9979 | 45.8645 | 68.7881 | 0.962 | 0.038 |
| e2e_masked_advanced | voicephishing | 500 | 86.2473 | 83.4536 | 64.4344 | 96.7669 | 0.944 | 0.944 |


## 5. Key-term document frequency

| term | bank_call | voicephishing |
| --- | --- | --- |
| 검찰 | 0.0 | 0.0 |
| 검토 | 1.0 | 0.03 |
| 공식 | 1.0 | 0.116 |
| 내부 | 0.97 | 0.144 |
| 대표번호 | 0.968 | 0.0 |
| 링크 | 0.06 | 0.73 |
| 명의도용 | 1.0 | 0.0 |
| 방문 | 1.0 | 0.056 |
| 보안점검 | 1.0 | 0.03 |
| 보호 | 1.0 | 1.0 |
| 본인확인 | 1.0 | 0.118 |
| 사건번호 | 0.0 | 0.0 |
| 설치 | 0.0 | 0.614 |
| 송금 | 0.12 | 0.0 |
| 수사관 | 0.0 | 0.0 |
| 앱 | 1.0 | 0.702 |
| 영업점 | 1.0 | 0.0 |
| 원격 | 0.0 | 0.292 |
| 이상거래 | 1.0 | 0.088 |
| 이체 | 0.786 | 0.354 |
| 인증번호 | 0.216 | 0.558 |
| 제한 | 1.0 | 0.262 |
| 지급정지 | 0.85 | 0.028 |


## Interpretation

- The benchmark is label-balanced: 500 voicephishing positives and 500 bank_call hard negatives.

- Both labels are represented by 34/33 unique source samples expanded through transcript-style variants, so the 1000 rows are an augmented robustness benchmark rather than fully independent scenarios.

- Line-count medians are similar across labels, while bank_call scripts are longer on average; therefore the result should be presented together with hard-negative construction rather than as an external real-world benchmark.

- The main trend is stable across retrieval-threshold and e2e settings: masked naive RAG drops sharply, while masked advanced RAG recovers performance.

- Key-term frequency confirms that bank_call contains many banking/security terms, so it is a harder negative class than irrelevant samples; however normal-resolution terms such as official/representative-number/branch-visit are important for reducing false positives.
