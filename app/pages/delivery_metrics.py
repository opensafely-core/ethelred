import itertools
import os
import pathlib
import statistics
from datetime import date

import altair

from delivery_metrics import domain
from delivery_metrics.repository import Repository


DEFAULT_WIDTH = 600
DEFAULT_HEIGHT = 150
SCATTER_HEIGHT = 300
LABEL_WIDTH = 60
AXIS_LABEL_COLOR = "#6b6b6b"


def main(repository):  # pragma: no cover  # called in subprocess in tests

    import datetime as dt

    import streamlit

    from delivery_metrics import domain
    from pages import delivery_metrics as page

    today = dt.date.today()
    interesting_prs = repository.get_interesting_prs()
    unabandoned_prs = [pr for pr in interesting_prs if not pr.was_abandoned()]

    weekly_windows = domain.build_weekly_windows(
        domain.START_DATE, today - domain.ONE_DAY
    )
    prs_open_by_day, prs_opened_by_day = domain.categorise_prs(
        unabandoned_prs, today=today
    )

    streamlit.title("Ethelred: Delivery Metrics")
    page.write_charts(
        page.with_y_label(
            page.scatter_chart(interesting_prs, today),
            "Age (days)",
            page.SCATTER_HEIGHT,
        ),
        page.with_y_label(
            page.count_chart("Opened per day", prs_opened_by_day, weekly_windows),
            "Opened per day",
            page.DEFAULT_HEIGHT,
        ),
        page.with_y_label(
            page.count_chart("Open at end of day", prs_open_by_day, weekly_windows),
            "Open at end of day",
            page.DEFAULT_HEIGHT,
        ),
        page.with_y_label(
            page.closed_within_days_chart(prs_opened_by_day, weekly_windows, days=2),
            "Closed within 2 days",
            page.DEFAULT_HEIGHT,
        ),
    )


def scatter_chart(prs, today):
    scatter_data = []
    for pr in prs:
        if not pr.was_closed():
            category = "open"
            age = pr.age_at_end_of(today)
        elif pr.was_abandoned():
            category = "abandoned"
            age = pr.age_when_closed()
        else:
            category = "merged"
            age = pr.age_when_merged()
        scatter_data.append(
            domain.datapoint(pr.created_at, value=age, category=category)
        )

    return (
        altair.Chart(
            altair.Data(values=scatter_data), width=DEFAULT_WIDTH, height=SCATTER_HEIGHT
        )
        .mark_circle()
        .encode(
            x=altair.X(
                "date:T",
                title="Date opened",
                axis=altair.Axis(format="%Y", tickCount="year"),
            ),
            y=altair.Y(
                "value:Q",
                axis=altair.Axis(
                    values=[1, 2, 5, 10, 20, 50, 100, 200, 500],
                    titleY=SCATTER_HEIGHT / 2,
                    titleBaseline="middle",
                    titleAnchor="middle",
                ),
                title=None,
            ).scale(type="symlog"),
            color=altair.Color("category:N", legend=altair.Legend(title="Outcome")),
        )
    )


def count_chart(title, prs, windows):
    count_data = domain.window_count_datapoints(prs, windows)
    return shewhart_chart_with_trend_and_residual_limits(
        count_data,
        value_field="count",
        y_label=title,
    )


def closed_within_days_chart(prs, windows, days):
    probabilities_data = domain.closed_within_days_datapoints(prs, windows, days)
    return shewhart_chart_with_trend_and_residual_limits(
        probabilities_data,
        value_field="value",
        y_label=f"Closed within {days} days",
        lower_bound=0.0,
        upper_bound=1.0,
    )


def _best_fit_line_datapoints(data, value_field):
    x_values = [date.fromisoformat(item["date"]).toordinal() for item in data]
    y_values = [item[value_field] for item in data]
    x_mean = statistics.mean(x_values)
    y_mean = statistics.mean(y_values)
    x_variance = sum((x - x_mean) ** 2 for x in x_values)
    assert x_variance > 0, "best-fit line requires distinct x values"
    slope = (
        sum(
            (x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values, strict=True)
        )
        / x_variance
    )
    intercept = y_mean - slope * x_mean
    return [
        {"date": item["date"], "best_fit": slope * x + intercept}
        for item, x in zip(data, x_values, strict=True)
    ]


