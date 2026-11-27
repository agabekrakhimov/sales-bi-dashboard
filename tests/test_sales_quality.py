"""Checks for the sample order frame and the overview KPIs."""

import numpy as np
import pandas as pd
import pytest

from sales_quality import build_sample_orders, kpi_summary, validate_orders


def _by_name(df):
    return {check.name: check for check in validate_orders(df)}


def test_sample_is_deterministic():
    first = build_sample_orders(200, seed=7)
    second = build_sample_orders(200, seed=7)
    pd.testing.assert_frame_equal(first, second)


def test_default_sample_passes_every_check():
    df = build_sample_orders()
    assert len(df) == 10_000
    assert df["order_id"].is_unique
    assert (df["unit_cost"] <= df["unit_price"]).all()
    assert (df["gross_profit"] >= 0).all()
    failed = [check.name for check in validate_orders(df) if not check.passed]
    assert failed == []


def test_empty_frame_passes_and_kpis_are_zero():
    df = build_sample_orders(20, seed=1).iloc[0:0]
    assert [check.name for check in validate_orders(df) if not check.passed] == []
    summary = kpi_summary(df)
    assert summary == {
        "revenue": 0.0,
        "gross_profit": 0.0,
        "margin_pct": 0.0,
        "orders": 0,
        "aov": 0.0,
    }


def test_margin_is_weighted_by_revenue():
    # Line margins are 50% and 10%. An unweighted mean is 30%.
    # Profit is 140 on 1,000 revenue, so the dashboard margin is 14%.
    df = pd.DataFrame(
        {
            "order_id": [1, 2],
            "revenue": [100.0, 900.0],
            "gross_profit": [50.0, 90.0],
        }
    )
    summary = kpi_summary(df)
    assert summary["margin_pct"] == pytest.approx(14.0)
    assert summary["aov"] == pytest.approx(500.0)
    assert summary["orders"] == 2


def test_duplicate_order_ids_count_once_in_aov():
    df = pd.DataFrame(
        {
            "order_id": [1, 1],
            "revenue": [40.0, 60.0],
            "gross_profit": [10.0, 10.0],
        }
    )
    summary = kpi_summary(df)
    assert summary["orders"] == 1
    assert summary["aov"] == pytest.approx(100.0)


def test_missing_column_stops_before_later_checks():
    df = build_sample_orders(10, seed=1).drop(columns=["revenue"])
    checks = validate_orders(df)
    assert len(checks) == 1
    assert checks[0].name == "required_columns"
    assert not checks[0].passed
    assert "revenue" in checks[0].detail


def test_null_order_id_fails():
    df = build_sample_orders(30, seed=2)
    df.loc[0, "order_id"] = np.nan
    check = _by_name(df)["no_nulls"]
    assert not check.passed
    assert check.failed_rows >= 1


def test_duplicate_order_id_fails():
    df = build_sample_orders(30, seed=2)
    df.loc[1, "order_id"] = df.loc[0, "order_id"]
    check = _by_name(df)["unique_order_id"]
    assert not check.passed
    assert check.failed_rows == 1


def test_non_positive_quantity_fails():
    df = build_sample_orders(30, seed=2)
    df.loc[0, "quantity"] = 0
    assert not _by_name(df)["positive_quantity"].passed


def test_non_positive_price_fails():
    df = build_sample_orders(30, seed=2)
    df.loc[0, "unit_price"] = 0
    assert not _by_name(df)["positive_unit_price"].passed


def test_negative_unit_cost_fails():
    df = build_sample_orders(30, seed=2)
    df.loc[0, "unit_cost"] = -1
    assert not _by_name(df)["non_negative_unit_cost"].passed


def test_cost_above_price_fails():
    df = build_sample_orders(30, seed=2)
    df.loc[0, "unit_cost"] = df.loc[0, "unit_price"] + 5
    check = _by_name(df)["cost_not_above_price"]
    assert not check.passed
    assert check.failed_rows == 1


def test_revenue_identity_fails_when_revenue_is_edited():
    df = build_sample_orders(30, seed=2)
    df.loc[0, "revenue"] = df.loc[0, "revenue"] + 25
    assert not _by_name(df)["revenue_identity"].passed


def test_cogs_identity_fails_when_cogs_is_edited():
    df = build_sample_orders(30, seed=2)
    df.loc[0, "cogs"] = df.loc[0, "cogs"] + 10
    assert not _by_name(df)["cogs_identity"].passed


def test_profit_identity_fails_when_profit_is_edited():
    df = build_sample_orders(30, seed=2)
    df.loc[0, "gross_profit"] = df.loc[0, "gross_profit"] + 8
    assert not _by_name(df)["profit_identity"].passed


def test_margin_identity_fails_when_margin_is_edited():
    df = build_sample_orders(30, seed=2)
    df.loc[0, "margin_pct"] = df.loc[0, "margin_pct"] + 5
    assert not _by_name(df)["margin_identity"].passed


def test_unknown_category_and_region_fail():
    df = build_sample_orders(30, seed=2)
    df.loc[0, "category"] = "Toys"
    df.loc[1, "region"] = "Antarctica"
    checks = _by_name(df)
    assert not checks["known_category"].passed
    assert not checks["known_region"].passed


def test_unparseable_order_date_fails():
    df = build_sample_orders(30, seed=2)
    df["order_date"] = df["order_date"].astype(str)
    df.loc[0, "order_date"] = "not-a-date"
    assert not _by_name(df)["order_date_parsed"].passed


def test_build_rejects_non_positive_n():
    with pytest.raises(ValueError):
        build_sample_orders(0)
