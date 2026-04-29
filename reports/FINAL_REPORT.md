# African Climate Trend Analysis - Final Progress Report

## Repository

- GitHub repository: https://github.com/abigiyacodehub/climate-challenge-week0
- Current working branch: `compare-countries`
- Main task branches created:
  - `setup-task`
  - `eda-ethiopia`
  - `compare-countries`
- Future branch expected by rubric:
  - `dashboard-dev`

## Completed Performances

### Task 1: Git Setup and Repository Structure

- Added and refined `.gitignore` to exclude virtual environments, notebook checkpoints, local raw data, processed data, generated figures, environment files, and CSV/Parquet/XLSX data files.
- Added `requirements.txt` with the project scientific Python and notebook dependencies.
- Added `.github/workflows/ci.yml` for GitHub Actions CI.
- Updated `README.md` with project overview, folder structure, environment reproduction steps, notebook execution steps, Git workflow, branch strategy, and CI notes.
- Created logical project folders:
  - `data/raw/`
  - `data/interim/`
  - `data/processed/`
  - `notebooks/`
  - `reports/figures/`
  - `src/`
  - `tests/`
- Preserved folder placeholders with `.gitkeep` files while keeping generated data uncommitted.

### Task 2: Data Profiling, Cleaning, and Ethiopia EDA

- Created branch `eda-ethiopia`.
- Added `notebooks/ethiopia_eda.ipynb`.
- Implemented NASA POWER daily data loading for Addis Ababa, Ethiopia.
- Added local raw-data caching under `data/raw/`.
- Added data profiling for:
  - row and column counts
  - date coverage
  - duplicate dates
  - missing values
  - descriptive statistics
- Added cleaning logic for:
  - NASA missing-value sentinels (`-999`)
  - duplicate date removal
  - daily date reindexing
  - numeric time interpolation
  - date feature engineering
  - seasonal labels
- Exported cleaned local data to `data/processed/ethiopia_daily_cleaned.csv`.
- Confirmed raw and cleaned CSVs are ignored and not committed.
- Added visualizations and markdown interpretations for:
  - annual mean temperature trend
  - monthly rainfall seasonality
  - daily rainfall vs temperature by season
- Added defensive handling:
  - API/schema exception handling
  - expected-column validation
  - empty dataset validation
  - date parsing validation
  - documented data-quality decisions in markdown

### Task 3: Cross-Country Comparison and Vulnerability Ranking

- Created branch `compare-countries`.
- Added `notebooks/compare_countries.ipynb`.
- Selected five countries for cross-country comparison:
  - Ethiopia
  - Kenya
  - Nigeria
  - Sudan
  - Tanzania
- Implemented code to create or load all five countries' cleaned local datasets.
- Combined all five country datasets into a single dataframe for joint analysis.
- Added temperature comparison:
  - summary statistics
  - annual mean temperature trend visualization
- Added precipitation comparison:
  - annual precipitation summary statistics
  - annual precipitation trend visualization
  - monthly precipitation seasonality plots
- Added extreme events analysis:
  - country-specific 95th percentile extreme heat thresholds
  - extreme heat day frequency
  - dry day frequency
  - drought month frequency
- Added a relative climate vulnerability ranking table using normalized climate indicators:
  - mean temperature
  - temperature trend
  - precipitation variability
  - dry day rate
  - drought month rate
- Added COP32-framed observations covering adaptation finance, resilience planning, drought preparedness, heat exposure, and country-specific African climate risks.
- Added defensive handling:
  - country metadata validation
  - API/schema exception handling
  - expected-column validation
  - empty raw and cleaned dataset checks
  - documented vulnerability-index limitations in markdown

### Medium-Style COP32 PDF Report

- Added `reports/COP32_CLIMATE_EVIDENCE_REPORT.pdf`.
- The PDF report is written for mixed technical and non-technical readers.
- It explains the business objective: EthioClimate Analytics supporting the Ethiopian Ministry of Planning and Development as Ethiopia prepares to host COP32 in Addis Ababa in 2027.
- It frames NASA POWER daily climate evidence from January 2015 through March 2026 for Ethiopia, Kenya, Sudan, Tanzania, and Nigeria.
- It applies the negotiation-grade evidence framework:
  - What is changing?
  - What did it cause?
  - What does it demand?
- It includes properly captioned visualizations, vulnerability ranking, COP32 recommendations, limitations, and future work.

## Git and GitHub Evidence

### Branches

- `main`: contains merged setup work.
- `setup-task`: repository setup branch exists in remote history.
- `eda-ethiopia`: EDA branch exists locally and remotely.
- `compare-countries`: comparison branch exists locally and remotely.

### Conventional Commits

Recent relevant commits:

```text
03cf661 chore: document workflow and harden notebooks
8f5fd12 feat: compare country climate vulnerability
8f10ade feat: add Ethiopia climate EDA
f37dea3 Merge pull request #2 from abigiyacodehub/setup-task
bd5b9a8 chore: finalize environment setup and update dependencies for EDA
2c02ab5 ci: opt into node24 to resolve deprecation warning
df98382 fix: resolve merge conflicts in gitignore and requirements
9437dc7 ci: update github actions to verify python environment
8277bf7 init: add .gitignore
150a44b ci: add GitHub Actions workflow
```

### Pull Requests

- Setup work has already been merged into `main` through pull requests.
- `eda-ethiopia` and `compare-countries` branches are pushed and ready for pull requests into `main`.
- Pull request creation still requires explicit user approval because it publishes new GitHub PR records.

Suggested PR links:

- https://github.com/abigiyacodehub/climate-challenge-week0/pull/new/eda-ethiopia
- https://github.com/abigiyacodehub/climate-challenge-week0/pull/new/compare-countries

## CI/CD

- Workflow file: `.github/workflows/ci.yml`
- CI validates:
  - dependency installation from `requirements.txt`
  - core scientific Python imports
  - notebook JSON readability
- CI triggers on:
  - `main`
  - `eda-*`
  - `compare-countries`
  - `dashboard-dev`
- Latest observed `compare-countries` CI result: passed.
- CI run URL: https://github.com/abigiyacodehub/climate-challenge-week0/actions/runs/25088268823

## Validation Performed

Local validation commands completed successfully:

```text
Python import smoke check: passed
Notebook JSON validation: passed
notebooks/ethiopia_eda.ipynb execution: passed
notebooks/compare_countries.ipynb execution: passed
```

Notebook output evidence:

```text
notebooks/ethiopia_eda.ipynb: 20 cells, 12 code outputs
notebooks/compare_countries.ipynb: 19 cells, 12 code outputs
```

Git data-file check:

- Tracked files under `data/` are only `.gitkeep` placeholders.
- Generated raw and processed CSV files remain local and ignored.

## Current Repository File Evidence

```text
.github/workflows/ci.yml
.gitignore
README.md
requirements.txt
data/raw/.gitkeep
data/interim/.gitkeep
data/processed/.gitkeep
notebooks/ethiopia_eda.ipynb
notebooks/compare_countries.ipynb
reports/FINAL_REPORT.md
reports/COP32_CLIMATE_EVIDENCE_REPORT.pdf
reports/figures/.gitkeep
src/.gitkeep
tests/.gitkeep
```

## Remaining Recommendations

1. Open pull requests for `eda-ethiopia` and `compare-countries` into `main`.
2. Wait for CI to pass on each pull request.
3. Merge through GitHub to satisfy the pull-request evidence requirement.
4. Start the next dashboard task on `dashboard-dev` when the dashboard rubric is provided.
