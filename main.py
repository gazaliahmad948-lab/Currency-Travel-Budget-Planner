import os
from datetime import date
from decimal import Decimal

import streamlit as st

from models import BudgetReport, CurrencyConverter, Expense, TripBudget
from services import COUNTRIES, CurrencyService, GeminiService, HolidayService, compare_countries
from utils import (
    format_money,
    holiday_message,
    load_expenses,
    parse_non_negative_decimal,
    parse_positive_decimal,
    save_budget,
    save_expense,
    validate_currency_code,
    validate_duration,
)


st.set_page_config(page_title="Currency & Travel Budget Planner", page_icon="✈️", layout="wide")

st.title("✈️ Currency & Travel Budget Planner")
st.caption("Plan a trip, convert currencies, track expenses, compare destinations, and check public holidays.")

if "trip" not in st.session_state:
    st.session_state.trip = None
if "expenses" not in st.session_state:
    st.session_state.expenses = []
if "rate" not in st.session_state:
    st.session_state.rate = None


def show_error(message: str) -> None:
    st.error(message)


tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["💱 Currency", "🧳 Trip Budget", "💳 Expenses", "🌍 Compare & Holidays", "🤖 AI Advice"]
)


with tab1:
    st.header("Currency Converter")

    col1, col2, col3 = st.columns(3)
    with col1:
        from_currency = st.text_input("Home currency", value="NGN", max_chars=3).upper()
    with col2:
        to_currency = st.text_input("Destination currency", value="USD", max_chars=3).upper()
    with col3:
        amount_text = st.text_input("Amount", value="100000")

    if st.button("Convert Money", type="primary"):
        try:
            from_currency = validate_currency_code(from_currency)
            to_currency = validate_currency_code(to_currency)
            amount = parse_positive_decimal(amount_text)

            rate = CurrencyService.get_rate(from_currency, to_currency)
            converter = CurrencyConverter(from_currency, to_currency, rate)
            converted = converter.convert(amount)
            st.session_state.rate = rate

            st.success(f"{format_money(amount, from_currency)} = {format_money(converted, to_currency)}")
            st.info(f"Exchange rate: 1 {from_currency} = {rate} {to_currency}")
        except (ValueError, RuntimeError) as exc:
            show_error(str(exc))


with tab2:
    st.header("Trip Budget Planner")

    col1, col2 = st.columns(2)
    with col1:
        destination = st.text_input("Destination", value="Dubai")
        home_currency = st.text_input("Your currency", value="NGN", max_chars=3).upper()
        destination_currency = st.text_input("Destination currency", value="AED", max_chars=3).upper()
        budget_text = st.text_input("Total budget in your currency", value="500000")

    with col2:
        duration = st.number_input("Travel duration (days)", min_value=1, max_value=365, value=7, step=1)
        start_date = st.date_input("Travel start date", value=date.today())

    if st.button("Create Trip Budget", type="primary"):
        try:
            home_currency = validate_currency_code(home_currency)
            destination_currency = validate_currency_code(destination_currency)
            amount = parse_positive_decimal(budget_text)
            duration = validate_duration(duration)

            trip = TripBudget(
                destination=destination.strip(),
                home_currency=home_currency,
                destination_currency=destination_currency,
                amount=amount,
                duration=duration,
                start_date=start_date,
            )

            st.session_state.trip = trip
            st.session_state.expenses = []
            save_budget(trip.to_dict())

            st.success("Trip budget created and saved locally.")
            metric1, metric2, metric3 = st.columns(3)
            metric1.metric("Total budget", format_money(trip.amount, trip.home_currency))
            metric2.metric("Daily limit", format_money(trip.daily_limit, trip.home_currency))
            metric3.metric("End date", trip.end_date.strftime("%d %b %Y"))
        except (ValueError, RuntimeError) as exc:
            show_error(str(exc))

    if st.session_state.trip:
        trip = st.session_state.trip
        st.divider()
        st.subheader("Current Trip")
        st.write(
            f"**{trip.destination}** — {trip.start_date.strftime('%d %b %Y')} "
            f"to {trip.end_date.strftime('%d %b %Y')}"
        )


