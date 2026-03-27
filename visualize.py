"""
Sleep Study Visualizations
===========================
Generates 3 charts for the presentation:
1. Screen time over time (before vs after March 16)
2. Sleep duration over time
3. Correlation between screen time and sleep quality/duration

Run from the project root. Reads from output/sleep_*.csv files.
Saves charts to output/charts/
"""

import csv
import statistics
from pathlib import Path
from datetime import datetime, date

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.dates as mdates
import numpy as np

# ── CONFIG ────────────────────────────────────────────────────────────────────

OUTPUT_DIR = Path('output')
CHARTS_DIR = OUTPUT_DIR / 'charts'
INTERVENTION_DATE = date(2026, 3, 16)

# Color per user — add more if needed
USER_COLORS = [
    '#4C9BE8',
    '#E8724C',
    '#4CE8A0',
    '#E8C84C',
    '#A04CE8',
    '#E84C8B',
]

STYLE = {
    'bg':         '#0F1117',
    'panel':      '#1A1D27',
    'grid':       '#2A2D3A',
    'text':       '#E8E8F0',
    'subtext':    '#7A7D9A',
    'before':     '#4C9BE8',
    'after':      '#4CE8A0',
    'intervline': '#FF6B6B',
}

# ── DATA LOADING ──────────────────────────────────────────────────────────────

def load_all() -> dict[str, list[dict]]:
    """Loads all sleep_*.csv files from OUTPUT_DIR. Returns {user_id: [rows]}."""
    data = {}
    for file in sorted(OUTPUT_DIR.glob('sleep_*.csv')):
        user_id = file.stem.replace('sleep_', '')
        rows = []
        with open(file, 'r', newline='') as f:
            for row in csv.DictReader(f):
                try:
                    d = date.fromisoformat(str(row['date']))
                    rows.append({
                        'date': d,
                        'sleep_duration_min': _int(row.get('sleep_duration_min')),
                        'deep_duration_min': _int(row.get('deep_duration_min')),
                        'light_duration_min': _int(row.get('light_duration_min')),
                        'rem_duration_min': _int(row.get('rem_duration_min')),
                        'awake_duration_min': _int(row.get('awake_duration_min')),
                        'quality': _int(row.get('quality')),
                        'screen_time_minutes': _int(row.get('screen_time_minutes')),
                    })
                except (ValueError, KeyError):
                    continue
        if rows:
            data[user_id] = sorted(rows, key=lambda r: r['date'])
    return data


def filter_common_dates(data: dict) -> dict:
    """Keep only dates that appear in ALL users' data."""
    date_sets = [set(r['date'] for r in rows) for rows in data.values()]
    common = set.intersection(*date_sets)
    return {
        user_id: [r for r in rows if r['date'] in common]
        for user_id, rows in data.items()
    }


def aggregate_daily(data: dict) -> dict:
    """Sum all sessions per day per user — handles naps + main sleep."""
    result = {}
    for user_id, rows in data.items():
        by_date: dict = {}
        for row in rows:
            d = row['date']
            if d not in by_date:
                by_date[d] = {
                    'date':                d,
                    'sleep_duration_min':  0,
                    'deep_duration_min':   0,
                    'light_duration_min':  0,
                    'rem_duration_min':    0,
                    'awake_duration_min':  0,
                    'quality':             [],
                    'screen_time_minutes': row['screen_time_minutes'],
                }
            for field in ('sleep_duration_min', 'deep_duration_min',
                          'light_duration_min', 'rem_duration_min',
                          'awake_duration_min'):
                v = row[field]
                if v is not None:
                    by_date[d][field] += v
            if row['quality'] is not None:
                by_date[d]['quality'].append(row['quality'])

        # average quality across sessions
        for d, r in by_date.items():
            r['quality'] = round(sum(r['quality']) / len(r['quality'])) if r['quality'] else None

        result[user_id] = sorted(by_date.values(), key=lambda r: r['date'])
    return result


def _int(val) -> int | None:
    try:
        v = int(float(val))
        return v if v >= 0 else None
    except (TypeError, ValueError):
        return None


def daily_avg(data: dict, field: str) -> dict[date, float]:
    """Averages a field across all users per date."""
    by_date: dict[date, list[float]] = {}
    for rows in data.values():
        for row in rows:
            v = row[field]
            if v is not None:
                by_date.setdefault(row['date'], []).append(v)
    return {d: statistics.mean(vs) for d, vs in sorted(by_date.items())}


