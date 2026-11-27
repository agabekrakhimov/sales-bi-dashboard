# 📊 Sales Performance BI Dashboard

An interactive **Business Intelligence dashboard** built with Python and Streamlit, visualizing key sales KPIs, product performance, regional trends, and customer segments — with SQL queries ready to connect to your data warehouse.

> **Live Demo:** Run locally in under 2 minutes with Docker or pip.

---

## 🖥️ Dashboard Preview

The dashboard features 4 pages:

| Page | Content |
|------|---------|
| **Executive Overview** | Revenue, orders, AOV, profit margin KPI cards |
| **Sales Trends** | Monthly/quarterly revenue with YoY comparison |
| **Product Performance** | Top products, category breakdown, margin analysis |
| **Regional Analysis** | Revenue by country/region with growth rates |

---

## 📦 Tech Stack

| Tool | Purpose |
|------|---------|
| **Streamlit** | Interactive web dashboard |
| **Plotly** | Interactive charts and graphs |
| **pandas** | Data manipulation |
| **SQLAlchemy** | Database connectivity |
| **PostgreSQL** | Production data warehouse |

---

## 📂 Project Structure

```
sales-bi-dashboard/
├── app.py                     # Main Streamlit app entry point
├── sales_quality.py           # Sample orders, KPI math, data checks
├── tests/
│   └── test_sales_quality.py  # pytest coverage for the checks and KPIs
├── requirements-dev.txt       # Test dependencies
├── .github/workflows/ci.yml   # Runs pytest on pull requests
├── components/
│   ├── kpi_cards.py           # KPI metric card components
│   ├── sales_charts.py        # Revenue & trend charts
│   ├── product_charts.py      # Product performance charts
│   └── regional_charts.py     # Geographic charts
├── sql/
│   ├── sales_summary.sql      # Executive KPI queries
│   ├── monthly_trends.sql     # Time series queries
│   ├── top_products.sql       # Product ranking queries
│   └── regional_breakdown.sql # Geographic breakdown
├── data/
│   └── generate_sample_data.py # Sample data generator
├── requirements.txt
└── .streamlit/
    └── config.toml             # Streamlit theming
```

---

## 🚀 Getting Started

### Option A: pip install

```bash
# 1. Clone the repo
git clone https://github.com/agabekrakhimov/sales-bi-dashboard.git
cd sales-bi-dashboard

# 2. Install dependencies
pip install -r requirements.txt

# 3. Optional: check the sample orders (no database)
python sales_quality.py

# 4. Run the dashboard
streamlit run app.py
```

`pyarrow` is pinned to 15.0.2. Current pyarrow builds require NumPy 2, and this project stays on NumPy 1.26. Without the pin, a fresh install fails when Streamlit imports.

Open [http://localhost:8501](http://localhost:8501) in your browser. The app builds the sample frame itself.

### Run the tests

```bash
pip install -r requirements-dev.txt
pytest
```

GitHub Actions installs `requirements-dev.txt` and runs the same suite on every pull request and on pushes to `main`.

### Option B: Connect to your data warehouse

Edit `.env`:
```env
DB_HOST=your-warehouse-host
DB_PORT=5432
DB_NAME=your_database
DB_USER=your_user
DB_PASSWORD=your_password
```

Then set `USE_LIVE_DB=true` in `app.py`.

---

## Data checks

`sales_quality.py` is the piece the dashboard reads before it draws charts.

The sample used to draw unit cost on its own range. Cost often landed above price, so gross profit and margin went negative with nothing to flag it. The overview "average margin" was also the mean of line-level percentages, which gives a $15 order the same weight as a $2,000 order.

What it does now:

- `build_sample_orders` sets unit cost to 40–80% of unit price, so sample gross profit stays non-negative. Same seed, same frame.
- `validate_orders` checks the frame the sidebar reports on: required columns, nulls, unique order ids, positive quantity and price, non-negative cost, cost not above price, and the revenue, COGS, profit, and margin identities. Unknown categories, unknown regions, and bad dates fail too.
- `kpi_summary` computes gross margin as total gross profit / total revenue. An empty filter shows "No orders match these filters." instead of sending empty series into the charts.

`python sales_quality.py` prints each check and the headline KPIs. A failed check exits non-zero. The dashboard shows the same result in the sidebar.

## 🔍 SQL Queries

All business logic lives in clean, reusable SQL files you can drop directly into Power BI, Tableau, or Looker.

### Example — Monthly Revenue Trend
```sql
SELECT
    DATE_TRUNC('month', order_date)   AS month,
    SUM(line_total)                   AS revenue,
    SUM(gross_profit)                 AS profit,
    COUNT(DISTINCT order_id)          AS orders,
    ROUND(SUM(line_total) /
          COUNT(DISTINCT order_id), 2) AS avg_order_value
FROM marts.fct_orders
WHERE order_date >= DATEADD(month, -13, CURRENT_DATE)
GROUP BY 1
ORDER BY 1;
```

---

## 📈 KPIs Tracked

- **Total Revenue** (with MoM % change)
- **Gross Profit Margin**
- **Average Order Value (AOV)**
- **Order Volume**
- **Customer Retention Rate**
- **Top 10 Products by Revenue**
- **Revenue by Region**

---

## 🔗 Connecting to Power BI / Tableau

The SQL files in `/sql` are dialect-compatible with:
- PostgreSQL / Redshift
- Snowflake (minor syntax adjustments noted in comments)
- BigQuery (partition syntax noted)
- Databricks SQL

To use with **Power BI**: Import the SQL queries via `Get Data → PostgreSQL`.
To use with **Tableau**: Connect via native PostgreSQL connector and use Custom SQL.

---

## 🤝 Connect

**Ogabek Rakhimov** — [LinkedIn](https://www.linkedin.com/in/ogabekrakhimov/) | [GitHub](https://github.com/agabekrakhimov)
