"""Sample sales orders, KPI math, and checks that gate the dashboard.

Unit cost is drawn as a share of unit price so gross profit stays
non-negative. Overview margin is total profit divided by total revenue,
not the mean of line-level margins.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

CATEGORIES = ["Electronics", "Clothing", "Home & Garden", "Sports", "Books"]
REGIONS = ["North America", "Europe", "Asia Pacific", "Latin America", "Middle East"]

REQUIRED_COLUMNS = [
    "order_date",
    "order_id",
    "product",
    "category",
    "region",
    "quantity",
    "unit_price",
    "unit_cost",
    "revenue",
    "cogs",
    "gross_profit",
    "margin_pct",
]

# Identities are stored at cent / tenth precision. Allow one rounding step.
MONEY_TOLERANCE = 0.01
MARGIN_TOLERANCE = 0.05


@dataclass(frozen=True)
class Check:
    name: str
    passed: bool
    failed_rows: int
    detail: str


def build_sample_orders(n: int = 10_000, seed: int = 42) -> pd.DataFrame:
    """Build a deterministic order frame the dashboard can render offline.

    Unit cost is 40-80% of unit price. The old generator drew cost on its
    own, so cost landed above price and gross profit went negative.
    """
    if n <= 0:
        raise ValueError("n must be positive")

    rng = np.random.default_rng(seed)
    dates = pd.date_range("2023-01-01", "2024-12-31", periods=n)
    unit_price = rng.uniform(10, 500, n).round(2)
    unit_cost = (unit_price * rng.uniform(0.40, 0.80, n)).round(2)
    quantity = rng.integers(1, 8, n)

    df = pd.DataFrame(
        {
            "order_date": rng.choice(dates.to_numpy(), n),
            "order_id": np.arange(1, n + 1),
            "product": [f"Product {chr(65 + i % 26)}{i % 50:02d}" for i in range(n)],
            "category": rng.choice(CATEGORIES, n, p=[0.30, 0.25, 0.20, 0.15, 0.10]),
            "region": rng.choice(REGIONS, n, p=[0.35, 0.28, 0.20, 0.10, 0.07]),
            "quantity": quantity,
            "unit_price": unit_price,
            "unit_cost": unit_cost,
        }
    )
    df["revenue"] = (df["quantity"] * df["unit_price"]).round(2)
    df["cogs"] = (df["quantity"] * df["unit_cost"]).round(2)
    df["gross_profit"] = (df["revenue"] - df["cogs"]).round(2)
    df["margin_pct"] = (df["gross_profit"] / df["revenue"] * 100).round(1)

    order_date = pd.to_datetime(df["order_date"])
    df["month"] = order_date.dt.to_period("M").astype(str)
    df["year"] = order_date.dt.year
    df["quarter"] = order_date.dt.to_period("Q").astype(str)
    return df


def kpi_summary(df: pd.DataFrame) -> dict:
    """KPIs for the overview tab.

    Gross margin is weighted by revenue. Averaging line-level margin_pct
    gives a $15 order the same vote as a $2,000 order.
    """
    if df.empty:
        return {
            "revenue": 0.0,
            "gross_profit": 0.0,
            "margin_pct": 0.0,
            "orders": 0,
            "aov": 0.0,
        }

    revenue = float(df["revenue"].sum())
    profit = float(df["gross_profit"].sum())
    orders = int(df["order_id"].nunique())
    return {
        "revenue": revenue,
        "gross_profit": profit,
        "margin_pct": (profit / revenue * 100) if revenue else 0.0,
        "orders": orders,
        "aov": (revenue / orders) if orders else 0.0,
    }


def _check(name: str, failed_rows: int, detail: str) -> Check:
    failed = int(failed_rows)
    return Check(name=name, passed=failed == 0, failed_rows=failed, detail=detail)


def validate_orders(df: pd.DataFrame) -> list[Check]:
    """Run the order-frame checks. An empty frame with the right columns passes."""
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        return [
            _check(
                "required_columns",
                len(missing),
                "missing columns: " + ", ".join(missing),
            )
        ]

    checks = [_check("required_columns", 0, "all required columns present")]

    null_counts = df[REQUIRED_COLUMNS].isna().sum()
    null_cols = [col for col, count in null_counts.items() if count]
    checks.append(
        _check(
            "no_nulls",
            int(null_counts.sum()),
            "nulls in " + ", ".join(null_cols) if null_cols else "no nulls",
        )
    )

    duplicate_ids = int(df["order_id"].duplicated().sum())
    checks.append(
        _check(
            "unique_order_id",
            duplicate_ids,
            f"{duplicate_ids} duplicate order ids",
        )
    )

    bad_qty = int((df["quantity"] <= 0).sum())
    checks.append(
        _check(
            "positive_quantity",
            bad_qty,
            f"{bad_qty} rows with quantity <= 0",
        )
    )

    bad_price = int((df["unit_price"] <= 0).sum())
    checks.append(
        _check(
            "positive_unit_price",
            bad_price,
            f"{bad_price} rows with unit_price <= 0",
        )
    )

    bad_cost = int((df["unit_cost"] < 0).sum())
    checks.append(
        _check(
            "non_negative_unit_cost",
            bad_cost,
            f"{bad_cost} rows with negative unit cost",
        )
    )

    cost_above_price = int((df["unit_cost"] > df["unit_price"]).sum())
    checks.append(
        _check(
            "cost_not_above_price",
            cost_above_price,
            f"{cost_above_price} rows where unit cost exceeds unit price",
        )
    )

    bad_revenue = int((df["revenue"] <= 0).sum())
    checks.append(
        _check(
            "positive_revenue",
            bad_revenue,
            f"{bad_revenue} rows with revenue <= 0",
        )
    )

    revenue_gap = (
        df["revenue"] - (df["quantity"] * df["unit_price"]).round(2)
    ).abs() > MONEY_TOLERANCE
    checks.append(
        _check(
            "revenue_identity",
            int(revenue_gap.sum()),
            f"{int(revenue_gap.sum())} rows where revenue != quantity * unit_price",
        )
    )

    cogs_gap = (
        df["cogs"] - (df["quantity"] * df["unit_cost"]).round(2)
    ).abs() > MONEY_TOLERANCE
    checks.append(
        _check(
            "cogs_identity",
            int(cogs_gap.sum()),
            f"{int(cogs_gap.sum())} rows where cogs != quantity * unit_cost",
        )
    )

    profit_gap = (
        df["gross_profit"] - (df["revenue"] - df["cogs"]).round(2)
    ).abs() > MONEY_TOLERANCE
    checks.append(
        _check(
            "profit_identity",
            int(profit_gap.sum()),
            f"{int(profit_gap.sum())} rows where gross_profit != revenue - cogs",
        )
    )

    positive_revenue = df["revenue"] > 0
    expected_margin = pd.Series(np.nan, index=df.index, dtype="float64")
    expected_margin.loc[positive_revenue] = (
        df.loc[positive_revenue, "gross_profit"]
        / df.loc[positive_revenue, "revenue"]
        * 100
    ).round(1)
    margin_gap = positive_revenue & (
        (df["margin_pct"] - expected_margin).abs() > MARGIN_TOLERANCE
    )
    checks.append(
        _check(
            "margin_identity",
            int(margin_gap.sum()),
            f"{int(margin_gap.sum())} rows where margin_pct does not match profit / revenue",
        )
    )

    bad_category = int((~df["category"].isin(CATEGORIES)).sum())
    checks.append(
        _check(
            "known_category",
            bad_category,
            f"{bad_category} rows with an unknown category",
        )
    )

    bad_region = int((~df["region"].isin(REGIONS)).sum())
    checks.append(
        _check(
            "known_region",
            bad_region,
            f"{bad_region} rows with an unknown region",
        )
    )

    parsed_dates = pd.to_datetime(df["order_date"], errors="coerce", format="mixed")
    bad_dates = int(parsed_dates.isna().sum())
    checks.append(
        _check(
            "order_date_parsed",
            bad_dates,
            f"{bad_dates} rows with an unparseable order_date",
        )
    )
    return checks


def main() -> int:
    df = build_sample_orders()
    checks = validate_orders(df)
    failed = [check for check in checks if not check.passed]
    for check in checks:
        status = "ok  " if check.passed else "FAIL"
        print(f"{status} {check.name}: {check.detail}")
    kpis = kpi_summary(df)
    print(
        f"orders={kpis['orders']} revenue={kpis['revenue']:.2f} "
        f"margin={kpis['margin_pct']:.2f}%"
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