with tab3:
    st.header("Expense Tracker")
    trip = st.session_state.trip

    if not trip:
        st.info("Create a trip budget first.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            expense_category = st.selectbox("Category", ["Food", "Transport", "Accommodation", "Shopping", "Activities", "Other"])
            expense_description = st.text_input("Description", value="Lunch")
            expense_amount_text = st.text_input("Amount", value="5000")
        with col2:
            st.text_input("Expense currency", value=trip.home_currency, disabled=True)
            expense_date = st.date_input(
    "Expense date",
    value=max(date.today(), trip.start_date),
    min_value=trip.start_date,
    max_value=trip.end_date
)

        if st.button("Add Expense", type="primary"):
            try:
                expense_currency = trip.home_currency
                expense_amount = parse_positive_decimal(expense_amount_text)
                expense = Expense(
                    category=expense_category,
                    description=expense_description,
                    amount=expense_amount,
                    currency=expense_currency,
                    expense_date=expense_date,
                )

                st.session_state.expenses.append(expense)
                save_expense(expense.to_dict())
                st.success("Expense added and saved to CSV.")
            except (ValueError, RuntimeError) as exc:
                show_error(str(exc))

        report = BudgetReport(trip, st.session_state.expenses)
        total = report.total_expenses()
        remaining = report.remaining_budget()

        metric1, metric2 = st.columns(2)
        metric1.metric("Recorded expenses", format_money(total, trip.home_currency))
        metric2.metric("Remaining budget", format_money(remaining, trip.home_currency))

        if st.session_state.expenses:
            rows = [expense.to_dict() for expense in st.session_state.expenses]
            st.dataframe(rows, use_container_width=True)

            categories = report.expenses_by_category()
            if categories:
                st.subheader("Expenses by Category")
                st.bar_chart({key: float(value) for key, value in categories.items()})


with tab4:
    st.header("Country Comparison & Public Holiday Checker")

    st.subheader("Compare Two Destinations")
    country_names = list(COUNTRIES.keys())
    col1, col2 = st.columns(2)

    with col1:
        country_one = st.selectbox("Country 1", country_names, index=1)
        daily_one_text = st.text_input("Estimated daily cost for Country 1 (home currency)", value="100000")

    with col2:
        country_two = st.selectbox("Country 2", country_names, index=2)
        daily_two_text = st.text_input("Estimated daily cost for Country 2 (home currency)", value="120000")

    compare_duration = st.number_input("Comparison duration (days)", min_value=1, max_value=365, value=7, step=1)
    comparison_currency = st.text_input("Comparison currency", value="NGN", max_chars=3).upper()

    if st.button("Compare Countries", type="primary"):
        try:
            comparison_currency = validate_currency_code(comparison_currency)
            daily_one = parse_non_negative_decimal(daily_one_text)
            daily_two = parse_non_negative_decimal(daily_two_text)
            results = compare_countries(
                comparison_currency,
                country_one,
                daily_one,
                country_two,
                daily_two,
                compare_duration,
            )

            for result in results:
                st.write(
                    f"**{result['country']}**: {format_money(result['daily_cost'], comparison_currency)} per day "
                    f"→ **{format_money(result['trip_cost'], comparison_currency)}** for {compare_duration} days"
                )

            if results[0]["trip_cost"] < results[1]["trip_cost"]:
                st.success(f"{country_one} is cheaper based on the estimates you entered.")
            elif results[1]["trip_cost"] < results[0]["trip_cost"]:
                st.success(f"{country_two} is cheaper based on the estimates you entered.")
            else:
                st.info("Both countries have the same estimated cost.")
        except (ValueError, RuntimeError) as exc:
            show_error(str(exc))

    st.divider()
    st.subheader("Public Holiday Checker")

    holiday_country = st.selectbox("Destination country", country_names, key="holiday_country")
    holiday_code = COUNTRIES[holiday_country]
    holiday_start = st.date_input("Travel start", value=date.today(), key="holiday_start")
    holiday_end = st.date_input("Travel end", value=date.today(), key="holiday_end")

    if st.button("Check Public Holidays"):
        if holiday_end < holiday_start:
            show_error("Travel end date cannot be before the start date.")
        else:
            try:
                holidays = HolidayService.holidays_during_trip(holiday_start, holiday_end, holiday_code)
                if holidays:
                    st.warning(holiday_message(holidays))
                else:
                    st.success(holiday_message(holidays))
            except RuntimeError as exc:
                show_error(str(exc))


with tab5:
    st.header("AI Travel Budget Advice")
    trip = st.session_state.trip

    if not trip:
        st.info("Create a trip budget first so the AI has information to work with.")
    else:
        st.write("The AI will use your trip budget and recorded expenses to suggest ways to manage your spending.")

        if st.button("Generate AI Advice", type="primary"):
            report = BudgetReport(trip, st.session_state.expenses)
            prompt = f"""
You are a practical travel budget advisor.

Trip destination: {trip.destination}
Travel dates: {trip.start_date} to {trip.end_date}
Duration: {trip.duration} days
Home currency: {trip.home_currency}
Destination currency: {trip.destination_currency}
Total budget: {trip.amount} {trip.home_currency}
Daily budget: {trip.daily_limit} {trip.home_currency}
Recorded expenses: {report.total_expenses()} {trip.home_currency}
Remaining budget: {report.remaining_budget()} {trip.home_currency}

Give concise, realistic travel-budget advice. Mention daily spending discipline,
transport, food, accommodation, emergency money, and one or two ways to reduce costs.
Do not invent exact exchange rates or public-holiday information.
"""
            try:
                advice = GeminiService.generate_advice(prompt)
                st.markdown(advice)
            except RuntimeError as exc:
                show_error(str(exc))

st.divider()
st.caption("Local records are stored in the data/ folder as JSON and CSV files.")
