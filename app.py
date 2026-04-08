"""
app.py
------
Sales Performance BI Dashboard — main Streamlit entry point.

Run: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Sales BI Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .kpi-card {
        background: #f0f7f4;
        border-left: 4px solid #2D6A4F;
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 10px;
    }
    .kpi-value { font-size: 28px; font-weight: 700; color: #1b4332; }
    .kpi-label { font-size: 13px; color: #555; margin-bottom: 4px; }
    .kpi-delta-pos { color: #2D6A4F; font-size: 13px; }
    .kpi-delta-neg { color: #c0392b; font-size: 13px; }
    h1, h2, h3 { color: #1b4332; }
</style>
""", unsafe_allow_html=True)


# ── Data loading ──────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    """Load sample data or connect to DB."""
    np.random.seed(42)
    n = 10_000

    dates = pd.date_range("2023-01-01", "2024-12-31", periods=n)
    categories = ["Electronics", "Clothing", "Home & Garden", "Sports", "Books"]
    regions    = ["North America", "Europe", "Asia Pacific", "Latin America", "Middle East"]

    df = pd.DataFrame({
        "order_date":    np.random.choice(dates, n),
        "order_id":      range(1, n + 1),
        "product":       [f"Product {chr(65 + i % 26)}{i % 50:02d}" for i in range(n)],
        "category":      np.random.choice(categories, n, p=[0.30, 0.25, 0.20, 0.15, 0.10]),
        "region":        np.random.choice(regions, n, p=[0.35, 0.28, 0.20, 0.10, 0.07]),
        "quantity":      np.random.randint(1, 8, n),
        "unit_price":    np.random.uniform(10, 500, n).round(2),
        "unit_cost":     np.random.uniform(5, 250, n).round(2),
    })

    df["revenue"]      = (df["quantity"] * df["unit_price"]).round(2)
    df["cogs"]         = (df["quantity"] * df["unit_cost"]).round(2)
    df["gross_profit"] = (df["revenue"] - df["cogs"]).round(2)
    df["margin_pct"]   = (df["gross_profit"] / df["revenue"] * 100).round(1)
    df["month"]        = pd.to_datetime(df["order_date"]).dt.to_period("M").astype(str)
    df["year"]         = pd.to_datetime(df["order_date"]).dt.year
    df["quarter"]      = pd.to_datetime(df["order_date"]).dt.to_period("Q").astype(str)
    return df


df = load_data()

# ── Sidebar filters ───────────────────────────────────────────────────────────
st.sidebar.image("https://img.icons8.com/color/48/bar-chart.png", width=48)
st.sidebar.title("Filters")

year_options = sorted(df["year"].unique())
selected_years = st.sidebar.multiselect("Year", year_options, default=year_options)

category_options = df["category"].unique()
selected_cats = st.sidebar.multiselect("Category", category_options, default=list(category_options))

region_options = df["region"].unique()
selected_regions = st.sidebar.multiselect("Region", region_options, default=list(region_options))

# Apply filters
mask = (
    df["year"].isin(selected_years) &
    df["category"].isin(selected_cats) &
    df["region"].isin(selected_regions)
)
filtered = df[mask]

st.sidebar.markdown("---")
st.sidebar.markdown(f"**{len(filtered):,}** orders selected")
st.sidebar.markdown("Built by [Ogabek Rakhimov](https://www.linkedin.com/in/ogabekrakhimov/)")

# ── Header ────────────────────────────────────────────────────────────────────
st.title("📊 Sales Performance Dashboard")
st.caption("Interactive BI dashboard — filter by year, category, and region using the sidebar.")

tab1, tab2, tab3, tab4 = st.tabs(["🏠 Overview", "📈 Trends", "📦 Products", "🌍 Regional"])

