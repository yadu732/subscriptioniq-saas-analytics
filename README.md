# 📈 SubscriptionIQ | SaaS Revenue & Cohort Analytics

[![CI](https://github.com/yadu732/subscriptioniq-saas-analytics/actions/workflows/ci.yml/badge.svg)](https://github.com/yadu732/subscriptioniq-saas-analytics/actions/workflows/ci.yml)

**A reproducible analytics portfolio project** that turns fictional subscription histories into executive SaaS KPIs, cohort retention views, and a queryable SQLite reporting warehouse. Relevant to **Data Analyst, BI Analyst, Analytics Engineer** roles and subscription-platform experience.

> **Demo data only.** All customers, markets, and financial transactions are synthesized. Numbers are not real company performance.

## What it demonstrates

- Python ETL and dimensional reporting model, with `dim_customers`, `fct_subscription_snapshots` and SQL marts.
- MRR waterfall/bridge with **new, expansion, contraction, churn, reactivation** components and an exact reconciliation assertion.
- ARR run-rate, NRR, GRR, gross revenue churn, channel breakdown and cohort retention.
- Streamlit dashboard with filters and CSV downloads.
- SQL business questions in `sql/business_queries.sql`, reproducible data generation and automated tests.

## Run locally (Windows PowerShell)

```powershell
cd subscriptioniq
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m subscriptioniq.cli generate --out data --seed 42
python -m subscriptioniq.cli build --data data --db warehouse/subscriptioniq.db --reports reports
pytest -q
streamlit run app.py
```

Then visit **http://localhost:8501**.

On macOS/Linux use `python3 -m venv .venv` and `source .venv/bin/activate`.

### Docker

```bash
docker build -t subscriptioniq .
docker run --rm -p 8501:8501 subscriptioniq
```

## Repository layout

```text
src/subscriptioniq/generate.py    Synthetic customer and subscription history generator
src/subscriptioniq/metrics.py     Validated SaaS KPI engine and cohort calculation
src/subscriptioniq/warehouse.py   SQLite and CSV analytics mart builder
src/subscriptioniq/cli.py         CLI
app.py                            Interactive Streamlit report
sql/business_queries.sql          Three practical analyst SQL queries
data/                             Small demo source datasets
tests/                            Analytical correctness and validation tests
.github/workflows/ci.yml          Continuous integration
```

## KPI definitions and caveats

- **MRR**: sum of positive subscription MRR at the end of the reporting month (EUR).
- **ARR run-rate**: 12 × current MRR. **Not actual annual revenue**.
- **Net Revenue Retention**: (starting MRR − churn − contraction + expansion) / starting MRR × 100. New or reactivated revenue is excluded.
- **Gross Revenue Retention**: (starting MRR − churn − contraction) / starting MRR × 100.
- **Customer/logo cohort retention**: fraction of first-paying customers with active subscriptions at a given cohort age. A previously cancelled and then reactivated customer counts in later active months.
- MRR movements are computed on **customer totals**, not individual invoices or subscription lines. This simplifies multi-subscription complexities and excludes taxes, refunds, usage billing, FX and recognized revenue.
- At-risk and churn probabilities in the simulator are arbitrary illustrative assumptions, **not calibrated industry rates**.
- Blank months in synthetic snapshots are treated as 0 MRR by the reporting engine. This is appropriate for this controlled generator, not a general policy for incomplete production data.
