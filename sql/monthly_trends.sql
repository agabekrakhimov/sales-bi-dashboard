-- monthly_trends.sql
-- Monthly revenue trends with YoY comparison
-- Use in: Power BI (Custom SQL), Tableau (Custom SQL), Looker (raw SQL)

WITH monthly_data AS (
    SELECT
        DATE_TRUNC('month', order_date)                     AS month,
        product_category,
        SUM(line_total)                                     AS revenue,
        SUM(gross_profit)                                   AS gross_profit,
        COUNT(DISTINCT order_id)                            AS orders,
        COUNT(DISTINCT customer_id)                         AS unique_customers,
        ROUND(SUM(gross_profit) / NULLIF(SUM(line_total), 0) * 100, 2) AS margin_pct,
        ROUND(SUM(line_total) / NULLIF(COUNT(DISTINCT order_id), 0), 2) AS avg_order_value
    FROM marts.fct_orders
    WHERE order_date >= CURRENT_DATE - INTERVAL '24 months'
    GROUP BY 1, 2
),

with_yoy AS (
    SELECT
        m.*,
        LAG(m.revenue, 12) OVER (
            PARTITION BY m.product_category
            ORDER BY m.month
        )                                                   AS revenue_same_month_ly,
        ROUND(
            (m.revenue - LAG(m.revenue, 12) OVER (
                PARTITION BY m.product_category ORDER BY m.month
            )) / NULLIF(LAG(m.revenue, 12) OVER (
                PARTITION BY m.product_category ORDER BY m.month
            ), 0) * 100,
        2)                                                  AS revenue_yoy_pct
    FROM monthly_data m
)

SELECT *
FROM with_yoy
ORDER BY month DESC, revenue DESC;
