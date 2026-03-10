import datetime
import itertools
import statistics
from collections import defaultdict
from dataclasses import dataclass


WEEKLY_BUCKET_DAYS = 21
ONE_DAY = datetime.timedelta(days=1)
START_DATE = datetime.date(2021, 1, 1)

SPC_RULE_RUN_8_SAME_SIDE = "8 consecutive on same side of mean"
SPC_RULE_TREND_6 = "6 consecutive increasing/decreasing"
SPC_RULE_POINT_BEYOND_LIMITS = "point beyond control limits"
SPC_RULE_2_OF_3_BEYOND_2SIGMA = "2 of 3 beyond 2 sigma on same side"
SPC_RULE_4_OF_5_BEYOND_1SIGMA = "4 of 5 beyond 1 sigma on same side"
SPC_RULE_15_WITHIN_1SIGMA = "15 consecutive within 1 sigma"
SPC_RULE_8_OUTSIDE_1SIGMA = "8 consecutive outside 1 sigma"
SPC_RULE_14_ALTERNATING = "14 consecutive alternating up/down"
SPC_RULE_8_NO_ZONE_C_BOTH_SIDES = "8 consecutive with no zone C and both sides"


@dataclass(frozen=True)
class Repo:
    org: str
    name: str
    is_content_repo: bool = False


@dataclass(frozen=True)
class PR:
    repo: Repo
    author: str
    created_at: datetime.datetime
    merged_at: datetime.datetime | None
    closed_at: datetime.datetime | None
    is_draft: bool
    is_content: bool

    def was_closed(self):
        return self.closed_at is not None

    def was_merged(self):
        return self.merged_at is not None

    def was_abandoned(self):
        return self.was_closed() and not self.was_merged()

    def age_at(self, time):
        return (time - self.created_at) / ONE_DAY

    def age_at_end_of(self, date):
        midnight = datetime.time(0, 0, 0, tzinfo=datetime.UTC)
        next_day = date + ONE_DAY
        return self.age_at(datetime.datetime.combine(next_day, midnight))

    def age_when_closed(self):
        if not self.was_closed():
            raise ValueError()
        assert self.closed_at is not None
        return self.age_at(self.closed_at)

    def age_when_merged(self):
        if not self.was_merged():
            raise ValueError()
        assert self.merged_at is not None
        return self.age_at(self.merged_at)


@dataclass
class Window:
    start: datetime.date  # exclusive
    end: datetime.date  # inclusive

    def days(self):
        return iter_days(self.start + ONE_DAY, self.end)


def iter_days(start, end):
    day = start
    while day <= end:
        yield day
        day += ONE_DAY


def datapoint(date, **kwargs):
    return dict(date=date.isoformat(), **kwargs)


def build_weekly_windows(start_date, end_date):
    window_size = datetime.timedelta(days=WEEKLY_BUCKET_DAYS)

    windows = []
    end = end_date
    while (start := end - window_size) >= start_date:
        windows.append(Window(start, end))
        end -= window_size

    return list(reversed(windows))


def categorise_prs(unabandoned_prs, today):
    prs_opened_by_day = defaultdict(list)
    prs_open_by_day = defaultdict(list)

    for pr in unabandoned_prs:
        prs_opened_by_day[pr.created_at.date()].append(pr)

        if pr.was_closed():
            assert pr.closed_at is not None
            end = pr.closed_at.date() - ONE_DAY
        else:
            end = today - ONE_DAY

        for day in iter_days(pr.created_at.date(), end):
            prs_open_by_day[day].append(pr)

    return prs_open_by_day, prs_opened_by_day


def window_count_datapoints(prs, windows):
    count_data = []

    for window in windows:
        window_counts = [len(prs.get(day, [])) for day in window.days()]
        count_data.append(datapoint(window.end, count=statistics.mean(window_counts)))

    return count_data


def closed_within_days_datapoints(prs, windows, days):
    probabilities_data = []
    for window in windows:
        probabilities_data.append(
            datapoint(
                window.end,
                value=closed_within_days_km_datapoint(prs, window, days)["value"],
            )
        )

    return probabilities_data


