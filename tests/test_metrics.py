import pandas as pd
import pytest
from subscriptioniq.generate import create_data
from subscriptioniq.metrics import monthly_metrics, cohort_retention, validate_data, segment_snapshots


def small_fixture():
    c = pd.DataFrame([{"customer_id": x, "signup_month": "2026-01-01", "country":"Germany", "channel":"Organic", "segment":"SMB"} for x in ["A", "B", "C"]])
    rows = [("A","2026-01-01",100), ("B","2026-01-01",50), ("C","2026-01-01",0),
            ("A","2026-02-01",150), ("B","2026-02-01",0), ("C","2026-02-01",20),
            ("A","2026-03-01",120), ("B","2026-03-01",60), ("C","2026-03-01",0)]
    s = pd.DataFrame([{"customer_id":u,"month":m,"mrr_eur":v,"plan":"Test"} for u,m,v in rows])
    return c,s


def test_mrr_bridge_expansion_churn_and_new():
    c,s = small_fixture()
    m = monthly_metrics(c,s).set_index("month")
    jan = m.loc["2026-01-01"]
    assert jan.ending_mrr == 150 and jan.new_mrr == 150
    feb = m.loc["2026-02-01"]
    assert feb.starting_mrr == 150 and feb.expansion_mrr == 50
    assert feb.churned_mrr == 50 and feb.new_mrr == 20 and feb.ending_mrr == 170
    mar = m.loc["2026-03-01"]
    assert mar.contraction_mrr == 30 and mar.reactivation_mrr == 60
    assert mar.churned_mrr == 20 and mar.ending_mrr == 180


def test_grr_nrr_denominator():
    c,s = small_fixture()
    feb = monthly_metrics(c,s).set_index("month").loc["2026-02-01"]
    assert feb.net_revenue_retention_pct == pytest.approx(100 * 150 / 150)
    assert feb.gross_revenue_retention_pct == pytest.approx(100 * 100 / 150, abs=.01)


def test_cohort_retention():
    c,s = small_fixture()
    ret = cohort_retention(c,s)
    jan_age_1 = ret[(ret.cohort == "2026-01-01") & (ret.age_months == 1)].iloc[0]
    assert jan_age_1.retention_pct == 50.0
    assert jan_age_1.cohort_size == 2


def test_generation_is_reproducible():
    c1,s1 = create_data(customers=20, seed=14)
    c2,s2 = create_data(customers=20, seed=14)
    pd.testing.assert_frame_equal(c1,c2)
    pd.testing.assert_frame_equal(s1,s2)
    assert (s1.mrr_eur >= 0).all()


def test_invalid_unknown_customer():
    c,s = small_fixture()
    s.loc[0,"customer_id"] = "unknown"
    with pytest.raises(ValueError, match="unknown"):
        validate_data(c,s)


def test_invalid_duplicate_snapshot():
    c,s = small_fixture()
    with pytest.raises(ValueError, match="snapshot"):
        validate_data(c,pd.concat([s,s.iloc[[0]]],ignore_index=True))


def test_segment_filter():
    c,s = small_fixture()
    c.loc[0,"country"] = "France"
    cf,sf = segment_snapshots(c,s,country="France")
    assert cf.customer_id.tolist() == ["A"]
    assert set(sf.customer_id) == {"A"}
