"""The dashboard wires the order checks and survives an empty filter."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

from sales_quality import build_sample_orders, kpi_summary

APP = Path(__file__).resolve().parents[1] / "app.py"


def _run():
    app = AppTest.from_file(str(APP), default_timeout=60)
    app.run()
    return app


def test_overview_shows_passing_checks_and_weighted_margin():
    app = _run()
    assert list(app.exception) == []
    assert "15 data checks passed" in [item.value for item in app.sidebar.caption]
    expected = f"{kpi_summary(build_sample_orders())['margin_pct']:.1f}%"
    shown = next(item.value for item in app.metric if "Gross Margin" in item.label)
    assert shown == expected


def test_clearing_the_year_filter_does_not_crash():
    app = _run()
    app.sidebar.multiselect[0].set_value([]).run()
    assert list(app.exception) == []
    assert any("No orders match" in item.value for item in app.info)
