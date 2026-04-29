# African Climate Trend Analysis - Week 0

## Project Overview

This repository contains exploratory climate trend analysis for Ethiopia using NASA POWER daily weather data from January 2015 through March 2026. The Week 0 work focuses on repository setup, reproducible Python tooling, data profiling, cleaning, exploratory analysis, and locally exported cleaned datasets.

## Repository Structure

```text
.
├── .github/workflows/ci.yml   # GitHub Actions environment validation
├── data/
│   ├── raw/                   # Local raw downloads, ignored by Git
│   ├── interim/               # Local intermediate files, ignored by Git
│   └── processed/             # Local cleaned exports, ignored by Git
├── notebooks/                 # Country EDA notebooks
├── reports/figures/           # Local generated plots, ignored by Git
├── src/                       # Reusable project code
├── tests/                     # Test suite placeholder
├── .gitignore
├── requirements.txt
└── README.md
```

Only folder placeholders are committed under `data/` and `reports/figures/`. Raw, interim, processed, and generated data files stay local.

## Environment Reproduction

### Prerequisites

- Git
- Python 3.10 or newer

### Local Setup

```bash
git clone https://github.com/abigiyacodehub/climate-challenge-week0.git
cd climate-challenge-week0
python -m venv .venv
```

Activate the environment:

```bash
# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# macOS/Linux
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Register the notebook kernel:

```bash
python -m ipykernel install --user --name climate-week0 --display-name "Python (climate-week0)"
```

### Run the Ethiopia EDA Notebook

Task 2 work is on the `eda-ethiopia` branch:

```bash
git switch eda-ethiopia
jupyter notebook notebooks/ethiopia_eda.ipynb
```

Run all notebook cells from top to bottom. The notebook downloads NASA POWER data, profiles data quality, cleans daily climate features, exports a cleaned CSV to `data/processed/ethiopia_daily_cleaned.csv`, and produces analytical visualizations with written interpretations.

### Run the Cross-Country Comparison Notebook

Task 3 work is on the `compare-countries` branch:

```bash
git switch compare-countries
jupyter notebook notebooks/compare_countries.ipynb
```

Run all notebook cells from top to bottom. The notebook creates or loads cleaned local datasets for Ethiopia, Kenya, Nigeria, Egypt, and South Africa; combines them into one analysis dataset; compares temperature and precipitation patterns; analyzes extreme heat and drought frequency; and builds a relative climate vulnerability ranking framed for COP32 adaptation discussion.

## Git Workflow

This project uses feature branches and conventional commits. Example:

```bash
git switch -c eda-ethiopia
git add .
git commit -m "feat: add Ethiopia climate EDA notebook"
```

Task branch convention:

- `setup-task` for repository setup and CI configuration
- `eda-<country>` for country-level profiling, cleaning, and EDA
- `compare-countries` for cross-country comparison and vulnerability ranking
- `dashboard-dev` for dashboard development when the dashboard task begins

Open a pull request from each task branch into `main`, wait for CI to pass, then merge through GitHub so branch history and review evidence remain visible.

## Continuous Integration

GitHub Actions installs `requirements.txt`, verifies core scientific Python imports, and validates notebook JSON files on pushes to `main`, `eda-*`, and comparison branches.
