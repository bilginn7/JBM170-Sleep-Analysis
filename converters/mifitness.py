import csv
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Generator
from utils import anonymize, make_row


def parse(file: Path) -> Generator[dict, None, None]:
    """
    Parses raw MiFitness CSV with inline screen_time_minutes column (Junior).
    Columns: Uid, Sid, Key, Time, Value, UpdateTime, screen_time_minutes
    Uses sleep_efficiency as quality (already 0-100).
    """
    with open(file, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['Key'] != 'sleep':
                continue

            value = json.loads(row['Value'])
            d = datetime.fromtimestamp(int(row['Time']), tz=timezone.utc).date()

            yield make_row(
                user_id             = anonymize(row['Uid']),
                date                = d,
                bedtime             = int(value.get('bedtime')),
                wake_up_time        = int(value.get('wake_up_time')),
                sleep_duration_min  = value.get('sleep_duration'),
                deep_duration_min   = value.get('sleep_deep_duration'),
                light_duration_min  = value.get('sleep_light_duration'),
                rem_duration_min    = value.get('sleep_rem_duration'),
                awake_duration_min  = value.get('sleep_awake_duration'),
                quality             = value.get('sleep_efficiency'),
                screen_time_minutes = row.get('screen_time_minutes', ''),
            )
