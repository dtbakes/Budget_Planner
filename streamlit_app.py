import pandas as pd
import streamlit as st

import budget

st.set_page_config(page_title=f"Budget Planner {budget.YEAR}", page_icon="💰", layout="wide")

st.title(f"💰 Budget Planner {budget.YEAR}")
st.caption("Plan your monthly budget, check it against the 50/30/20 rule, and project your year.")

with st.sidebar:
    st.header("Income")
    income = st.number_input("Monthly take-home pay ($)", min_value=0.0, value=5000.0, step=100.0)
    starting_balance = st.number_input(
        f"Cash on hand, Jan 1 {budget.YEAR} ($)", min_value=0.0, value=0.0, step=100.0
    )
    st.divider()
    uploaded = st.file_uploader("Load a saved budget (CSV)", type="csv")

if "expenses" not in st.session_state:
    st.session_state.expenses = budget.default_expenses()
# Only load the file once per upload so it doesn't overwrite later edits.
if uploaded is not None and st.session_state.get("loaded_file") != uploaded.file_id:
    st.session_state.expenses = budget.clean(pd.read_csv(uploaded))
    st.session_state.loaded_file = uploaded.file_id
    st.session_state.pop("expense_editor", None)

st.subheader("Monthly expenses")
edited = st.data_editor(
    st.session_state.expenses,
    num_rows="dynamic",
    width="stretch",
    column_config={
        "Category": st.column_config.TextColumn(required=True),
        "Bucket": st.column_config.SelectboxColumn(options=list(budget.BUCKETS), required=True),
        "Monthly": st.column_config.NumberColumn("Monthly ($)", min_value=0.0, format="dollar"),
    },
    key="expense_editor",
)
expenses = budget.clean(edited)
summary = budget.summarize(income, expenses)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Income", budget.money(summary.income))
c2.metric("Expenses", budget.money(summary.expenses))
c3.metric("Left over", budget.money(summary.remaining))
c4.metric("Savings rate", f"{summary.savings_rate:.0%}")

if summary.remaining < 0:
    st.error(f"You're over budget by ${-summary.remaining:,.2f} a month.")

left, right = st.columns(2)
with left:
    st.subheader("50/30/20 check")
    breakdown = budget.bucket_breakdown(income, expenses)
    st.bar_chart(breakdown[["Actual", "Target"]], stack=False)
    st.dataframe(breakdown.style.format(lambda v: budget.money(v, cents=True)), width="stretch")
with right:
    st.subheader("Spending by category")
    st.bar_chart(expenses.set_index("Category")["Monthly"], horizontal=True)

st.subheader(f"{budget.YEAR} projection")
plan = budget.yearly_plan(income, expenses, starting_balance)
st.line_chart(plan, x="Date", y="Balance")
st.caption(
    f"At this pace you'll have **{budget.money(plan['Balance'].iloc[-1])}** in cash by December, "
    "not counting your planned savings."
)

st.download_button(
    "Download budget as CSV",
    expenses.to_csv(index=False),
    file_name=f"budget_{budget.YEAR}.csv",
    mime="text/csv",
)
