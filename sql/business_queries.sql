-- Run against warehouse/subscriptioniq.db using SQLite.
-- 1) Latest MRR by country (filtered to paying snapshots)
SELECT c.country, SUM(s.mrr_eur) AS mrr_eur, COUNT(*) AS active_customers
FROM fct_subscription_snapshots s
JOIN dim_customers c ON c.customer_id = s.customer_id
WHERE s.month = (SELECT MAX(month) FROM fct_subscription_snapshots) AND s.mrr_eur > 0
GROUP BY c.country ORDER BY mrr_eur DESC;

-- 2) Top acquisition channels by current MRR
SELECT c.channel, SUM(s.mrr_eur) AS latest_mrr_eur
FROM fct_subscription_snapshots s
JOIN dim_customers c ON c.customer_id = s.customer_id
WHERE s.month = (SELECT MAX(month) FROM fct_subscription_snapshots)
GROUP BY c.channel ORDER BY latest_mrr_eur DESC;

-- 3) Monthly retention and revenue bridge
SELECT month, starting_mrr, new_mrr, expansion_mrr, reactivation_mrr,
       contraction_mrr, churned_mrr, ending_mrr, net_revenue_retention_pct
FROM mart_monthly_revenue ORDER BY month DESC;
