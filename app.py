"""Streamlit frontend. Run: streamlit run app.py"""
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st
from subscriptioniq.metrics import monthly_metrics, cohort_retention, segment_snapshots

st.set_page_config(page_title="SubscriptionIQ | SaaS Analytics", page_icon="📈", layout="wide")
st.title("📈 SubscriptionIQ")
st.caption("SaaS Revenue Intelligence & Cohort Analytics | Reproducible synthetic subscription data")
st.info("Portfolio demonstration. All customers, subscriptions, and amounts are fictional.")

@st.cache_data

def load_data():
    p = Path(__file__).resolve().parent / "data"
    return pd.read_csv(p / "customers.csv"), pd.read_csv(p / "subscription_snapshots.csv")

try:
    customers, snapshots = load_data()
except FileNotFoundError:
    st.error("Data missing. Run: python -m subscriptioniq.cli generate")
    st.stop()

st.sidebar.header("Customer segment")
channel = st.sidebar.selectbox("Acquisition channel", ["All"] + sorted(customers.channel.unique().tolist()))
country = st.sidebar.selectbox("Country", ["All"] + sorted(customers.country.unique().tolist()))
segment = st.sidebar.selectbox("Segment", ["All"] + sorted(customers.segment.unique().tolist()))
customers, snapshots = segment_snapshots(customers, snapshots, channel=channel, country=country, segment=segment)
if customers.empty:
    st.warning("No customers match these filters")
    st.stop()
kpis = monthly_metrics(customers, snapshots)
cohorts = cohort_retention(customers, snapshots)
last, prior = kpis.iloc[-1], kpis.iloc[-2] if len(kpis) > 1 else kpis.iloc[-1]
metrics = st.columns(4)
metrics[0].metric("MRR", f"€{last.ending_mrr:,.0f}", f"€{last.ending_mrr-prior.ending_mrr:+,.0f} MoM")
metrics[1].metric("ARR (run rate)", f"€{last.arr_eur:,.0f}")
metrics[2].metric("Active customers", f"{last.active_customers:,.0f}")
metrics[3].metric("Net revenue retention", "N/A" if pd.isna(last.net_revenue_retention_pct) else f"{last.net_revenue_retention_pct:.1f}%")

tab1, tab2, tab3, tab4 = st.tabs(["Revenue trend", "MRR bridge", "Cohort retention", "Audit table"])
with tab1:
    fig = px.line(kpis, x="month", y="ending_mrr", title="Monthly recurring revenue", markers=True, labels={"month":"Month", "ending_mrr":"MRR (€)"})
    st.plotly_chart(fig, use_container_width=True)
    left, right = st.columns(2)
    with left:
        st.plotly_chart(px.line(kpis, x="month", y=["net_revenue_retention_pct", "gross_revenue_retention_pct"], title="Revenue retention (%)"), use_container_width=True)
    with right:
        st.plotly_chart(px.bar(kpis, x="month", y="active_customers", title="Paying customers"), use_container_width=True)
with tab2:
    focus = st.selectbox("Selected reporting month", kpis.month.tolist(), index=len(kpis) - 1)
    r = kpis.set_index("month").loc[focus]
    bridge = pd.DataFrame({"Component": ["Beginning", "New", "Expansion", "Reactivation", "Contraction", "Churn", "Ending"], "MRR (€)": [r.starting_mrr, r.new_mrr, r.expansion_mrr, r.reactivation_mrr, -r.contraction_mrr, -r.churned_mrr, r.ending_mrr]})
    st.dataframe(bridge, hide_index=True, use_container_width=True)
    st.caption("Ending MRR = Beginning + New + Expansion + Reactivation − Contraction − Churn")
with tab3:
    if not cohorts.empty:
        matrix = cohorts.pivot(index="cohort", columns="age_months", values="retention_pct")
        st.plotly_chart(px.imshow(matrix, title="Customer logo retention by first paid month (%)", aspect="auto", color_continuous_scale="Blues", labels={"x":"Months since first paid", "y":"Acquisition cohort", "color":"Retained %"}), use_container_width=True)
        st.caption("Cohort size counts customers first paying in that month. Logo retention is active customers divided by original cohort size; reactivations count as retained in later months.")
with tab4:
    st.dataframe(kpis, use_container_width=True, hide_index=True)
    st.download_button("Download filtered KPIs (CSV)", kpis.to_csv(index=False), file_name="subscriptioniq_kpis.csv", mime="text/csv")
    st.download_button("Download filtered cohort data (CSV)", cohorts.to_csv(index=False), file_name="subscriptioniq_cohorts.csv", mime="text/csv")

st.caption("Definitions: ARR is 12 × current MRR, not recognized revenue. NRR/GRR use beginning-of-month MRR and exclude new and reactivated revenue from the numerator.")