def shewhart_chart_with_trend_and_residual_limits(
    data,
    value_field,
    y_label,
    lower_bound=None,
    upper_bound=None,
):
    assert len(data) >= 2, (
        "shewhart_chart_with_trend_and_residual_limits requires at least 2 datapoints"
    )
    assert all(value_field in item for item in data), (
        f"shewhart_chart_with_trend_and_residual_limits data missing field {value_field!r}"
    )
    trend_data = _best_fit_line_datapoints(data, value_field)
    residuals = [
        item[value_field] - trend["best_fit"]
        for item, trend in zip(data, trend_data, strict=True)
    ]
    residual_ranges = [
        abs(curr - prev) for prev, curr in itertools.pairwise(residuals)
    ] or [0.0]
    band = 2.66 * statistics.mean(residual_ranges)
    signal_rules_by_point = domain.detect_spc_signals(
        residuals, mean=0.0, ucl=band, lcl=-band
    )

    annotated_data = []
    for item, trend, signal_rules in zip(
        data, trend_data, signal_rules_by_point, strict=True
    ):
        ucl = trend["best_fit"] + band
        lcl = trend["best_fit"] - band
        if upper_bound is not None:
            ucl = min(upper_bound, ucl)
        if lower_bound is not None:
            lcl = max(lower_bound, lcl)
        value = item[value_field]
        point_beyond_limits = value > ucl or value < lcl
        combined_rules = set(signal_rules)
        if point_beyond_limits:
            combined_rules.add(domain.SPC_RULE_POINT_BEYOND_LIMITS)
        annotated_data.append(
            {
                **item,
                "trend": trend["best_fit"],
                "ucl": ucl,
                "lcl": lcl,
                "signal": bool(combined_rules),
                "signal_rules": ", ".join(sorted(combined_rules)),
            }
        )

    return altair.layer(
        altair.Chart(
            altair.Data(values=annotated_data),
            width=DEFAULT_WIDTH,
            height=DEFAULT_HEIGHT,
        )
        .mark_line(color="#4c78a8", opacity=0.45)
        .encode(
            x=altair.X(
                "date:T", title=None, axis=altair.Axis(format="%Y", tickCount="year")
            ),
            y=altair.Y(
                f"{value_field}:Q",
                title=None,
                axis=altair.Axis(
                    titleY=DEFAULT_HEIGHT / 2,
                    titleBaseline="middle",
                    titleAnchor="middle",
                    labelFlush=False,
                ),
            ),
            tooltip=[
                altair.Tooltip("date:T", title="Bucket end", format="%d %b %Y"),
                altair.Tooltip(f"{value_field}:Q", title=y_label, format=".3f"),
                altair.Tooltip("trend:Q", title="Trend", format=".3f"),
                altair.Tooltip("signal_rules:N", title="SPC signals"),
            ],
        ),
        altair.Chart(altair.Data(values=annotated_data))
        .mark_line(color="#4c78a8", strokeDash=[6, 3])
        .encode(
            x=altair.X("date:T", title=None),
            y=altair.Y("trend:Q", title=None),
        ),
        altair.Chart(altair.Data(values=annotated_data))
        .mark_line(color="#a3c5f4", strokeDash=[4, 4])
        .encode(
            x=altair.X("date:T", title=None),
            y=altair.Y("ucl:Q", title=None),
        ),
        altair.Chart(altair.Data(values=annotated_data))
        .mark_line(color="#a3c5f4", strokeDash=[4, 4])
        .encode(
            x=altair.X("date:T", title=None),
            y=altair.Y("lcl:Q", title=None),
        ),
        altair.Chart(altair.Data(values=annotated_data))
        .mark_point(color="#e45756", size=60, filled=True)
        .transform_filter("datum.signal")
        .encode(
            x=altair.X("date:T", title=None),
            y=altair.Y(f"{value_field}:Q", title=None),
            tooltip=[
                altair.Tooltip("date:T", title="Bucket end", format="%d %b %Y"),
                altair.Tooltip(f"{value_field}:Q", title=y_label, format=".3f"),
                altair.Tooltip("trend:Q", title="Trend", format=".3f"),
                altair.Tooltip("signal_rules:N", title="SPC signals"),
            ],
        ),
    )


def y_label_chart(label, height):
    return (
        altair.Chart(altair.Data(values=[{}]), width=LABEL_WIDTH, height=height)
        .mark_text(
            angle=270,
            align="center",
            baseline="middle",
            fontSize=18,
            color=AXIS_LABEL_COLOR,
        )
        .encode(text=altair.value(label))
    )


def with_y_label(chart, label, height):
    return altair.hconcat(y_label_chart(label, height), chart, spacing=5)


def write_charts(*charts):
    import streamlit

    combined = (
        altair.vconcat(*charts)
        .resolve_scale(color="independent")
        .configure_axis(
            labelFontSize=18,
            titleFontSize=18,
            labelColor=AXIS_LABEL_COLOR,
            titleColor=AXIS_LABEL_COLOR,
        )
        .configure_axisY(titleAlign="left", titleX=-60, titlePadding=10)
        .configure_legend(labelFontSize=18, titleFontSize=18)
    )
    streamlit.altair_chart(combined, use_container_width=False)


if __name__ == "__main__":
    root_uri = os.environ.get(
        "REPOSITORY_ROOT_URI", pathlib.Path("data").resolve().as_uri()
    )
    main(Repository(root_uri))