# ── CHART HELPERS ─────────────────────────────────────────────────────────────

def apply_style(fig, axes):
    fig.patch.set_facecolor(STYLE['bg'])
    for ax in (axes if hasattr(axes, '__iter__') else [axes]):
        ax.set_facecolor(STYLE['panel'])
        ax.tick_params(colors=STYLE['subtext'], labelsize=9)
        ax.xaxis.label.set_color(STYLE['text'])
        ax.yaxis.label.set_color(STYLE['text'])
        ax.title.set_color(STYLE['text'])
        for spine in ax.spines.values():
            spine.set_edgecolor(STYLE['grid'])
        ax.grid(color=STYLE['grid'], linestyle='--', linewidth=0.5, alpha=0.7)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
        ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha='right')


def add_intervention(ax, label=True):
    ax.axvline(INTERVENTION_DATE, color=STYLE['intervline'],
               linewidth=1.5, linestyle='--', alpha=0.9)
    if label:
        ax.text(INTERVENTION_DATE, ax.get_ylim()[1] * 0.97,
                ' ← intervention', color=STYLE['intervline'],
                fontsize=8, va='top')


# ── CHART 1: SCREEN TIME OVER TIME ───────────────────────────────────────────

def chart_screen_time(data: dict):
    fig, ax = plt.subplots(figsize=(12, 5))
    apply_style(fig, ax)

    avg = daily_avg(data, 'screen_time_minutes')
    dates = list(avg.keys())
    values = [avg[d] / 60 for d in dates]  # convert to hours

    # per-user lines (thin, faded)
    for (user_id, rows), color in zip(data.items(), USER_COLORS):
        user_dates = [r['date'] for r in rows if r['screen_time_minutes'] is not None]
        user_vals  = [r['screen_time_minutes'] / 60 for r in rows if r['screen_time_minutes'] is not None]
        if user_dates:
            ax.plot(user_dates, user_vals, color=color, alpha=0.25, linewidth=1)

    # before/after colored fill
    before_dates = [d for d in dates if d < INTERVENTION_DATE]
    after_dates  = [d for d in dates if d >= INTERVENTION_DATE]
    before_vals  = [avg[d] / 60 for d in before_dates]
    after_vals   = [avg[d] / 60 for d in after_dates]

    ax.plot(before_dates, before_vals, color=STYLE['before'], linewidth=2.5, label='Before intervention')
    ax.plot(after_dates,  after_vals,  color=STYLE['after'],  linewidth=2.5, label='After intervention')
    ax.fill_between(before_dates, before_vals, alpha=0.15, color=STYLE['before'])
    ax.fill_between(after_dates,  after_vals,  alpha=0.15, color=STYLE['after'])

    add_intervention(ax)

    ax.set_title('Screen Time Over Time (Group Average)', fontsize=13, pad=12, fontweight='bold')
    ax.set_ylabel('Screen Time (hours)')
    ax.legend(facecolor=STYLE['panel'], edgecolor=STYLE['grid'],
              labelcolor=STYLE['text'], fontsize=9)

    fig.tight_layout()
    path = CHARTS_DIR / 'screen_time.png'
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor=STYLE['bg'])
    plt.close(fig)
    print(f"Saved {path}")


# ── CHART 2: SLEEP DURATION OVER TIME ────────────────────────────────────────

