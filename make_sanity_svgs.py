#!/usr/bin/env python3
from pathlib import Path
import pandas as pd

OUT=Path('docs/results/sanity_check_1000')
OUT.mkdir(parents=True, exist_ok=True)

def svg_bar(labels, values, title, path, width=900, height=360, color='#4c78a8'):
    margin_l, margin_r, margin_t, margin_b = 70, 25, 45, 90
    plot_w=width-margin_l-margin_r; plot_h=height-margin_t-margin_b
    maxv=max(values) if values else 1
    bw=plot_w/len(values)*0.65
    gap=plot_w/len(values)
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
           '<rect width="100%" height="100%" fill="white"/>',
           f'<text x="{width/2}" y="25" text-anchor="middle" font-family="Arial" font-size="18" font-weight="700">{title}</text>',
           f'<line x1="{margin_l}" y1="{margin_t+plot_h}" x2="{width-margin_r}" y2="{margin_t+plot_h}" stroke="#333"/>',
           f'<line x1="{margin_l}" y1="{margin_t}" x2="{margin_l}" y2="{margin_t+plot_h}" stroke="#333"/>']
    for t in [0,0.25,0.5,0.75,1.0]:
        y=margin_t+plot_h-(t/maxv)*plot_h if maxv>1 else margin_t+plot_h-t*plot_h
        label=t if maxv<=1 else t*maxv
        parts.append(f'<line x1="{margin_l}" y1="{y:.1f}" x2="{width-margin_r}" y2="{y:.1f}" stroke="#ddd"/>')
        parts.append(f'<text x="{margin_l-8}" y="{y+4:.1f}" text-anchor="end" font-family="Arial" font-size="11">{label:.2f}</text>')
    for i,(lab,val) in enumerate(zip(labels,values)):
        x=margin_l+i*gap+(gap-bw)/2
        h=(val/maxv)*plot_h
        y=margin_t+plot_h-h
        parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{h:.1f}" fill="{color}"/>')
        parts.append(f'<text x="{x+bw/2:.1f}" y="{y-6:.1f}" text-anchor="middle" font-family="Arial" font-size="11">{val:.3f}</text>')
        parts.append(f'<text x="{x+bw/2:.1f}" y="{margin_t+plot_h+16}" text-anchor="end" font-family="Arial" font-size="10" transform="rotate(-30 {x+bw/2:.1f},{margin_t+plot_h+16})">{lab}</text>')
    parts.append('</svg>')
    path.write_text('\n'.join(parts), encoding='utf-8')

def svg_grouped(labels, series, title, path, width=760, height=360):
    colors=['#d62728','#1f77b4']
    margin_l, margin_r, margin_t, margin_b = 75, 25, 45, 70
    plot_w=width-margin_l-margin_r; plot_h=height-margin_t-margin_b
    maxv=max(max(vals) for vals in series.values())
    names=list(series.keys())
    group_w=plot_w/len(labels)
    bw=group_w/(len(names)+1)
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">','<rect width="100%" height="100%" fill="white"/>',
           f'<text x="{width/2}" y="25" text-anchor="middle" font-family="Arial" font-size="18" font-weight="700">{title}</text>']
    y0=margin_t+plot_h
    parts.append(f'<line x1="{margin_l}" y1="{y0}" x2="{width-margin_r}" y2="{y0}" stroke="#333"/>')
    for i,lab in enumerate(labels):
        gx=margin_l+i*group_w
        for j,name in enumerate(names):
            val=series[name][i]
            h=val/maxv*plot_h
            x=gx+(j+0.7)*bw
            y=y0-h
            parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw*.85:.1f}" height="{h:.1f}" fill="{colors[j]}"/>')
            parts.append(f'<text x="{x+bw*.42:.1f}" y="{y-5:.1f}" text-anchor="middle" font-family="Arial" font-size="10">{val:.0f}</text>')
        parts.append(f'<text x="{gx+group_w/2:.1f}" y="{y0+18}" text-anchor="middle" font-family="Arial" font-size="12">{lab}</text>')
    for j,name in enumerate(names):
        parts.append(f'<rect x="{width-180}" y="{55+j*20}" width="12" height="12" fill="{colors[j]}"/>')
        parts.append(f'<text x="{width-162}" y="{66+j*20}" font-family="Arial" font-size="12">{name}</text>')
    parts.append('</svg>')
    path.write_text('\n'.join(parts), encoding='utf-8')

perf=pd.read_csv(OUT/'pipeline_performance_summary.csv')
svg_bar(perf['pipeline'].tolist(), perf['accuracy'].tolist(), '1000-row benchmark accuracy', OUT/'pipeline_accuracy_bar.svg', color='#55a868')
length=pd.read_csv(OUT/'length_token_stats.csv')
svg_grouped(['char median','token median','line median'], {
    'voicephishing':[float(length[length.source_type=='voicephishing']['char_median'].iloc[0]), float(length[length.source_type=='voicephishing']['token_median'].iloc[0]), float(length[length.source_type=='voicephishing']['line_median'].iloc[0])],
    'bank_call':[float(length[length.source_type=='bank_call']['char_median'].iloc[0]), float(length[length.source_type=='bank_call']['token_median'].iloc[0]), float(length[length.source_type=='bank_call']['line_median'].iloc[0])],
}, 'Length/token sanity check', OUT/'length_token_grouped.svg')
score=pd.read_csv(OUT/'score_distribution_by_pipeline.csv')
retr=score[score.pipeline.isin(['retrieval_original_naive','retrieval_masked_naive','retrieval_masked_advanced'])]
labels=['original naive','masked naive','masked advanced']
series={}
for source in ['voicephishing','bank_call']:
    vals=[]
    for p in ['retrieval_original_naive','retrieval_masked_naive','retrieval_masked_advanced']:
        vals.append(float(retr[(retr.pipeline==p)&(retr.source_type==source)].score_median.iloc[0]))
    series[source]=vals
svg_grouped(labels, series, 'Retrieval score median by label', OUT/'retrieval_score_median.svg')
print('wrote svg charts')
