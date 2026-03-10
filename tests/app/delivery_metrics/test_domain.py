from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

import pytest

from delivery_metrics import domain


class DummyPR:
    def __init__(self, created_at):
        self.created_at = created_at
        self.merged_at = None

    def was_merged(self):
        return False


def test_build_weekly_windows_non_overlapping():
    start = date(2024, 1, 1)
    end = date(2024, 1, 22)

    windows = domain.build_weekly_windows(start, end)

    assert [(w.start, w.end) for w in windows] == [
        (date(2024, 1, 1), date(2024, 1, 22)),
    ]


def test_window_count_datapoints_average():
    day = date(2024, 1, 1)
    window = domain.Window(day - timedelta(days=7), day)

    prs_by_day = {
        day: [DummyPR(datetime(2024, 1, 1, 0, 0, 0)) for _ in range(2)],
        day - timedelta(days=1): [DummyPR(datetime(2023, 12, 31, 0, 0, 0))],
    }

    data = domain.window_count_datapoints(prs_by_day, [window])

    assert data == [domain.datapoint(window.end, count=3 / 7)]


def test_closed_within_days_datapoints():
    day = date(2024, 1, 1)
    window = domain.Window(day - timedelta(days=7), day)

    prs_by_day = defaultdict(list)
    prs_by_day[day].append(DummyPR(datetime(2024, 1, 1, 0, 0, 0)))

    data = domain.closed_within_days_datapoints(prs_by_day, [window], days=3)

    assert data == [domain.datapoint(window.end, value=0.0)]


def test_detect_spc_signals_flags_run_of_8_on_one_side():
    values = [1, 2, 3, 4, 5, 6, 7, 8]
    signals = domain.detect_spc_signals(values, mean=0, ucl=3, lcl=-3)

    assert all(domain.SPC_RULE_RUN_8_SAME_SIDE in item for item in signals)


def test_detect_spc_signals_flags_trend_of_6():
    values = [9, 8, 7, 6, 5, 4]
    signals = domain.detect_spc_signals(values, mean=0, ucl=3, lcl=-3)

    assert all(domain.SPC_RULE_TREND_6 in item for item in signals)


def test_detect_spc_signals_flags_points_beyond_limits():
    values = [0.0, 3.5, -3.2]
    signals = domain.detect_spc_signals(values, mean=0, ucl=3, lcl=-3)

    assert domain.SPC_RULE_POINT_BEYOND_LIMITS not in signals[0]
    assert domain.SPC_RULE_POINT_BEYOND_LIMITS in signals[1]
    assert domain.SPC_RULE_POINT_BEYOND_LIMITS in signals[2]


def test_detect_spc_signals_flags_2_of_3_beyond_2sigma():
    values = [2.2, 2.3, 0.4]
    signals = domain.detect_spc_signals(values, mean=0, ucl=3, lcl=-3)

    assert domain.SPC_RULE_2_OF_3_BEYOND_2SIGMA in signals[0]
    assert domain.SPC_RULE_2_OF_3_BEYOND_2SIGMA in signals[1]
    assert domain.SPC_RULE_2_OF_3_BEYOND_2SIGMA not in signals[2]


def test_detect_spc_signals_flags_2_of_3_below_2sigma():
    values = [-2.2, -2.3, -0.4]
    signals = domain.detect_spc_signals(values, mean=0, ucl=3, lcl=-3)

    assert domain.SPC_RULE_2_OF_3_BEYOND_2SIGMA in signals[0]
    assert domain.SPC_RULE_2_OF_3_BEYOND_2SIGMA in signals[1]
    assert domain.SPC_RULE_2_OF_3_BEYOND_2SIGMA not in signals[2]


def test_detect_spc_signals_flags_4_of_5_beyond_1sigma():
    values = [1.2, 1.3, 0.2, 1.4, 1.5]
    signals = domain.detect_spc_signals(values, mean=0, ucl=3, lcl=-3)

    assert domain.SPC_RULE_4_OF_5_BEYOND_1SIGMA in signals[0]
    assert domain.SPC_RULE_4_OF_5_BEYOND_1SIGMA in signals[1]
    assert domain.SPC_RULE_4_OF_5_BEYOND_1SIGMA not in signals[2]
    assert domain.SPC_RULE_4_OF_5_BEYOND_1SIGMA in signals[3]
    assert domain.SPC_RULE_4_OF_5_BEYOND_1SIGMA in signals[4]


