import csv
from pathlib import Path
from datetime import datetime
from typing import Generator
from utils import anonymize, make_row


def parse(file: Path, user_id: str) -> Generator[dict, None, None]:
    """
    Parses Pieter's CSV with datetime strings.
    Columns: segment_1_bedtime_datetime, segment_1_wake_up_time_datetime,
             Time_datetime, total_duration, sleep_deep_duration,
             sleep_light_duration, sleep_rem_duration, sleep_awake_duration,
             sleep_score, avg_hr, min_hr, max_hr, total_long_duration,
             awake_count, screen_time_minutes (last col, may be unnamed)
    Uses sleep_score as quality (already 0-100).
    """
    with open(file, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row.get('segment_1_bedtime_datetime', '').strip():
                continue

            bedtime = datetime.strptime(row['segment_1_bedtime_datetime'].strip(), '%d/%m/%Y %H:%M')
            wake_up = datetime.strptime(row['segment_1_wake_up_time_datetime'].strip(), '%d/%m/%Y %H:%M')
            d       = datetime.strptime(row['Time_datetime'].strip(), '%d/%m/%Y %H:%M').date()

            # last column may be unnamed — find screen time by keyword or empty header
            fieldnames = reader.fieldnames or []
            screen_time = ''
            for key in fieldnames:
                if 'screen' in key.lower() or key.strip() == '':
                    screen_time = row.get(key, '').strip()
                    break

            yield make_row(
                user_id             = anonymize(user_id),
                date                = d,
                bedtime             = int(bedtime.timestamp()),
                wake_up_time        = int(wake_up.timestamp()),
                sleep_duration_min  = row.get('total_duration', '').strip(),
                deep_duration_min   = row.get('sleep_deep_duration', '').strip(),
                light_duration_min  = row.get('sleep_light_duration', '').strip(),
                rem_duration_min    = row.get('sleep_rem_duration', '').strip(),
                awake_duration_min  = row.get('sleep_awake_duration', '').strip(),
                quality             = row.get('sleep_score', '').strip(),
                screen_time_minutes = screen_time,
            )
