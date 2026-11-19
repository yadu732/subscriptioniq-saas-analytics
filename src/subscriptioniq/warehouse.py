"""Store CSV source data and reporting tables in a local SQLite warehouse."""
from pathlib import Path
import sqlite3
import pandas as pd
from .metrics import monthly_metrics, cohort_retention, validate_data


def build_warehouse(data_dir: str | Path = "data", db_path: str | Path = "warehouse/subscriptioniq.db", report_dir: str | Path = "reports") -> None:
    data_dir, db_path, report_dir = Path(data_dir), Path(db_path), Path(report_dir)
    customers = pd.read_csv(data_dir / "customers.csv")
    snapshots = pd.read_csv(data_dir / "subscription_snapshots.csv")
    validate_data(customers, snapshots)
    kpis = monthly_metrics(customers, snapshots)
    cohorts = cohort_retention(customers, snapshots)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        for name, df in [("dim_customers", customers), ("fct_subscription_snapshots", snapshots), ("mart_monthly_revenue", kpis), ("mart_cohort_retention", cohorts)]:
            df.to_sql(name, conn, index=False, if_exists="replace")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_month ON fct_subscription_snapshots(month)")
    kpis.to_csv(report_dir / "monthly_revenue_kpis.csv", index=False)
    cohorts.to_csv(report_dir / "cohort_retention.csv", index=False)
    print(f"Created {db_path}, {len(kpis)} KPI months, and {len(cohorts)} cohort observations")
