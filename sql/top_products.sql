-- top_products.sql
-- Top N products by revenue with rank and category context

WITH product_metrics AS (
    SELECT
        product_id,
        product_name,
        product_category,
        SUM(line_total)                                     AS revenue,
        SUM(gross_profit)                                   AS gross_profit,
        COUNT(DISTINCT order_id)                            AS orders,
        COUNT(DISTINCT customer_id)                         AS unique_customers,
        ROUND(SUM(gross_profit) / NULLIF(SUM(line_total), 0) * 100, 2) AS margin_pct,
        SUM(quantity)                                       AS units_sold,
        MIN(order_date)                                     AS first_sale_date,
        MAX(order_date)                                     AS last_sale_date
    FROM marts.fct_orders
    WHERE order_date >= CURRENT_DATE - INTERVAL '12 months'
    GROUP BY 1, 2, 3
),

ranked AS (
    SELECT
        *,
        RANK() OVER (ORDER BY revenue DESC)                 AS overall_rank,
        RANK() OVER (
            PARTITION BY product_category
            ORDER BY revenue DESC
        )                                                   AS category_rank,
        ROUND(revenue / SUM(revenue) OVER () * 100, 2)     AS pct_of_total_revenue
    FROM product_metrics
)

SELECT *
FROM ranked
WHERE overall_rank <= 50
ORDER BY overall_rank;
