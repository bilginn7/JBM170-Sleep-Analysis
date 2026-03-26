from pathlib import Path
from datetime import datetime, date, timedelta
from typing import Generator
from utils import anonymize, make_row, parse_screen_time_duration


def parse(file: Path, user_id: str) -> Generator[dict, None, None]:
    """
    Parses Rayan's ODS file.
    Columns: id, date, startTime, endTime, duration, remDuration,
             awakeDuration, deepSleepDuration, lightSleepDuration,
             unknownSleepDuration, quality, Screen time
    quality is 0-10, multiplied by 10 to normalize to 0-100.
    Screen time is HH:MM:SS due to Excel bug — parsed as hours + minutes.
    """
    try:
        import pyexcel_ods
    except ImportError as e:
        raise ImportError(f"pyexcel-ods not found: {e}. Run: pip install pyexcel-ods")

    data = pyexcel_ods.get_data(str(file))
    sheet = list(data.values())[0]
    headers = [h.strip() for h in sheet[0]]  # strip trailing spaces

    for raw_row in sheet[1:]:
        row = dict(zip(headers, raw_row))

        if not row.get('date'):
            continue

        if isinstance(row['date'], date):
            d = row['date']
        else:
            d = datetime.strptime(str(row['date']), '%Y-%m-%d').date()

        def combine(d, t):
            if not t:
                return ''
            t_obj = t if not isinstance(t, str) else datetime.strptime(t, '%H:%M').time()
            return int(datetime.combine(d, t_obj).timestamp())

        bedtime      = combine(d, row.get('startTime'))
        wake_up_time = combine(d, row.get('endTime'))

        if bedtime and wake_up_time and wake_up_time < bedtime:
            wake_up_time = int((datetime.fromtimestamp(wake_up_time) + timedelta(days=1)).timestamp())

        raw_quality = row.get('quality', '')
        quality = str(int(raw_quality) * 10) if raw_quality != '' else ''

        yield make_row(
            user_id             = anonymize(user_id),
            date                = d,
            bedtime             = bedtime,
            wake_up_time        = wake_up_time,
            sleep_duration_min  = row.get('duration', ''),
            deep_duration_min   = row.get('deepSleepDuration', ''),
            light_duration_min  = row.get('lightSleepDuration', ''),
            rem_duration_min    = row.get('remDuration', ''),
            awake_duration_min  = row.get('awakeDuration', ''),
            quality             = quality,
            screen_time_minutes = parse_screen_time_duration(row.get('Screen time', '')),
        )
