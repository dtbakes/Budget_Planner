import pandas as pd
import pytest

import budget


def make(rows):
    return pd.DataFrame(rows, columns=["Category", "Bucket", "Monthly"])


def test_summarize_totals():
    df = make([("Rent", "Needs", 1000), ("Fun", "Wants", 200), ("IRA", "Savings", 300)])
    s = budget.summarize(2000, df)
    assert s.expenses == 1500
    assert s.remaining == 500
    assert s.savings == 300
    assert s.savings_rate == pytest.approx(0.4)


def test_savings_rate_handles_zero_income_and_overspending():
    df = make([("Rent", "Needs", 1000), ("IRA", "Savings", 100)])
    assert budget.summarize(0, df).savings_rate == 0.0
    assert budget.summarize(500, df).savings_rate == pytest.approx(0.2)


def test_clean_drops_blank_rows_and_bad_values():
    df = make([("Rent", "Needs", "abc"), ("", "Wants", 50), (None, "Needs", 10), ("Gym", "Bogus", -5)])
    out = budget.clean(df)
    assert list(out["Category"]) == ["Rent", "Gym"]
    assert list(out["Monthly"]) == [0.0, 0.0]
    assert list(out["Bucket"]) == ["Needs", "Needs"]


def test_bucket_breakdown_against_50_30_20():
    df = make([("Rent", "Needs", 2500), ("Fun", "Wants", 1000)])
    out = budget.bucket_breakdown(4000, df)
    assert out.loc["Needs", "Target"] == 2000
    assert out.loc["Needs", "Difference"] == -500
    assert out.loc["Savings", "Actual"] == 0


def test_yearly_plan_accumulates_balance():
    df = make([("Rent", "Needs", 900)])
    plan = budget.yearly_plan(1000, df, starting_balance=50)
    assert len(plan) == 12
    assert plan["Month"].iloc[0] == "Jan"
    assert plan["Date"].iloc[-1] == pd.Timestamp("2026-12-01")
    assert plan["Balance"].iloc[-1] == 50 + 12 * 100


def test_money_formatting():
    assert budget.money(1234.4) == "$1,234"
    assert budget.money(-690) == "-$690"
    assert budget.money(-80, cents=True) == "-$80.00"


def test_default_expenses_are_valid():
    df = budget.default_expenses()
    assert set(df["Bucket"]) <= set(budget.BUCKETS)
    assert len(budget.clean(df)) == len(df)
