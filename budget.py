"""Pure budgeting logic, kept separate from the Streamlit UI so it can be tested."""

from __future__ import annotations

import calendar
from dataclasses import dataclass

import pandas as pd

YEAR = 2026
BUCKETS = ("Needs", "Wants", "Savings")
# The 50/30/20 rule: share of take-home pay suggested for each bucket.
TARGET_SPLIT = {"Needs": 0.50, "Wants": 0.30, "Savings": 0.20}

DEFAULT_EXPENSES = [
    {"Category": "Rent / Mortgage", "Bucket": "Needs", "Monthly": 1500.0},
    {"Category": "Utilities", "Bucket": "Needs", "Monthly": 180.0},
    {"Category": "Groceries", "Bucket": "Needs", "Monthly": 450.0},
    {"Category": "Transportation", "Bucket": "Needs", "Monthly": 250.0},
    {"Category": "Insurance", "Bucket": "Needs", "Monthly": 200.0},
    {"Category": "Dining Out", "Bucket": "Wants", "Monthly": 200.0},
    {"Category": "Subscriptions", "Bucket": "Wants", "Monthly": 60.0},
    {"Category": "Entertainment", "Bucket": "Wants", "Monthly": 150.0},
    {"Category": "Emergency Fund", "Bucket": "Savings", "Monthly": 300.0},
    {"Category": "Retirement (IRA)", "Bucket": "Savings", "Monthly": 400.0},
]


@dataclass(frozen=True)
class Summary:
    income: float
    expenses: float
    remaining: float
    savings: float

    @property
    def savings_rate(self) -> float:
        """Planned savings plus any unallocated money, as a share of income."""
        if self.income <= 0:
            return 0.0
        return (self.savings + max(self.remaining, 0.0)) / self.income


def money(value: float, cents: bool = False) -> str:
    """Format a dollar amount, putting the sign before the symbol: -$690."""
    sign = "-" if value < 0 else ""
    return f"{sign}${abs(value):,.{2 if cents else 0}f}"


def default_expenses() -> pd.DataFrame:
    return pd.DataFrame(DEFAULT_EXPENSES)


def clean(expenses: pd.DataFrame) -> pd.DataFrame:
    """Drop blank rows and coerce amounts so user edits can't break the math."""
    df = expenses.copy()
    df["Category"] = df["Category"].fillna("").astype(str).str.strip()
    df["Monthly"] = pd.to_numeric(df["Monthly"], errors="coerce").fillna(0.0).clip(lower=0.0)
    df["Bucket"] = df["Bucket"].where(df["Bucket"].isin(BUCKETS), "Needs")
    return df[df["Category"] != ""].reset_index(drop=True)


def summarize(income: float, expenses: pd.DataFrame) -> Summary:
    df = clean(expenses)
    savings = float(df.loc[df["Bucket"] == "Savings", "Monthly"].sum())
    total = float(df["Monthly"].sum())
    return Summary(income=income, expenses=total, remaining=income - total, savings=savings)


def bucket_breakdown(income: float, expenses: pd.DataFrame) -> pd.DataFrame:
    """Compare actual spending per bucket against the 50/30/20 targets."""
    df = clean(expenses)
    actual = df.groupby("Bucket")["Monthly"].sum().reindex(BUCKETS, fill_value=0.0)
    out = pd.DataFrame(
        {
            "Actual": actual,
            "Target": [income * TARGET_SPLIT[b] for b in BUCKETS],
        }
    )
    out["Difference"] = out["Target"] - out["Actual"]
    out.index.name = "Bucket"
    return out


def yearly_plan(
    income: float,
    expenses: pd.DataFrame,
    starting_balance: float = 0.0,
    year: int = YEAR,
) -> pd.DataFrame:
    """Month-by-month projection of the running balance for the year."""
    s = summarize(income, expenses)
    rows = []
    balance = starting_balance
    for month in range(1, 13):
        balance += s.remaining
        rows.append(
            {
                "Month": calendar.month_abbr[month],
                "Date": pd.Timestamp(year=year, month=month, day=1),
                "Income": s.income,
                "Expenses": s.expenses,
                "Net": s.remaining,
                "Balance": balance,
            }
        )
    return pd.DataFrame(rows)
