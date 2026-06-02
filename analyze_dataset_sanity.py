#!/usr/bin/env python3
from __future__ import annotations

import csv
import math
import re
from collections import Counter
from pathlib import Path
from typing import Iterable

import pandas as pd

OUT_DIR = Path('docs/results/sanity_check_1000')
QA_PATH = Path('data/expanded_hard_binary_qa_1000.csv')
RESULT_FILES = {
    'retrieval_original_naive': Path('data/expanded1000_original_naive_threshold_results.csv'),
    'retrieval_masked_naive': Path('data/expanded1000_masked_naive_threshold_results.csv'),
    'retrieval_masked_advanced': Path('data/expanded1000_masked_advanced_rag_threshold_results.csv'),
    'e2e_original': Path('data/e2e1000_original_identifier_filtered_results.csv'),
    'e2e_masked': Path('data/e2e1000_masked_identifier_filtered_results.csv'),
    'e2e_masked_advanced': Path('data/e2e1000_masked_advanced_guarded_results.csv'),
}

TOKEN_RE = re.compile(r"[A-Za-z0-9]+(?:[-./][A-Za-z0-9]+)*|[가-힣]{2,}")
STOPWORDS = {
    '고객님','고객','확인','안내','절차','보안','계좌','거래','본인','오늘','지금','네','예','말씀','상담원','상담사',
    '고객센터','피해자','사기범','은행직원','담당자','합니다','있습니다','했습니다','됩니다','주세요','아니요','그럼',
    '있는지','있는','없는','같은','위해','통해','현재','최근','다시','혹시','먼저','바로','가능합니다','알겠습니다'
}
KEY_TERMS = [
    '링크','앱','설치','인증번호','원격','이체','송금','대표번호','공식','영업점','방문','내부','검토',
    '이상거래','보안점검','본인확인','명의도용','사건번호','수사관','검찰','보호','제한','지급정지'
]


def tokens(text: str) -> list[str]:
    return [t for t in TOKEN_RE.findall(str(text)) if t not in STOPWORDS and len(t) >= 2]


def parse_score(raw: str, retrieved_scores: str = '') -> float:
    raw = str(raw)
    matches = re.findall(r"score:([-0-9.]+)", raw)
    if matches:
        return float(matches[-1])
    parts = str(retrieved_scores).split('|')
    try:
        return float(parts[0])
    except Exception:
        return math.nan


def q25(x: pd.Series) -> float:
    return float(x.quantile(0.25))


def q75(x: pd.Series) -> float:
    return float(x.quantile(0.75))



