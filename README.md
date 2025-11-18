# SQL Product Analytics Labs

End-to-end, recruiter-friendly sample:
1) Deterministic **synthetic data** (customers, events, orders, A/B).
2) **SQL labs** (JOINs, WINDOWs, CTE/funnel) on DuckDB over CSVs.
3) **Jupytext notebooks** executed in CI → **HTML + PNG** visuals.

**Start here**
- SQL: `sql/01_retention_joins.sql`, `sql/02_cohort_windows.sql`, `sql/03_funnel_ctes.sql`
- Notebooks (text): `notebooks_py/01_retention_cohorts.py`, `02_funnel_analysis.py`, `03_ab_test_marketing.py`

**Visuals (appear after merge to main)**
- HTML: `reports/01_retention_cohorts.html`, `02_funnel_analysis.html`, `03_ab_test_marketing.html`
- PNGs: `assets/retention_line.png`, `assets/funnel.png`, `assets/ab_uplift.png`

Local (optional):
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python src/generate_data.py
```