def closed_within_days_km_datapoint(prs, window, days):
    estimate = build_survival_estimate_with_censor_date(prs, window, window.end)
    survival, variance, at_risk = estimate(days)
    return datapoint(window.end, value=1 - survival, variance=variance, n=at_risk)


def build_survival_curve_with_censor_date(prs, window, censor_date):
    estimate = build_survival_estimate_with_censor_date(prs, window, censor_date)

    def prob_of_surviving_for_days(days):
        return estimate(days)[0]

    return prob_of_surviving_for_days


def build_survival_estimate_with_censor_date(prs, window, censor_date):
    observation_flags = []
    durations = []

    for day in window.days():
        for pr in prs[day]:
            if pr.was_merged():
                assert pr.merged_at is not None
                observation_flags.append(True)
                durations.append(working_days_between(pr.created_at, pr.merged_at))
            else:
                observation_flags.append(False)
                end_midnight = datetime.time(0, 0, 0, tzinfo=pr.created_at.tzinfo)
                censor_end = datetime.datetime.combine(
                    censor_date + ONE_DAY, end_midnight
                )
                durations.append(working_days_between(pr.created_at, censor_end))

    event_times = sorted(
        {
            duration
            for observed, duration in zip(observation_flags, durations)
            if observed
        }
    )
    survival_by_time = {}
    variance_sum_by_time = {}
    survival = 1.0
    variance_sum = 0.0
    for time in event_times:
        at_risk = sum(duration >= time for duration in durations)
        events = sum(
            observed and duration == time
            for observed, duration in zip(observation_flags, durations)
        )
        survival *= 1 - (events / at_risk)
        if at_risk > events:
            variance_sum += events / (at_risk * (at_risk - events))
        survival_by_time[time] = survival
        variance_sum_by_time[time] = variance_sum

    def estimate_for_days(days):
        if days == 0 or not survival_by_time:
            at_risk = sum(duration >= days for duration in durations)
            return 1.0, 0.0, at_risk

        current = 1.0
        current_variance_sum = 0.0
        for time in sorted(survival_by_time):
            if time > days:
                break
            current = survival_by_time[time]
            current_variance_sum = variance_sum_by_time[time]
        variance = (current**2) * current_variance_sum
        at_risk = sum(duration >= days for duration in durations)
        return current, variance, at_risk

    return estimate_for_days


def working_days_between(start, end):
    if end <= start:
        return 0.0

    total_seconds = 0.0
    current = start
    while current.date() <= end.date():
        day_start = datetime.datetime.combine(
            current.date(), datetime.time(0, 0, 0, tzinfo=current.tzinfo)
        )
        day_end = day_start + ONE_DAY

        segment_start = max(current, day_start)
        segment_end = min(end, day_end)

        if segment_start < segment_end and segment_start.weekday() < 5:
            total_seconds += (segment_end - segment_start).total_seconds()

        current = day_end

    return total_seconds / ONE_DAY.total_seconds()


def detect_spc_signals(values, mean, ucl, lcl):
    signals = [set() for _ in values]
    _mark_points_beyond_limits(values, ucl, lcl, signals)
    _mark_run_of_8_same_side(values, mean, signals)
    _mark_trend_of_6(values, signals)
    sigma = (ucl - mean) / 3
    if sigma > 0:
        _mark_2_of_3_beyond_2sigma(values, mean, sigma, signals)
        _mark_4_of_5_beyond_1sigma(values, mean, sigma, signals)
        _mark_15_within_1sigma(values, mean, sigma, signals)
        _mark_8_outside_1sigma(values, mean, sigma, signals)
        _mark_8_no_zone_c_both_sides(values, mean, sigma, signals)
    _mark_14_alternating(values, signals)
    return signals


def _mark_points_beyond_limits(values, ucl, lcl, signals):
    for index, value in enumerate(values):
        if value > ucl or value < lcl:
            signals[index].add(SPC_RULE_POINT_BEYOND_LIMITS)