def chart_sleep_duration(data: dict):
    fig, ax = plt.subplots(figsize=(12, 5))
    apply_style(fig, ax)

    avg = daily_avg(data, 'sleep_duration_min')
    dates = list(avg.keys())
    values = [avg[d] / 60 for d in dates]  # convert to hours

    # per-user lines
    for (user_id, rows), color in zip(data.items(), USER_COLORS):
        user_dates = [r['date'] for r in rows if r['sleep_duration_min'] is not None]
        user_vals  = [r['sleep_duration_min'] / 60 for r in rows if r['sleep_duration_min'] is not None]
        if user_dates:
            ax.plot(user_dates, user_vals, color=color, alpha=0.25, linewidth=1, label=user_id)

    before_dates = [d for d in dates if d < INTERVENTION_DATE]
    after_dates  = [d for d in dates if d >= INTERVENTION_DATE]
    before_vals  = [avg[d] / 60 for d in before_dates]
    after_vals   = [avg[d] / 60 for d in after_dates]

    ax.plot(before_dates, before_vals, color=STYLE['before'], linewidth=2.5)
    ax.plot(after_dates,  after_vals,  color=STYLE['after'],  linewidth=2.5)
    ax.fill_between(before_dates, before_vals, alpha=0.15, color=STYLE['before'])
    ax.fill_between(after_dates,  after_vals,  alpha=0.15, color=STYLE['after'])

    # recommended sleep line
    ax.axhline(8, color=STYLE['subtext'], linewidth=1, linestyle=':', alpha=0.7)
    ax.text(dates[0], 8.1, 'recommended 8h', color=STYLE['subtext'], fontsize=8)

    add_intervention(ax)

    ax.set_title('Sleep Duration Over Time (Group Average)', fontsize=13, pad=12, fontweight='bold')
    ax.set_ylabel('Sleep Duration (hours)')

    # user legend
    handles = [mpatches.Patch(color=c, alpha=0.6, label=uid)
               for (uid, _), c in zip(data.items(), USER_COLORS)]
    ax.legend(handles=handles, facecolor=STYLE['panel'], edgecolor=STYLE['grid'],
              labelcolor=STYLE['text'], fontsize=8, title='Users',
              title_fontsize=8)

    fig.tight_layout()
    path = CHARTS_DIR / 'sleep_duration.png'
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor=STYLE['bg'])
    plt.close(fig)
    print(f"Saved {path}")


# ── CHART 3: CORRELATION SCREEN TIME VS SLEEP ─────────────────────────────────

def chart_correlation(data: dict):
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    apply_style(fig, axes)

    for ax in axes:
        ax.xaxis.set_major_formatter(plt.ScalarFormatter())
        ax.xaxis.set_major_locator(plt.AutoLocator())
        ax.set_xlabel('Screen Time (hours)')

    # collect paired points
    pairs_duration = []
    pairs_quality  = []

    for user_id, rows in data.items():
        for row in rows:
            st = row['screen_time_minutes']
            sd = row['sleep_duration_min']
            sq = row['quality']
            if st is not None and sd is not None:
                pairs_duration.append((st / 60, sd / 60,
                                       row['date'] >= INTERVENTION_DATE))
            if st is not None and sq is not None:
                pairs_quality.append((st / 60, sq,
                                      row['date'] >= INTERVENTION_DATE))

    def scatter_and_fit(ax, pairs, ylabel, title):
        if not pairs:
            return
        before = [(x, y) for x, y, after in pairs if not after]
        after  = [(x, y) for x, y, after in pairs if after]

        for pts, color, label in [(before, STYLE['before'], 'Before'),
                                   (after,  STYLE['after'],  'After')]:
            if pts:
                xs, ys = zip(*pts)
                ax.scatter(xs, ys, color=color, alpha=0.5, s=30, label=label)
                # trend line
                z = np.polyfit(xs, ys, 1)
                p = np.poly1d(z)
                xline = np.linspace(min(xs), max(xs), 100)
                ax.plot(xline, p(xline), color=color, linewidth=1.5, alpha=0.8)

        ax.set_ylabel(ylabel)
        ax.set_title(title, fontsize=11, fontweight='bold')
        ax.legend(facecolor=STYLE['panel'], edgecolor=STYLE['grid'],
                  labelcolor=STYLE['text'], fontsize=8)

    scatter_and_fit(axes[0], pairs_duration,
                    'Sleep Duration (hours)',
                    'Screen Time vs Sleep Duration')
    scatter_and_fit(axes[1], pairs_quality,
                    'Sleep Quality (0–100)',
                    'Screen Time vs Sleep Quality')

    fig.suptitle('Correlation: Screen Time & Sleep', fontsize=14,
                 fontweight='bold', color=STYLE['text'], y=1.01)
    fig.tight_layout()
    path = CHARTS_DIR / 'correlation.png'
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor=STYLE['bg'])
    plt.close(fig)
    print(f"Saved {path}")


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)

    data = load_all()
    data = filter_common_dates(data)
    data = aggregate_daily(data)
    sample_user = next(iter(data.values()))
    print(f"Using {len(sample_user)} common dates across all users")
    if not data:
        print("No data found in output/. Make sure sleep_*.csv files are present.")
        return

    print(f"Loaded data for {len(data)} users: {', '.join(data.keys())}")

    chart_screen_time(data)
    chart_sleep_duration(data)
    chart_correlation(data)

    print(f"\nAll charts saved to {CHARTS_DIR}/")


if __name__ == '__main__':
    main()