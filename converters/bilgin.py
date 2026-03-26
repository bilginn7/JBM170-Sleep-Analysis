import csv
from pathlib import Path
from typing import Generator
from utils import anonymize, make_row


def parse(file: Path) -> Generator[dict, None, None]:
    """
    Parses Bilgin's already-cleaned CSV.
    Columns: uid, sid, date, bedtime, wake_up_time, sleep_duration_min,
             deep_duration_min, light_duration_min, rem_duration_min,
             awake_duration_min, efficiency, avg_hr, min_hr, max_hr,
             avg_spo2, min_spo2, awake_count, screen_time_minutes
    Uses efficiency as quality (already 0-100).
    """
    with open(file, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield make_row(
                user_id             = anonymize(row['uid']),
                date                = row['date'],
                bedtime             = row['bedtime'],
                wake_up_time        = row['wake_up_time'],
                sleep_duration_min  = row['sleep_duration_min'],
                deep_duration_min   = row['deep_duration_min'],
                light_duration_min  = row['light_duration_min'],
                rem_duration_min    = row['rem_duration_min'],
                awake_duration_min  = row['awake_duration_min'],
                quality             = row.get('efficiency', ''),
                screen_time_minutes = row.get('screen_time_minutes', ''),
            )