def _mark_run_of_8_same_side(values, mean, signals):
    run_sign = 0
    run_start = 0

    for index, value in enumerate(values):
        sign = 1 if value > mean else -1 if value < mean else 0
        if sign == 0:
            run_sign = 0
            run_start = index + 1
            continue

        if sign != run_sign:
            run_sign = sign
            run_start = index

        if index - run_start + 1 >= 8:
            for marked_index in range(run_start, index + 1):
                signals[marked_index].add(SPC_RULE_RUN_8_SAME_SIDE)


def _mark_trend_of_6(values, signals):
    increasing_start = 0
    decreasing_start = 0

    for index in range(1, len(values)):
        if values[index] > values[index - 1]:
            if index == 1 or values[index - 1] <= values[index - 2]:
                increasing_start = index - 1

            if index - increasing_start + 1 >= 6:
                for marked_index in range(increasing_start, index + 1):
                    signals[marked_index].add(SPC_RULE_TREND_6)
        elif values[index] < values[index - 1]:
            if index == 1 or values[index - 1] >= values[index - 2]:
                decreasing_start = index - 1

            if index - decreasing_start + 1 >= 6:
                for marked_index in range(decreasing_start, index + 1):
                    signals[marked_index].add(SPC_RULE_TREND_6)


def _mark_2_of_3_beyond_2sigma(values, mean, sigma, signals):
    threshold = 2 * sigma
    for start in range(len(values) - 2):
        window_indexes = range(start, start + 3)
        above_indexes = [i for i in window_indexes if values[i] > mean + threshold]
        below_indexes = [i for i in window_indexes if values[i] < mean - threshold]
        if len(above_indexes) >= 2:
            for index in above_indexes:
                signals[index].add(SPC_RULE_2_OF_3_BEYOND_2SIGMA)
        if len(below_indexes) >= 2:
            for index in below_indexes:
                signals[index].add(SPC_RULE_2_OF_3_BEYOND_2SIGMA)


def _mark_4_of_5_beyond_1sigma(values, mean, sigma, signals):
    for start in range(len(values) - 4):
        window_indexes = range(start, start + 5)
        above_indexes = [i for i in window_indexes if values[i] > mean + sigma]
        below_indexes = [i for i in window_indexes if values[i] < mean - sigma]
        if len(above_indexes) >= 4:
            for index in above_indexes:
                signals[index].add(SPC_RULE_4_OF_5_BEYOND_1SIGMA)
        if len(below_indexes) >= 4:
            for index in below_indexes:
                signals[index].add(SPC_RULE_4_OF_5_BEYOND_1SIGMA)


def _mark_15_within_1sigma(values, mean, sigma, signals):
    for start in range(len(values) - 14):
        window_indexes = list(range(start, start + 15))
        if all(abs(values[i] - mean) < sigma for i in window_indexes):
            for index in window_indexes:
                signals[index].add(SPC_RULE_15_WITHIN_1SIGMA)


def _mark_8_outside_1sigma(values, mean, sigma, signals):
    run_start = 0
    run_length = 0
    for index, value in enumerate(values):
        if abs(value - mean) > sigma:
            if run_length == 0:
                run_start = index
            run_length += 1
            if run_length >= 8:
                for marked_index in range(run_start, index + 1):
                    signals[marked_index].add(SPC_RULE_8_OUTSIDE_1SIGMA)
        else:
            run_length = 0


def _mark_14_alternating(values, signals):
    for start in range(len(values) - 13):
        window = values[start : start + 14]
        deltas = [curr - prev for prev, curr in itertools.pairwise(window)]
        if any(delta == 0 for delta in deltas):
            continue
        if all(prev * curr < 0 for prev, curr in itertools.pairwise(deltas)):
            for index in range(start, start + 14):
                signals[index].add(SPC_RULE_14_ALTERNATING)


def _mark_8_no_zone_c_both_sides(values, mean, sigma, signals):
    for start in range(len(values) - 7):
        window_indexes = list(range(start, start + 8))
        window_values = [values[i] for i in window_indexes]
        if not all(abs(value - mean) > sigma for value in window_values):
            continue
        has_above = any(value > mean for value in window_values)
        has_below = any(value < mean for value in window_values)
        if has_above and has_below:
            for index in window_indexes:
                signals[index].add(SPC_RULE_8_NO_ZONE_C_BOTH_SIDES)
