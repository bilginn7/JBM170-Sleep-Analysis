"""
Primary Analysis: Screen Time vs Sleep Stages
==============================================
Loads all output/sleep_*.csv files and computes:
  - Pearson r + p-value between screen_time_minutes and each sleep stage
  - Per-user breakdown
  - Scatter plots saved to output/charts/stages_correlation.png

Run from the project root: python analyze_stages.py
"""

import csv
from pathlib import Path
from datetime import date

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from scipy import stats

OUTPUT_DIR = Path('output')
CHARTS_DIR = OUTPUT_DIR / 'charts'

STAGES = [
    ('deep_duration_min',  'Deep Sleep'),
    ('light_duration_min', 'Light Sleep'),
    ('rem_duration_min',   'REM Sleep'),
]

USER_COLORS = ['#4C9BE8', '#E8724C', '#4CE8A0', '#E8C84C', '#A04CE8']

STYLE = {
    'bg':      '#0F1117',
    'panel':   '#1A1D27',
    'grid':    '#2A2D3A',
    'text':    '#E8E8F0',
    'subtext': '#7A7D9A',
}


# ── DATA LOADING ──────────────────────────────────────────────────────────────

def _num(val):
    try:
        v = float(val)
        return v if v >= 0 else None
    except (TypeError, ValueError):
        return None


def load_all():
    """Returns list of dicts (one per sleep session, all users pooled)."""
    records = []
    user_records = {}  # user_id -> list of dicts

    for file in sorted(OUTPUT_DIR.glob('sleep_*.csv')):
        user_id = file.stem.replace('sleep_', '')
        rows = []
        with open(file, 'r', newline='') as f:
            for row in csv.DictReader(f):
                screen = _num(row.get('screen_time_minutes'))
                deep   = _num(row.get('deep_duration_min'))
                light  = _num(row.get('light_duration_min'))
                rem    = _num(row.get('rem_duration_min'))
                if screen is None:
                    continue
                r = {
                    'user_id': user_id,
                    'screen_time_minutes':  screen,
                    'deep_duration_min':    deep,
                    'light_duration_min':   light,
                    'rem_duration_min':     rem,
                }
                rows.append(r)
                records.append(r)
        if rows:
            user_records[user_id] = rows

    return records, user_records


# ── STATS ──────────────────────────────────────────────────────────────────────

def correlate(records, x_field, y_field):
    """Pearson r and p-value for paired non-null values."""
    pairs = [(r[x_field], r[y_field]) for r in records
             if r[x_field] is not None and r[y_field] is not None]
    if len(pairs) < 3:
        return None, None, 0
    xs, ys = zip(*pairs)
    r, p = stats.pearsonr(xs, ys)
    return r, p, len(pairs)


def print_table(records, user_records):
    print("\n" + "=" * 60)
    print("  SCREEN TIME vs SLEEP STAGES — Pearson Correlation")
    print("=" * 60)
    print(f"  {'Stage':<18} {'r':>7} {'p':>9} {'n':>5}  {'sig':>4}")
    print("-" * 60)

    for field, label in STAGES:
        r, p, n = correlate(records, 'screen_time_minutes', field)
        if r is None:
            continue
        sig = '***' if p < 0.001 else ('**' if p < 0.01 else ('*' if p < 0.05 else 'n.s.'))
        print(f"  {label:<18} {r:>+7.3f} {p:>9.4f} {n:>5}  {sig:>4}")

    print("=" * 60)
    print("  Significance: *** p<.001  ** p<.01  * p<.05  n.s. not significant")

    print("\n  PER-USER BREAKDOWN (Deep Sleep only as example)")
    print("-" * 60)
    for uid, rows in user_records.items():
        r, p, n = correlate(rows, 'screen_time_minutes', 'deep_duration_min')
        if r is None:
            continue
        sig = '***' if p < 0.001 else ('**' if p < 0.01 else ('*' if p < 0.05 else 'n.s.'))
        print(f"  {uid:<10}  deep r={r:+.3f}  p={p:.4f}  n={n}  {sig}")
    print()


# ── CHART ──────────────────────────────────────────────────────────────────────

def chart_stages(records, user_records):
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    users = list(user_records.keys())
    color_map = {uid: USER_COLORS[i % len(USER_COLORS)] for i, uid in enumerate(users)}

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    fig.patch.set_facecolor(STYLE['bg'])

    for ax, (field, label) in zip(axes, STAGES):
        ax.set_facecolor(STYLE['panel'])
        ax.tick_params(colors=STYLE['subtext'], labelsize=8)
        ax.xaxis.label.set_color(STYLE['text'])
        ax.yaxis.label.set_color(STYLE['text'])
        ax.title.set_color(STYLE['text'])
        for spine in ax.spines.values():
            spine.set_edgecolor(STYLE['grid'])
        ax.grid(color=STYLE['grid'], linestyle='--', linewidth=0.5, alpha=0.6)

        # scatter per user
        for uid, rows in user_records.items():
            pairs = [(r['screen_time_minutes'] / 60, r[field] / 60)
                     for r in rows if r['screen_time_minutes'] is not None and r[field] is not None]
            if pairs:
                xs, ys = zip(*pairs)
                ax.scatter(xs, ys, color=color_map[uid], alpha=0.55, s=28, zorder=3)

        # overall trend line
        all_pairs = [(r['screen_time_minutes'] / 60, r[field] / 60)
                     for r in records
                     if r['screen_time_minutes'] is not None and r[field] is not None]
        if len(all_pairs) >= 3:
            xs_all, ys_all = zip(*all_pairs)
            z = np.polyfit(xs_all, ys_all, 1)
            xline = np.linspace(min(xs_all), max(xs_all), 100)
            ax.plot(xline, np.poly1d(z)(xline), color='#FF6B6B', linewidth=2, zorder=4, label='trend')

            r_val, p_val, _ = correlate(records, 'screen_time_minutes', field)
            sig = '***' if p_val < 0.001 else ('**' if p_val < 0.01 else ('*' if p_val < 0.05 else 'n.s.'))
            ax.set_title(f'{label}\nr = {r_val:+.3f}  {sig}', fontsize=10, fontweight='bold')
        else:
            ax.set_title(label, fontsize=10, fontweight='bold')

        ax.set_xlabel('Screen Time (hours)')
        ax.set_ylabel(f'{label} (hours)')

    # user legend
    handles = [mpatches.Patch(color=color_map[uid], alpha=0.7, label=uid) for uid in users]
    fig.legend(handles=handles, loc='lower center', ncol=len(users),
               facecolor=STYLE['panel'], edgecolor=STYLE['grid'],
               labelcolor=STYLE['text'], fontsize=8, bbox_to_anchor=(0.5, -0.05))

    fig.suptitle('Screen Time vs Sleep Stages (all users pooled)',
                 fontsize=13, fontweight='bold', color=STYLE['text'], y=1.02)
    fig.tight_layout()
    path = CHARTS_DIR / 'stages_correlation.png'
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor=STYLE['bg'])
    plt.close(fig)
    print(f"Chart saved to {path}")


# ── MAIN ──────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    records, user_records = load_all()
    print(f"Loaded {len(records)} sessions from {len(user_records)} users: {', '.join(user_records)}")
    print_table(records, user_records)
    chart_stages(records, user_records)
