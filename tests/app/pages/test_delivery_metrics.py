from datetime import date, datetime, timezone

import pytest

from delivery_metrics import domain
from pages import delivery_metrics
from pages.delivery_metrics import (
    main,
    scatter_chart,
    shewhart_chart_with_trend_and_residual_limits,
)


def _repo():
    return domain.Repo(
        org="opensafely-core",
        name="repo",
    )


@pytest.mark.slow
def test_app():
    from streamlit.testing.v1 import AppTest

    class FakeRepository:
        def get_interesting_prs(self):
            return []

    app_test = AppTest.from_function(main, args=(FakeRepository(),))
    app_test.run(timeout=10)
    assert not app_test.exception


def test_xmr_chart_from_series_is_removed():
    assert not hasattr(delivery_metrics, "xmr_chart_from_series")


def test_shewhart_chart_with_trend_and_residual_limits_includes_trend_line():
    chart = shewhart_chart_with_trend_and_residual_limits(
        [
            domain.datapoint(date(2024, 1, 1), value=0.40),
            domain.datapoint(date(2024, 1, 8), value=0.45),
            domain.datapoint(date(2024, 1, 15), value=0.50),
            domain.datapoint(date(2024, 1, 22), value=0.55),
        ],
        value_field="value",
        y_label="Closed within 2 days (trend)",
    )
    spec = chart.to_dict()

    trend_layer = next(
        layer
        for layer in spec["layer"]
        if isinstance(layer.get("mark"), dict)
        and layer["mark"].get("type") == "line"
        and layer["mark"].get("strokeDash") == [6, 3]
    )
    assert trend_layer["mark"].get("color") == "#4c78a8"
    assert trend_layer["mark"].get("strokeDash") == [6, 3]
    highlight_layer = next(
        layer
        for layer in spec["layer"]
        if isinstance(layer.get("mark"), dict) and layer["mark"].get("type") == "point"
    )
    assert highlight_layer["encoding"]["tooltip"][-1]["field"] == "signal_rules"


def test_shewhart_chart_with_trend_and_residual_limits_clips_limits_to_bounds():
    chart = shewhart_chart_with_trend_and_residual_limits(
        [
            domain.datapoint(date(2024, 1, 1), value=0.95),
            domain.datapoint(date(2024, 1, 8), value=0.20),
            domain.datapoint(date(2024, 1, 15), value=0.95),
            domain.datapoint(date(2024, 1, 22), value=0.20),
        ],
        value_field="value",
        y_label="Closed within 2 days (trend)",
        lower_bound=0.0,
        upper_bound=1.0,
    )
    values = chart.to_dict()["layer"][0]["data"]["values"]
    assert all(item["ucl"] <= 1.0 for item in values)
    assert all(item["lcl"] >= 0.0 for item in values)


def test_shewhart_chart_with_trend_and_residual_limits_uses_residual_spc_rules(
    monkeypatch,
):
    def fake_detect_spc_signals(values, mean, ucl, lcl):
        assert mean == 0.0
        assert ucl >= 0.0
        assert lcl <= 0.0
        return [
            set(),
            {domain.SPC_RULE_RUN_8_SAME_SIDE},
            set(),
            set(),
        ]

    monkeypatch.setattr(
        "pages.delivery_metrics.domain.detect_spc_signals",
        fake_detect_spc_signals,
    )

    chart = shewhart_chart_with_trend_and_residual_limits(
        [
            domain.datapoint(date(2024, 1, 1), value=0.40),
            domain.datapoint(date(2024, 1, 8), value=0.45),
            domain.datapoint(date(2024, 1, 15), value=0.50),
            domain.datapoint(date(2024, 1, 22), value=0.55),
        ],
        value_field="value",
        y_label="Closed within 2 days (trend)",
    )
    values = chart.to_dict()["layer"][0]["data"]["values"]

    assert values[1]["signal"] is True
    assert domain.SPC_RULE_RUN_8_SAME_SIDE in values[1]["signal_rules"]


def test_shewhart_chart_with_trend_and_residual_limits_adds_point_beyond_rule():
    chart = shewhart_chart_with_trend_and_residual_limits(
        [
            domain.datapoint(date(2024, 1, 1), value=2.0),
            domain.datapoint(date(2024, 1, 8), value=2.0),
        ],
        value_field="value",
        y_label="Closed within 2 days (trend)",
        lower_bound=0.0,
        upper_bound=1.0,
    )
    values = chart.to_dict()["layer"][0]["data"]["values"]

    assert all(
        domain.SPC_RULE_POINT_BEYOND_LIMITS in item["signal_rules"] for item in values
    )


def test_scatter_chart_includes_open_merged_and_abandoned_categories():
    repo = _repo()
    open_pr = domain.PR(
        repo=repo,
        author="dev",
        created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        merged_at=None,
        closed_at=None,
        is_draft=False,
        is_content=False,
    )
    merged_pr = domain.PR(
        repo=repo,
        author="dev",
        created_at=datetime(2024, 1, 2, tzinfo=timezone.utc),
        merged_at=datetime(2024, 1, 3, tzinfo=timezone.utc),
        closed_at=datetime(2024, 1, 3, tzinfo=timezone.utc),
        is_draft=False,
        is_content=False,
    )
    abandoned_pr = domain.PR(
        repo=repo,
        author="dev",
        created_at=datetime(2024, 1, 4, tzinfo=timezone.utc),
        merged_at=None,
        closed_at=datetime(2024, 1, 5, tzinfo=timezone.utc),
        is_draft=False,
        is_content=False,
    )

    chart = scatter_chart([open_pr, merged_pr, abandoned_pr], date(2024, 1, 7))
    values = chart.to_dict()["data"]["values"]
    categories = {item["category"] for item in values}
    assert categories == {"open", "merged", "abandoned"}
