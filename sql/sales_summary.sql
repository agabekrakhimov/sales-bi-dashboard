-- sales_summary.sql
-- Executive KPIs for the current period vs. previous period
-- Compatible with: PostgreSQL, Redshift, Snowflake, BigQuery*
-- *BigQuery: replace DATE_TRUNC with DATE_TRUNC(date, MONTH)

WITH current_period AS (
    SELECT
        COUNT(DISTINCT order_id)                            AS orders,
        SUM(line_total)                                     AS revenue,
        SUM(gross_profit)                                   AS gross_profit,
        ROUND(SUM(gross_profit) / NULLIF(SUM(line_total), 0) * 100, 2) AS margin_pct,
        ROUND(SUM(line_total) / NULLIF(COUNT(DISTINCT order_id), 0), 2) AS avg_order_value,
        COUNT(DISTINCT customer_id)                         AS unique_customers
    FROM marts.fct_orders
    WHERE order_date >= DATE_TRUNC('month', CURRENT_DATE)
      AND order_date <  CURRENT_DATE
),

previous_period AS (
    SELECT
        COUNT(DISTINCT order_id)                            AS orders,
        SUM(line_total)                                     AS revenue,
        SUM(gross_profit)                                   AS gross_profit,
        ROUND(SUM(gross_profit) / NULLIF(SUM(line_total), 0) * 100, 2) AS margin_pct,
        ROUND(SUM(line_total) / NULLIF(COUNT(DISTINCT order_id), 0), 2) AS avg_order_value,
        COUNT(DISTINCT customer_id)                         AS unique_customers
    FROM marts.fct_orders
    WHERE order_date >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month')
      AND order_date <  DATE_TRUNC('month', CURRENT_DATE)
)

SELECT
    c.revenue                                               AS revenue_current,
    p.revenue                                               AS revenue_previous,
    ROUND((c.revenue - p.revenue) / NULLIF(p.revenue, 0) * 100, 2) AS revenue_mom_pct,

    c.gross_profit                                          AS profit_current,
    c.margin_pct                                            AS margin_current,

    c.orders                                                AS orders_current,
    ROUND((c.orders - p.orders)::NUMERIC / NULLIF(p.orders, 0) * 100, 2) AS orders_mom_pct,

    c.avg_order_value                                       AS aov_current,
    c.unique_customers                                      AS customers_current

FROM current_period  c
CROSS JOIN previous_period p;