def test_detect_spc_signals_flags_15_within_1sigma():
    values = [0.1] * 15
    signals = domain.detect_spc_signals(values, mean=0, ucl=3, lcl=-3)

    assert all(domain.SPC_RULE_15_WITHIN_1SIGMA in item for item in signals)


def test_detect_spc_signals_flags_8_outside_1sigma():
    values = [1.2, -1.2, 1.3, -1.3, 1.4, -1.4, 1.5, -1.5]
    signals = domain.detect_spc_signals(values, mean=0, ucl=3, lcl=-3)

    assert all(domain.SPC_RULE_8_OUTSIDE_1SIGMA in item for item in signals)


def test_detect_spc_signals_flags_14_alternating():
    values = [0, 1] * 7
    signals = domain.detect_spc_signals(values, mean=0, ucl=3, lcl=-3)

    assert all(domain.SPC_RULE_14_ALTERNATING in item for item in signals)


def test_detect_spc_signals_flags_8_no_zone_c_both_sides():
    values = [1.2, -1.2, 1.3, -1.3, 1.4, -1.4, 1.5, -1.5]
    signals = domain.detect_spc_signals(values, mean=0, ucl=3, lcl=-3)

    assert all(domain.SPC_RULE_8_NO_ZONE_C_BOTH_SIDES in item for item in signals)


def test_pr_was_closed_at_end_of_is_removed():
    assert not hasattr(domain.PR, "was_closed_at_end_of")


def test_categorise_prs_uses_supplied_today():
    class OpenPR:
        def __init__(self, created_at):
            self.created_at = created_at

        def was_closed(self):
            return False

    created = datetime(2024, 1, 1, 12, 0, 0)
    pr = OpenPR(created)
    supplied_today = date(2024, 1, 3)

    prs_open_by_day, _ = domain.categorise_prs([pr], today=supplied_today)

    assert created.date() in prs_open_by_day
    assert date(2024, 1, 2) in prs_open_by_day


def test_working_days_between_excludes_weekends():
    start = datetime(2024, 1, 5, 12, 0, 0)
    end = datetime(2024, 1, 8, 12, 0, 0)

    assert domain.working_days_between(start, end) == 1.0


def test_working_days_between_zero_when_end_before_start():
    start = datetime(2024, 1, 8, 12, 0, 0)
    end = datetime(2024, 1, 8, 11, 0, 0)

    assert domain.working_days_between(start, end) == 0.0


def test_build_survival_curve_uses_working_days():
    created = datetime(2024, 1, 5, 12, 0, 0)
    merged = datetime(2024, 1, 8, 12, 0, 0)

    class PRStub(DummyPR):
        def was_merged(self):
            return True

    pr = PRStub(created)
    pr.merged_at = merged
    day = created.date()
    window = domain.Window(day - timedelta(days=1), day)

    curve = domain.build_survival_curve_with_censor_date({day: [pr]}, window, day)
    assert curve(1.0) == pytest.approx(0.0)


def test_survival_curve_breaks_at_later_event_time():
    created = datetime(2024, 1, 1, 0, 0, 0)

    class PRStub(DummyPR):
        def __init__(self, created_at, merged_at):
            super().__init__(created_at)
            self.merged_at = merged_at

        def was_merged(self):
            return True

    pr1 = PRStub(created, datetime(2024, 1, 2, 0, 0, 0))
    pr2 = PRStub(created, datetime(2024, 1, 4, 0, 0, 0))
    window = domain.Window(date(2023, 12, 31), date(2024, 1, 1))

    curve = domain.build_survival_curve_with_censor_date(
        {date(2024, 1, 1): [pr1, pr2]}, window, date(2024, 1, 4)
    )

    assert curve(2.0) == pytest.approx(0.5)