def df_to_md(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    lines = ["| " + " | ".join(map(str, cols)) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in df.iterrows():
        vals = [str(row[c]) for c in cols]
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def write_plots(qa: pd.DataFrame, result_files: dict[str, Path]) -> None:
    try:
        import matplotlib.pyplot as plt
    except Exception as exc:
        print(f'skip plots: {exc}')
        return

    # Length boxplots
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    for ax, col, title in zip(axes, ['char_len', 'token_count', 'line_count'], ['Character length', 'Token count', 'Line count']):
        data = [qa[qa.source_type == 'voicephishing'][col], qa[qa.source_type == 'bank_call'][col]]
        ax.boxplot(data, labels=['voicephishing', 'bank_call'], showfliers=False)
        ax.set_title(title)
        ax.grid(axis='y', alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT_DIR / 'length_token_line_boxplots.png', dpi=180)
    plt.close(fig)

    # Retrieval score distribution for core 3 retrieval pipelines.
    retrieval_names = ['retrieval_original_naive', 'retrieval_masked_naive', 'retrieval_masked_advanced']
    fig, axes = plt.subplots(1, 3, figsize=(13, 4), sharey=True)
    for ax, name in zip(axes, retrieval_names):
        df = pd.read_csv(result_files[name])
        df['score'] = [parse_score(r, s) for r, s in zip(df.get('raw_output',''), df.get('retrieved_scores',''))]
        for source, color in [('voicephishing', '#d62728'), ('bank_call', '#1f77b4')]:
            vals = df[df.source_type == source]['score'].dropna()
            ax.hist(vals, bins=24, alpha=0.55, label=source, color=color)
        ax.set_title(name.replace('_', ' '))
        ax.grid(axis='y', alpha=0.3)
    axes[0].set_ylabel('count')
    axes[-1].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT_DIR / 'retrieval_score_histograms.png', dpi=180)
    plt.close(fig)

    # Performance comparison bar chart.
    perf = pd.read_csv(OUT_DIR / 'pipeline_performance_summary.csv')
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.bar(range(len(perf)), perf['accuracy'], color=['#999999', '#c44e52', '#55a868', '#999999', '#c44e52', '#55a868'])
    ax.set_xticks(range(len(perf)))
    ax.set_xticklabels(perf['pipeline'], rotation=25, ha='right', fontsize=8)
    ax.set_ylim(0, 1.0)
    ax.set_ylabel('accuracy')
    ax.set_title('1000-row benchmark accuracy')
    ax.grid(axis='y', alpha=0.3)
    for idx, val in enumerate(perf['accuracy']):
        ax.text(idx, val + 0.015, f'{val:.3f}', ha='center', fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT_DIR / 'pipeline_accuracy_bar.png', dpi=180)
    plt.close(fig)

def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    qa = pd.read_csv(QA_PATH)
    qa['char_len'] = qa['scenario_text'].astype(str).str.len()
    qa['token_count'] = qa['scenario_text'].map(lambda x: len(tokens(str(x))))
    qa['line_count'] = qa['scenario_text'].astype(str).str.count('\n') + 1
    qa['source_family'] = qa['source_sample_id'].astype(str).str.split('-', n=1).str[0]

    label_dist = qa.groupby(['source_type','ground_truth']).size().reset_index(name='count')
    label_dist.to_csv(OUT_DIR / 'label_distribution.csv', index=False)

    length_stats = qa.groupby('source_type').agg(
        count=('qa_id','count'),
        char_mean=('char_len','mean'), char_median=('char_len','median'), char_q25=('char_len',q25), char_q75=('char_len',q75),
        token_mean=('token_count','mean'), token_median=('token_count','median'), token_q25=('token_count',q25), token_q75=('token_count',q75),
        line_mean=('line_count','mean'), line_median=('line_count','median'), line_q25=('line_count',q25), line_q75=('line_count',q75),
        unique_source_samples=('source_sample_id','nunique'), unique_families=('source_family','nunique'),
    ).round(3).reset_index()
    length_stats.to_csv(OUT_DIR / 'length_token_stats.csv', index=False)

    # Term frequency by class and ratio summary.
    rows = []
    counters = {}
    for source, group in qa.groupby('source_type'):
        c = Counter()
        for text in group['scenario_text']:
            c.update(tokens(str(text)))
        counters[source] = c
        for term, count in c.most_common(40):
            rows.append({'source_type': source, 'term': term, 'count': count})
    pd.DataFrame(rows).to_csv(OUT_DIR / 'top_terms_by_label.csv', index=False)

    key_rows = []
    for term in KEY_TERMS:
        for source, group in qa.groupby('source_type'):
            count = int(group['scenario_text'].astype(str).str.contains(term, regex=False).sum())
            key_rows.append({'term': term, 'source_type': source, 'doc_count': count, 'doc_ratio': round(count / len(group), 4)})
    pd.DataFrame(key_rows).to_csv(OUT_DIR / 'key_term_doc_frequency.csv', index=False)

    score_rows = []
    perf_rows = []
    for name, path in RESULT_FILES.items():
        df = pd.read_csv(path)
        df['score'] = [parse_score(r, s) for r, s in zip(df.get('raw_output',''), df.get('retrieved_scores',''))]
        df['correct'] = df['ground_truth'].eq(df['prediction'])
        score_stats = df.groupby('source_type').agg(
            count=('qa_id','count'),
            score_mean=('score','mean'), score_median=('score','median'), score_q25=('score',q25), score_q75=('score',q75),
            accuracy=('correct','mean'), yes_pred_ratio=('prediction', lambda s: float((s == 'yes').mean())),
        ).round(4).reset_index()
        score_stats.insert(0, 'pipeline', name)
        score_rows.extend(score_stats.to_dict('records'))
        perf_rows.append({
            'pipeline': name,
            'count': len(df),
            'accuracy': round(float(df['correct'].mean()), 4),
            'voicephishing_accuracy': round(float(df[df.source_type == 'voicephishing']['correct'].mean()), 4),
            'bank_call_accuracy': round(float(df[df.source_type == 'bank_call']['correct'].mean()), 4),
            'yes_pred_ratio': round(float((df['prediction'] == 'yes').mean()), 4),
        })
    pd.DataFrame(score_rows).to_csv(OUT_DIR / 'score_distribution_by_pipeline.csv', index=False)
    pd.DataFrame(perf_rows).to_csv(OUT_DIR / 'pipeline_performance_summary.csv', index=False)

    write_plots(qa, RESULT_FILES)

    # Markdown report.
    report = []
    report.append('# 1000-row Hard Benchmark Sanity Check\n')
    report.append('## 1. Label balance\n')
    report.append(df_to_md(label_dist))
    report.append('\n\n## 2. Length / token / line statistics\n')
    report.append(df_to_md(length_stats))
    report.append('\n\n## 3. Pipeline performance summary\n')
    report.append(df_to_md(pd.DataFrame(perf_rows)))
    report.append('\n\n## 4. Score distribution by pipeline\n')
    report.append(df_to_md(pd.DataFrame(score_rows)))
    report.append('\n\n## 5. Key-term document frequency\n')
    key_df = pd.DataFrame(key_rows)
    pivot = key_df.pivot(index='term', columns='source_type', values='doc_ratio').reset_index().fillna(0)
    report.append(df_to_md(pivot))
    report.append('\n\n## Interpretation\n')
    report.append('- The benchmark is label-balanced: 500 voicephishing positives and 500 bank_call hard negatives.\n')
    report.append('- Both labels are represented by 34/33 unique source samples expanded through transcript-style variants, so the 1000 rows are an augmented robustness benchmark rather than fully independent scenarios.\n')
    report.append('- Line-count medians are similar across labels, while bank_call scripts are longer on average; therefore the result should be presented together with hard-negative construction rather than as an external real-world benchmark.\n')
    report.append('- The main trend is stable across retrieval-threshold and e2e settings: masked naive RAG drops sharply, while masked advanced RAG recovers performance.\n')
    report.append('- Key-term frequency confirms that bank_call contains many banking/security terms, so it is a harder negative class than irrelevant samples; however normal-resolution terms such as official/representative-number/branch-visit are important for reducing false positives.\n')
    (OUT_DIR / 'sanity_check_report.md').write_text('\n'.join(report), encoding='utf-8')

    print(f'wrote outputs to {OUT_DIR}')
    print(length_stats.to_string(index=False))
    print(pd.DataFrame(perf_rows).to_string(index=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
