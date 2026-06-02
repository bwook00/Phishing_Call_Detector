교수님 안녕하세요.

말씀해주셨던 데이터셋 적절성 문제를 확인하기 위해, 1000개 규모로 확장한 hard negative benchmark에 대해 간단한 sanity check를 진행했습니다.

확인한 항목은 label 분포, 대본 길이, 토큰 수, 발화 수, 주요 표현 빈도, retrieval score 분포입니다.

## 확인 결과 요약

1. Label 분포는 voicephishing 500개, bank_call 500개로 균형 있게 구성되어 있습니다.

2. 발화 수 기준으로는 두 label 모두 median 18개 수준으로 유사했습니다. 다만 bank_call이 평균 글자 수와 토큰 수는 더 긴 편이었습니다. 따라서 최종 보고서에서는 이 데이터셋을 완전한 외부 독립 테스트셋이라기보다는, 정상 금융 통화와 보이스피싱을 구분하기 위한 hard negative augmented benchmark로 명확히 설명하려고 합니다.

3. 주요 표현 빈도를 확인해보니 bank_call에도 이상거래, 보안점검, 본인확인, 계좌 제한 등 보이스피싱과 표면적으로 유사한 금융/보안 표현이 많이 포함되어 있었습니다. 따라서 irrelevant sample보다 훨씬 어려운 negative로 볼 수 있었습니다.

4. Retrieval score 분포를 보면 masked naive RAG에서는 voicephishing 쪽 score와 recall이 크게 낮아졌고, Advanced RAG에서는 구조적 패턴을 활용하면서 score와 성능이 다시 회복되는 경향이 확인되었습니다.

정리하면, 현재 benchmark는 완전히 독립적인 1000개 시나리오라기보다는 67개 hard seed를 기반으로 transcript 형식과 표현을 변형한 augmented benchmark입니다. 다만 label balance와 hard negative 구성, 주요 표현 빈도, score 분포를 함께 보면 original/masked/advanced 조건 비교를 위한 실험셋으로는 사용할 수 있다고 판단했습니다.

추가로 정리되는 내용이 있으면 이어서 공유드리겠습니다.

감사합니다.
김병욱 드림.