# ── TAB 1: Overview (KPIs) ────────────────────────────────────────────────────
with tab1:
    st.subheader("Executive KPIs")

    total_rev  = filtered["revenue"].sum()
    total_prof = filtered["gross_profit"].sum()
    avg_margin = filtered["margin_pct"].mean()
    total_ord  = filtered["order_id"].nunique()
    aov        = total_rev / total_ord if total_ord > 0 else 0

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("💰 Total Revenue", f"${total_rev:,.0f}", delta="vs last period")
    with col2:
        st.metric("📈 Gross Profit", f"${total_prof:,.0f}")
    with col3:
        st.metric("📊 Avg Margin", f"{avg_margin:.1f}%")
    with col4:
        st.metric("🛒 Total Orders", f"{total_ord:,}")
    with col5:
        st.metric("💳 Avg Order Value", f"${aov:,.2f}")

    st.markdown("---")

    col_a, col_b = st.columns(2)
    with col_a:
        cat_rev = filtered.groupby("category")["revenue"].sum().sort_values(ascending=False)
        fig = px.pie(
            values=cat_rev.values, names=cat_rev.index,
            title="Revenue by Category",
            color_discrete_sequence=px.colors.sequential.Greens_r
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        reg_rev = filtered.groupby("region")["revenue"].sum().sort_values()
        fig = px.bar(
            x=reg_rev.values, y=reg_rev.index,
            orientation="h",
            title="Revenue by Region",
            color=reg_rev.values,
            color_continuous_scale="Greens",
            labels={"x": "Revenue (USD)", "y": ""}
        )
        fig.update_coloraxes(showscale=False)
        st.plotly_chart(fig, use_container_width=True)


# ── TAB 2: Trends ─────────────────────────────────────────────────────────────
with tab2:
    st.subheader("Revenue & Profit Trends")

    monthly = (
        filtered.groupby("month")
        .agg(revenue=("revenue", "sum"), profit=("gross_profit", "sum"), orders=("order_id", "count"))
        .reset_index()
        .sort_values("month")
    )

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=monthly["month"], y=monthly["revenue"],
        name="Revenue", line=dict(color="#2D6A4F", width=2.5),
        fill="tozeroy", fillcolor="rgba(45,106,79,0.1)"
    ))
    fig.add_trace(go.Scatter(
        x=monthly["month"], y=monthly["profit"],
        name="Gross Profit", line=dict(color="#52B788", width=2, dash="dot")
    ))
    fig.update_layout(
        title="Monthly Revenue vs Gross Profit",
        xaxis_title="Month", yaxis_title="Amount (USD)",
        hovermode="x unified", legend=dict(orientation="h", y=-0.2)
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    col_a, col_b = st.columns(2)
    with col_a:
        qtr = (
            filtered.groupby(["quarter", "category"])["revenue"]
            .sum().reset_index()
        )
        fig = px.bar(
            qtr, x="quarter", y="revenue", color="category",
            title="Quarterly Revenue by Category",
            color_discrete_sequence=px.colors.sequential.Greens_r
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        monthly_orders = (
            filtered.groupby("month")["order_id"].count().reset_index()
            .sort_values("month")
        )
        fig = px.line(
            monthly_orders, x="month", y="order_id",
            title="Monthly Order Volume",
            markers=True, color_discrete_sequence=["#2D6A4F"]
        )
        st.plotly_chart(fig, use_container_width=True)


# ── TAB 3: Products ───────────────────────────────────────────────────────────
with tab3:
    st.subheader("Product Performance")

    prod_perf = (
        filtered.groupby(["product", "category"])
        .agg(revenue=("revenue", "sum"), profit=("gross_profit", "sum"), orders=("order_id", "count"))
        .reset_index()
        .nlargest(15, "revenue")
    )

    fig = px.bar(
        prod_perf, x="revenue", y="product",
        orientation="h", color="category",
        title="Top 15 Products by Revenue",
        color_discrete_sequence=px.colors.sequential.Greens_r
    )
    st.plotly_chart(fig, use_container_width=True)

    col_a, col_b = st.columns(2)
    with col_a:
        cat_margin = filtered.groupby("category")["margin_pct"].mean().reset_index()
        fig = px.bar(
            cat_margin.sort_values("margin_pct", ascending=False),
            x="category", y="margin_pct",
            title="Average Gross Margin by Category (%)",
            color="margin_pct", color_continuous_scale="Greens"
        )
        fig.update_coloraxes(showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        fig = px.scatter(
            filtered.groupby("category").agg(
                revenue=("revenue", "sum"),
                margin=("margin_pct", "mean"),
                orders=("order_id", "count")
            ).reset_index(),
            x="revenue", y="margin",
            size="orders", color="category",
            title="Revenue vs Margin (bubble = order volume)",
            color_discrete_sequence=px.colors.qualitative.Safe
        )
        st.plotly_chart(fig, use_container_width=True)


# ── TAB 4: Regional ───────────────────────────────────────────────────────────
with tab4:
    st.subheader("Regional Breakdown")

    reg_detail = (
        filtered.groupby("region")
        .agg(
            revenue=("revenue", "sum"),
            profit=("gross_profit", "sum"),
            orders=("order_id", "count"),
            margin=("margin_pct", "mean")
        )
        .reset_index()
        .sort_values("revenue", ascending=False)
    )
    reg_detail["aov"] = (reg_detail["revenue"] / reg_detail["orders"]).round(2)

    st.dataframe(
        reg_detail.style.format({
            "revenue": "${:,.0f}",
            "profit":  "${:,.0f}",
            "orders":  "{:,}",
            "margin":  "{:.1f}%",
            "aov":     "${:,.2f}",
        }),
        use_container_width=True,
        hide_index=True
    )

    fig = px.treemap(
        filtered, path=["region", "category"],
        values="revenue",
        title="Revenue Treemap: Region → Category",
        color="revenue",
        color_continuous_scale="Greens"
    )
    st.plotly_chart(fig, use_container_width=True)
