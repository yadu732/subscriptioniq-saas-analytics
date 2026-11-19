"""Well-defined month-over-month SaaS revenue metrics."""
import pandas as pd

REQUIRED_CUSTOMERS = {"customer_id", "signup_month", "country", "channel", "segment"}
REQUIRED_SNAPSHOTS = {"customer_id", "month", "plan", "mrr_eur"}


def validate_data(customers: pd.DataFrame, snapshots: pd.DataFrame) -> None:
    if REQUIRED_CUSTOMERS - set(customers.columns):
        raise ValueError(f"Missing customer columns: {sorted(REQUIRED_CUSTOMERS - set(customers.columns))}")
    if REQUIRED_SNAPSHOTS - set(snapshots.columns):
        raise ValueError(f"Missing snapshot columns: {sorted(REQUIRED_SNAPSHOTS - set(snapshots.columns))}")
    if customers.customer_id.isna().any() or customers.customer_id.duplicated().any():
        raise ValueError("Customer IDs must be unique and non-null")
    if snapshots[["customer_id", "month"]].duplicated().any():
        raise ValueError("One snapshot per customer and month is allowed")
    if not snapshots.customer_id.isin(customers.customer_id).all():
        raise ValueError("Snapshot references unknown customer")
    if snapshots.mrr_eur.isna().any() or (pd.to_numeric(snapshots.mrr_eur, errors="coerce").isna().any()):
        raise ValueError("MRR must be numeric")
    if (pd.to_numeric(snapshots.mrr_eur) < 0).any():
        raise ValueError("MRR cannot be negative")
    if pd.to_datetime(snapshots.month, errors="coerce").isna().any():
        raise ValueError("Snapshot month must be a date")


def _full_matrix(customers: pd.DataFrame, snapshots: pd.DataFrame) -> pd.DataFrame:
    validate_data(customers, snapshots)
    snap = snapshots.copy()
    snap["month"] = pd.to_datetime(snap["month"]).dt.to_period("M").dt.to_timestamp()
    snap["mrr_eur"] = snap["mrr_eur"].astype(float)
    all_months = pd.date_range(snap.month.min(), snap.month.max(), freq="MS")
    matrix = (snap.pivot(index="month", columns="customer_id", values="mrr_eur")
              .reindex(index=all_months, columns=customers.customer_id).fillna(0.0))
    return matrix


def monthly_metrics(customers: pd.DataFrame, snapshots: pd.DataFrame) -> pd.DataFrame:
    """MRR bridge: ending = beginning + new + expansion + reactivation - contraction - churn."""
    m = _full_matrix(customers, snapshots)
    first_paid = {col: m.index[m[col] > 0].min() if (m[col] > 0).any() else pd.NaT for col in m.columns}
    output = []
    previous = pd.Series(0.0, index=m.columns)
    for month, current in m.iterrows():
        before = float(previous.sum())
        new, expanded, contracted, churned, reactivated = 0., 0., 0., 0., 0.
        for customer in m.columns:
            old, now = float(previous[customer]), float(current[customer])
            if old == 0 and now > 0:
                if first_paid[customer] == month:
                    new += now
                else:
                    reactivated += now
            elif old > 0 and now == 0:
                churned += old
            elif old > 0 and now > old:
                expanded += now - old
            elif old > 0 and now < old:
                contracted += old - now
        retained = before - churned - contracted + expanded
        output.append({"month": month.date().isoformat(), "starting_mrr": round(before, 2),
                       "new_mrr": round(new, 2), "expansion_mrr": round(expanded, 2),
                       "reactivation_mrr": round(reactivated, 2), "contraction_mrr": round(contracted, 2),
                       "churned_mrr": round(churned, 2), "ending_mrr": round(float(current.sum()), 2),
                       "arr_eur": round(float(current.sum()) * 12, 2),
                       "active_customers": int((current > 0).sum()),
                       "net_revenue_retention_pct": round(100 * retained / before, 2) if before else None,
                       "gross_revenue_retention_pct": round(100 * (before - churned - contracted) / before, 2) if before else None,
                       "gross_revenue_churn_pct": round(100 * (churned + contracted) / before, 2) if before else None})
        previous = current
    df = pd.DataFrame(output)
    delta = df.ending_mrr - (df.starting_mrr + df.new_mrr + df.expansion_mrr + df.reactivation_mrr - df.contraction_mrr - df.churned_mrr)
    if not (delta.abs() < 0.001).all():
        raise AssertionError("MRR bridge must reconcile")
    return df


def cohort_retention(customers: pd.DataFrame, snapshots: pd.DataFrame) -> pd.DataFrame:
    """Logo retention by first paid month, not signup month."""
    m = _full_matrix(customers, snapshots)
    records = []
    for customer in m.columns:
        paid = m.index[m[customer] > 0]
        if not len(paid):
            continue
        start = paid.min()
        for month in m.index[m.index >= start]:
            age = (month.year - start.year) * 12 + month.month - start.month
            records.append({"cohort": start.date().isoformat(), "age_months": age, "customer_id": customer, "retained": int(m.loc[month, customer] > 0)})
    rows = pd.DataFrame(records)
    if rows.empty:
        return pd.DataFrame(columns=["cohort", "age_months", "retention_pct", "cohort_size"])
    grouped = rows.groupby(["cohort", "age_months"], as_index=False).agg(retention_pct=("retained", "mean"), cohort_size=("customer_id", "nunique"))
    grouped["retention_pct"] = (grouped.retention_pct * 100).round(1)
    return grouped


def segment_snapshots(customers: pd.DataFrame, snapshots: pd.DataFrame, *, channel=None, country=None, segment=None):
    c = customers.copy()
    for field, selected in [("channel", channel), ("country", country), ("segment", segment)]:
        if selected and selected != "All":
            c = c[c[field] == selected]
    return c, snapshots[snapshots.customer_id.isin(c.customer_id)].copy()
