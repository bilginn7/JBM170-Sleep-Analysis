# Data Dictionary

This document describes all variables in the unified output data, the provenance of raw data, and the transformations applied.

## Unified Output Schema

All output files in `output/sleep_*.csv` share the following schema:

| Variable | Type | Unit | Range | Description |
|----------|------|------|-------|-------------|
| `user_id` | string | - | 6-char hex | Anonymized participant identifier (salted SHA-256 hash, first 6 characters) |
| `date` | string | ISO 8601 | YYYY-MM-DD | Date of the sleep session (date of waking up) |
| `bedtime` | integer | Unix timestamp (seconds) | - | Time the participant went to bed. Timezone: Europe/Amsterdam (CET/CEST, UTC+1/+2) |
| `wake_up_time` | integer | Unix timestamp (seconds) | - | Time the participant woke up. Same timezone as bedtime |
| `sleep_duration_min` | integer | minutes | 0-1440 | Total time spent asleep, excluding awake periods |
| `deep_duration_min` | integer | minutes | 0-1440 | Duration of deep (N3) sleep stage |
| `light_duration_min` | integer | minutes | 0-1440 | Duration of light (N1+N2) sleep stage |
| `rem_duration_min` | integer | minutes | 0-1440 | Duration of REM sleep stage |
| `awake_duration_min` | integer | minutes | 0-1440 | Time spent awake during the sleep period |
| `quality` | integer | percentage | 0-100 | Sleep quality score (see normalization below) |
| `screen_time_minutes` | integer | minutes | 0-1440 | Total daily smartphone screen time |

### Sleep Stage Terminology

Sleep stages follow the [American Academy of Sleep Medicine (AASM)](https://aasm.org/) classification:

- **Deep sleep** (N3 / slow-wave sleep): Most restorative stage, important for physical recovery
- **Light sleep** (N1 + N2): Transition stages between wakefulness and deeper sleep
- **REM sleep** (Rapid Eye Movement): Linked to memory consolidation and dreaming
- **Awake**: Periods of wakefulness during the overall sleep session

Reference: Berry, R.B. et al. (2017). *The AASM Manual for the Scoring of Sleep and Associated Events*. American Academy of Sleep Medicine.

## Quality Score Normalization

Different devices report sleep quality differently. All scores are normalized to a 0-100 scale:

| Source | Original Metric | Normalization |
|--------|----------------|---------------|
| Bilgin (Mi Band) | `efficiency` (0-100) | Used directly |
| Junior (MiFitness) | `sleep_efficiency` (0-100) | Used directly |
| Pieter (Mi Band) | `sleep_score` (0-100) | Used directly |
| Rayan (Garmin) | `quality` (0-10) | Multiplied by 10 |
| Jokubas (Apple Watch) | Not available | Computed as `(total_sleep / total_in_bed) * 100` |

## Anonymization

User identifiers are anonymized using SHA-256 hashing with a fixed salt (`tue_sleep_study_2026`). Only the first 6 hexadecimal characters of the hash are used as the `user_id`. This ensures:
- Consistent IDs across all sessions for the same participant
- No possibility of reverse-engineering the original identifier

Implementation: [`utils.py`](utils.py), `anonymize()` function.

## Raw Data Provenance

### Data Sources

| Raw File | Participant | Device | Export Source | Converter |
|----------|-------------|--------|--------------|-----------|
| `data/bilgin_screentime_sleep.csv` | Bilgin Eren | Xiaomi Mi Band | Pre-cleaned CSV | `converters/bilgin.py` |
| `data/junior_screentime.csv` | Junior Jansen | Xiaomi Mi Band | MiFitness app export | `converters/mifitness.py` |
| `data/Rayan_Sleep_CSV.ods` | Rayan Mahmoud | Garmin Fenix 7 | Garmin Connect export (ODS) | `converters/rayan.py` |
| `data/sleep_data_extracted_newer.csv` | Pieter Pronk | Xiaomi Mi Band | Device export (CSV, DD/MM/YYYY dates) | `converters/pieter.py` |
| `data/jokubas_screentime_sleep.csv` | Jokubas Jasas | Apple Watch | Apple HealthKit export | `converters/jokubas.py` |

### Output Files

| Output File | Participant |
|-------------|-------------|
| `output/sleep_bilgin.csv` | Bilgin Eren |
| `output/sleep_junior.csv` | Junior Jansen |
| `output/sleep_rayan.csv` | Rayan Mahmoud |
| `output/sleep_pieter.csv` | Pieter Pronk |
| `output/sleep_jokubas.csv` | Jokubas Jasas |

### Format-Specific Notes

**MiFitness (Junior)**: Raw CSV contains a `Value` column with serialized JSON objects. The parser extracts sleep metrics from these JSON objects. Only rows with `Key == 'sleep'` are processed.

**Apple HealthKit (Jokubas)**: Sleep data is stored as individual stage segments (one row per stage per period). The parser groups contiguous segments into sessions using a 2-hour gap threshold: if more than 2 hours pass between consecutive segments, a new sleep session begins. Stage durations are summed per session.
- Apple HealthKit identifiers used: `HKCategoryTypeIdentifierSleepAnalysis`
- Stage values mapped: `HKCategoryValueSleepAnalysisAsleepCore` (light), `HKCategoryValueSleepAnalysisAsleepDeep` (deep), `HKCategoryValueSleepAnalysisAsleepREM` (REM), `HKCategoryValueSleepAnalysisAwake` (awake)

**Garmin / ODS (Rayan)**: Screen time is stored as `HH:MM:SS` format due to a spreadsheet formatting artifact. The parser interprets the hours and minutes as total minutes (e.g., `8:50` = 8*60 + 50 = 530 minutes). Quality is on a 0-10 scale, multiplied by 10 for normalization.

**Pieter's CSV**: Uses European date format (`DD/MM/YYYY HH:MM`). The last column contains screen time but may have an empty or unnamed header.

## Screen Time Measurement

Screen time was collected through a mix of methods depending on the participant:
- **Self-reported**: Participants manually recorded daily screen time from their phone's built-in screen time tracker
- **Device-exported**: Some participants pulled screen time data directly from device settings

All screen time values are in minutes and represent total daily smartphone usage.

## Timestamps and Timezone

All Unix timestamps in `bedtime` and `wake_up_time` are based on local time in the Netherlands (Europe/Amsterdam timezone, CET UTC+1 or CEST UTC+2). The study period (Feb-Apr 2026) spans the DST transition on March 29, 2026.
