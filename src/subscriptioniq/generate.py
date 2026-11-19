"""Produce deterministic, fictional SaaS subscription snapshots."""
from pathlib import Path
import argparse
import numpy as np
import pandas as pd

PLANS = {"Starter": 29, "Growth": 99, "Enterprise": 299}
COUNTRIES = ["Germany", "Netherlands", "France", "United Kingdom", "Sweden"]
CHANNELS = ["Organic", "Paid Search", "Partner", "Referral"]
SEGMENTS = ["SMB", "Mid-Market", "Enterprise"]


def create_data(seed: int = 42, customers: int = 420, start: str = "2024-01-01", end: str = "2026-10-01") -> tuple[pd.DataFrame, pd.DataFrame]:
    if customers < 1:
        raise ValueError("customers must be positive")
    months = pd.date_range(start, end, freq="MS")
    if len(months) < 2:
        raise ValueError("Provide at least two months")
    rng = np.random.default_rng(seed)
    signup_indexes = rng.integers(0, len(months), size=customers)
    customer_rows = []
    snapshot_rows = []
    plans = list(PLANS)
    for idx in range(customers):
        user = f"C{idx+1:05d}"
        signup_index = int(signup_indexes[idx])
        channel = str(rng.choice(CHANNELS, p=[.38, .29, .13, .20]))
        segment = str(rng.choice(SEGMENTS, p=[.65, .27, .08]))
        country = str(rng.choice(COUNTRIES))
        customer_rows.append({"customer_id": user, "signup_month": months[signup_index].date().isoformat(), "country": country, "channel": channel, "segment": segment})
        plan_i = int(rng.choice([0, 1, 2], p=[.60, .32, .08] if segment != "Enterprise" else [.15,.40,.45]))
        active = True
        for month_idx in range(signup_index, len(months)):
            if month_idx > signup_index:
                if active and rng.random() < (0.022 if segment == "Enterprise" else 0.050):
                    active = False
                elif not active and rng.random() < 0.075:
                    active = True
                elif active:
                    movement = rng.random()
                    if movement < .075 and plan_i < 2:
                        plan_i += 1
                    elif movement < .13 and plan_i > 0:
                        plan_i -= 1
            snapshot_rows.append({"customer_id": user, "month": months[month_idx].date().isoformat(), "plan": plans[plan_i] if active else "Cancelled", "mrr_eur": PLANS[plans[plan_i]] if active else 0})
    c = pd.DataFrame(customer_rows).sort_values("customer_id").reset_index(drop=True)
    s = pd.DataFrame(snapshot_rows).sort_values(["month", "customer_id"]).reset_index(drop=True)
    return c, s


def write_data(folder: str | Path = "data", seed: int = 42, customers: int = 420) -> None:
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    c, s = create_data(seed=seed, customers=customers)
    c.to_csv(folder / "customers.csv", index=False)
    s.to_csv(folder / "subscription_snapshots.csv", index=False)
    print(f"Generated {len(c)} fictional customers and {len(s)} monthly snapshots in {folder}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate fictional SaaS data")
    parser.add_argument("--out", default="data")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--customers", type=int, default=420)
    args = parser.parse_args()
    write_data(args.out, args.seed, args.customers)


if __name__ == "__main__":
    main()
