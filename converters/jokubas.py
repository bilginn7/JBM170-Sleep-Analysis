import csv
from pathlib import Path
from datetime import datetime, timedelta
from typing import Generator
from utils import anonymize, make_row

# Gap threshold to split sessions — if > 2 hours between segments, new session
SESSION_GAP_HOURS = 2

SLEEP_TYPE = 'HKCategoryTypeIdentifierSleepAnalysis'

STAGE_MAP = {
    'HKCategoryValueSleepAnalysisAsleepCore':  'light',
    'HKCategoryValueSleepAnalysisAsleepDeep':  'deep',
    'HKCategoryValueSleepAnalysisAsleepREM':   'rem',
    'HKCategoryValueSleepAnalysisAwake':       'awake',
}

DATE_FMT = '%Y-%m-%d %H:%M:%S %z'


def parse(file: Path, user_id: str) -> Generator[dict, None, None]:
    """
    Parses Jokubas's Apple Health CSV export.
    Sleep is stored as individual stage segments per row.
    Groups contiguous segments into sessions (gap > 2h = new session).
    Aggregates stage durations and takes min/max timestamps per session.
    Screen time is duplicated on every row — takes first value per session.
    No quality field available in Apple Health.
    """
    # load all sleep segments
    segments = []
    with open(file, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['type'] != SLEEP_TYPE:
                continue
            stage = STAGE_MAP.get(row['value'])
            if stage is None:
                continue
            segments.append({
                'start':        datetime.strptime(row['startDate'], DATE_FMT),
                'end':          datetime.strptime(row['endDate'],   DATE_FMT),
                'stage':        stage,
                'duration_min': float(row['duration_minutes'] or 0),
                'screen_time':  row.get('screen_time', '').strip(),
            })

    if not segments:
        return

    # sort by start time
    segments.sort(key=lambda s: s['start'])

    # group into sessions by gap
    sessions = []
    current = [segments[0]]
    for seg in segments[1:]:
        gap = seg['start'] - current[-1]['end']
        if gap > timedelta(hours=SESSION_GAP_HOURS):
            sessions.append(current)
            current = [seg]
        else:
            current.append(seg)
    sessions.append(current)

    # aggregate each session
    for session in sessions:
        bedtime      = min(s['start'] for s in session)
        wake_up_time = max(s['end']   for s in session)
        date         = wake_up_time.date()

        deep  = round(sum(s['duration_min'] for s in session if s['stage'] == 'deep'))
        light = round(sum(s['duration_min'] for s in session if s['stage'] == 'light'))
        rem   = round(sum(s['duration_min'] for s in session if s['stage'] == 'rem'))
        awake = round(sum(s['duration_min'] for s in session if s['stage'] == 'awake'))
        total = deep + light + rem
        total_in_bed = total + awake
        quality = round((total / total_in_bed) * 100) if total_in_bed > 0 else ''

        screen_time = next((s['screen_time'] for s in session if s['screen_time']), '')
        yield make_row(
            user_id=anonymize(user_id),
            date=date,
            bedtime=int(bedtime.timestamp()),
            wake_up_time=int(wake_up_time.timestamp()),
            sleep_duration_min=total,
            deep_duration_min=deep,
            light_duration_min=light,
            rem_duration_min=rem,
            awake_duration_min=awake,
            quality=quality,
            screen_time_minutes=screen_time,
        )