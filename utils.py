import hashlib
import datetime

SALT = 'tue_sleep_study_2026'

FIELDNAMES = [
    'user_id',
    'date',
    'bedtime',
    'wake_up_time',
    'sleep_duration_min',
    'deep_duration_min',
    'light_duration_min',
    'rem_duration_min',
    'awake_duration_min',
    'quality',
    'screen_time_minutes',
]


def anonymize(uid: str | int) -> str:
    """Returns a 6-char salted hash of a uid."""
    return hashlib.sha256(f"{SALT}{uid}".encode()).hexdigest()[:6]


def make_row(user_id, date, bedtime, wake_up_time,
             sleep_duration_min, deep_duration_min, light_duration_min,
             rem_duration_min, awake_duration_min, quality,
             screen_time_minutes) -> dict:
    """Builds a unified output row."""
    return {
        'user_id':              user_id,
        'date':                 date,
        'bedtime':              bedtime,
        'wake_up_time':         wake_up_time,
        'sleep_duration_min':   sleep_duration_min,
        'deep_duration_min':    deep_duration_min,
        'light_duration_min':   light_duration_min,
        'rem_duration_min':     rem_duration_min,
        'awake_duration_min':   awake_duration_min,
        'quality':              quality,
        'screen_time_minutes':  screen_time_minutes,
    }


def parse_screen_time_duration(raw) -> str:
    """
    Parses screen time stored as HH:MM:SS (Excel duration bug).
    Treats it as hours + minutes → total minutes.
    Handles both datetime.time objects and strings.
    """
    if not raw:
        return ''
    try:
        if isinstance(raw, datetime.time):
            return str(raw.hour * 60 + raw.minute)
        clean = str(raw).strip().replace(' AM', '').replace(' PM', '')
        parts = clean.split(':')
        return str(int(parts[0]) * 60 + int(parts[1]))
    except (ValueError, IndexError):
        return ''
