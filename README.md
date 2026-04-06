# JBM170 Sleep Analysis

**What is the effect of reducing daily smartphone screen time on sleep quality and duration?**

This repository contains the data, processing pipeline, and analysis code for a self-experimentation study conducted as part of the JBM170 course at Eindhoven University of Technology (TU/e).

## Study Design

- **Participants**: N=5 university students at TU/e (all co-authors of this project)
- **Study period**: End of February to end of March 2026 (~7 weeks)
- **Intervention**: From March 16, 2026, all participants agreed to reduce their daily smartphone screen time to an average of 4 hours/week
- **Design**: Pre/post intervention comparison with continuous daily measurement

### Participants and Devices

| Participant     | Device          | Data Format       |
|-----------------|-----------------|-------------------|
| Bilgin Eren     | Xiaomi Mi Band  | Pre-cleaned CSV   |
| Junior Jansen   | Xiaomi Mi Band  | MiFitness JSON-in-CSV |
| Rayan Mahmoud   | Garmin Fenix 7  | ODS spreadsheet   |
| Pieter Pronk    | Xiaomi Mi Band  | CSV with European dates |
| Jokubas Jasas   | Apple Watch     | Apple HealthKit CSV export |

### Metrics

| Metric | Description |
|--------|-------------|
| **Sleep duration** | Total time spent asleep per night in minutes, excluding time awake in bed |
| **Sleep stages** | Each night broken down into deep, light, REM, and awake periods (following [AASM](https://aasm.org/) sleep staging terminology) |
| **Sleep quality** | Score from 0 to 100 calculated by the device, based on sleep efficiency |
| **Screen time** | Total daily smartphone screen time in minutes, self-reported or pulled from device tracking |

### Ethical Considerations

All five participants are the researchers themselves (self-experimentation). Participation was voluntary and all members agreed to share their data for this project. User identifiers in the output data are anonymized using salted SHA-256 hashing to ensure privacy while maintaining consistency across the dataset.

## Data Pipeline

```
data/ (raw)  -->  converter.py  -->  output/ (unified CSV)  -->  visualize.py + analyze_stages.py  -->  output/charts/
```

1. **Data collection**: Each participant exports raw sleep data from their device in its own format
2. **Format detection**: The converter automatically detects the file format based on filename keywords
3. **Parsing and normalizing**: Each parser extracts sleep metrics and maps them to a unified schema (see [DATA_DICTIONARY.md](DATA_DICTIONARY.md))
4. **Anonymization**: User IDs are replaced with a 6-character salted SHA-256 hash
5. **Unified output**: All files are merged into individual CSVs with a common schema in `output/`

## Repository Structure

```
JBM170-Sleep-Analysis/
├── data/                  # Raw input data (5 files, various formats)
├── output/                # Unified CSV output per participant
│   └── charts/            # Generated visualizations (PNG)
├── converters/            # Format-specific parsers
│   ├── bilgin.py          # Bilgin's pre-cleaned CSV parser
│   ├── mifitness.py       # MiFitness JSON-in-CSV parser (Junior)
│   ├── pieter.py          # Pieter's CSV parser (European date format)
│   ├── rayan.py           # Rayan's ODS parser (Garmin export)
│   └── jokubas.py         # Apple HealthKit CSV parser
├── converter.py           # Main pipeline orchestrator
├── visualize.py           # Time-series and correlation charts
├── analyze_stages.py      # Pearson correlation analysis (screen time vs sleep stages)
├── utils.py               # Shared schema, anonymization, and helpers
├── DATA_DICTIONARY.md     # Variable definitions and data provenance
├── CITATION.cff           # Citation metadata
├── LICENSE                # MIT License (code), CC-BY-4.0 (data)
└── requirements.txt       # Python dependencies
```

## Getting Started

### Prerequisites

- Python 3.10+

### Installation

```bash
pip install -r requirements.txt
```

### Running the Pipeline

```bash
# Step 1: Convert raw data to unified format
python converter.py

# Step 2: Generate visualizations
python visualize.py

# Step 3: Run statistical analysis (Pearson correlations)
python analyze_stages.py
```

## Key Results (Preliminary)

- Screen time dropped ~35% after the intervention (from ~7h to ~4h daily average)
- Sleep duration slightly improved, more consistently reaching the recommended 8 hours
- Pooled Pearson correlations between screen time and sleep stages: r = -0.3 to -0.4 (p < .001)
- However, no strong correlation was found between screen time and sleep quality at the individual level, likely due to small sample size and individual differences
- Causality cannot be confirmed from this observational design

## License

- **Code**: [MIT License](LICENSE)
- **Data**: [Creative Commons Attribution 4.0 International (CC-BY-4.0)](https://creativecommons.org/licenses/by/4.0/)

## Authors

Bilgin Eren, Junior Jansen, Rayan Mahmoud, Pieter Pronk, Jokubas Jasas

Eindhoven University of Technology, JBM170, 2026