def test_pr_methods_cover_closed_and_merged_paths():
    repo = domain.Repo(
        org="opensafely-core",
        name="repo",
    )
    created = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    closed = datetime(2024, 1, 2, 0, 0, 0, tzinfo=timezone.utc)
    merged = datetime(2024, 1, 2, 12, 0, 0, tzinfo=timezone.utc)
    pr = domain.PR(
        repo=repo,
        author="dev",
        created_at=created,
        merged_at=merged,
        closed_at=closed,
        is_draft=False,
        is_content=False,
    )

    assert pr.was_closed() is True
    assert pr.was_merged() is True
    assert pr.was_abandoned() is False
    assert pr.age_at_end_of(date(2024, 1, 1)) == 1.0
    assert pr.age_when_closed() == 1.0
    assert pr.age_when_merged() == 1.5


def test_pr_methods_raise_when_unset():
    repo = domain.Repo(
        org="opensafely-core",
        name="repo",
    )
    created = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    pr = domain.PR(
        repo=repo,
        author="dev",
        created_at=created,
        merged_at=None,
        closed_at=None,
        is_draft=False,
        is_content=False,
    )

    assert pr.was_closed() is False
    assert pr.was_merged() is False
    with pytest.raises(ValueError):
        pr.age_when_closed()
    with pytest.raises(ValueError):
        pr.age_when_merged()


def test_categorise_prs_handles_closed_prs():
    class ClosedPR:
        def __init__(self, created_at, closed_at):
            self.created_at = created_at
            self.closed_at = closed_at

        def was_closed(self):
            return True

    created = datetime(2024, 1, 1, 12, 0, 0)
    closed = datetime(2024, 1, 3, 12, 0, 0)
    pr = ClosedPR(created, closed)

    prs_open_by_day, prs_opened_by_day = domain.categorise_prs(
        [pr], today=date(2024, 1, 10)
    )

    assert created.date() in prs_opened_by_day
    assert date(2024, 1, 2) in prs_open_by_day
    assert date(2024, 1, 3) not in prs_open_by_day


def test_detect_spc_signals_handles_sigma_zero():
    signals = domain.detect_spc_signals([1, 1, 1], mean=1, ucl=1, lcl=1)
    assert signals == [set(), set(), set()]


def test_detect_spc_signals_4_of_5_below_1sigma():
    values = [-1.2, -1.3, -0.2, -1.4, -1.5]
    signals = domain.detect_spc_signals(values, mean=0, ucl=3, lcl=-3)

    assert domain.SPC_RULE_4_OF_5_BEYOND_1SIGMA in signals[0]
    assert domain.SPC_RULE_4_OF_5_BEYOND_1SIGMA in signals[1]
    assert domain.SPC_RULE_4_OF_5_BEYOND_1SIGMA not in signals[2]
    assert domain.SPC_RULE_4_OF_5_BEYOND_1SIGMA in signals[3]
    assert domain.SPC_RULE_4_OF_5_BEYOND_1SIGMA in signals[4]


def test_detect_spc_signals_15_within_1sigma_not_triggered():
    values = [0.1] * 7 + [2.5] + [0.1] * 7
    signals = domain.detect_spc_signals(values, mean=0, ucl=3, lcl=-3)
    assert all(domain.SPC_RULE_15_WITHIN_1SIGMA not in item for item in signals)


def test_detect_spc_signals_14_alternating_not_triggered_with_zero_delta():
    values = [1, 1] * 7
    signals = domain.detect_spc_signals(values, mean=0, ucl=3, lcl=-3)
    assert all(domain.SPC_RULE_14_ALTERNATING not in item for item in signals)


def test_detect_spc_signals_14_alternating_not_triggered_when_monotonic():
    values = list(range(14))
    signals = domain.detect_spc_signals(values, mean=0, ucl=30, lcl=-30)
    assert all(domain.SPC_RULE_14_ALTERNATING not in item for item in signals)


def test_detect_spc_signals_8_no_zone_c_needs_both_sides():
    values = [1.2] * 8
    signals = domain.detect_spc_signals(values, mean=0, ucl=3, lcl=-3)
    assert all(domain.SPC_RULE_8_NO_ZONE_C_BOTH_SIDES not in item for item in signals)
