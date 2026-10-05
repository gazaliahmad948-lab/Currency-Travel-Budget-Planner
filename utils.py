import csv
import json
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import List, Dict


DATA_DIR = Path(__file__).resolve().parent / "data"
BUDGET_FILE = DATA_DIR / "budgets.json"
EXPENSE_FILE = DATA_DIR / "expenses.csv"


def validate_currency_code(code: str) -> str:
    """Validate a three-letter ISO-style currency code with regex."""
    code = code.strip().upper()
    if not re.fullmatch(r"[A-Z]{3}", code):
        raise ValueError("Currency code must contain exactly 3 letters, such as NGN, USD, or GBP.")
    return code


def parse_positive_decimal(value: str) -> Decimal:
    """Extract a positive number from user input."""
    text = str(value).strip().replace(",", "")
    if not re.fullmatch(r"\d+(?:\.\d{1,2})?", text):
        raise ValueError("Enter a valid positive number, for example 50000 or 50000.50.")

    try:
        number = Decimal(text)
    except InvalidOperation as exc:
        raise ValueError("Enter a valid number.") from exc

    if number <= 0:
        raise ValueError("The number must be greater than zero.")
    return number


def parse_non_negative_decimal(value: str) -> Decimal:
    """Extract a number that may be zero."""
    text = str(value).strip().replace(",", "")
    if not re.fullmatch(r"\d+(?:\.\d{1,2})?", text):
        raise ValueError("Enter a valid number, for example 0, 50000, or 50000.50.")
    try:
        number = Decimal(text)
    except InvalidOperation as exc:
        raise ValueError("Enter a valid number.") from exc
    if number < 0:
        raise ValueError("The number cannot be negative.")
    return number


def validate_duration(duration: int) -> int:
    duration = int(duration)
    if duration <= 0 or duration > 365:
        raise ValueError("Trip duration must be between 1 and 365 days.")
    return duration


def save_budget(budget: Dict) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    budgets = []

    if BUDGET_FILE.exists():
        try:
            with BUDGET_FILE.open("r", encoding="utf-8") as file:
                budgets = json.load(file)
            if not isinstance(budgets, list):
                budgets = []
        except (json.JSONDecodeError, OSError):
            budgets = []

    budgets.append(budget)
    with BUDGET_FILE.open("w", encoding="utf-8") as file:
        json.dump(budgets, file, indent=4)


def save_expense(expense: Dict) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    file_exists = EXPENSE_FILE.exists()

    with EXPENSE_FILE.open("a", newline="", encoding="utf-8") as file:
        fieldnames = ["date", "category", "description", "amount", "currency"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        if not file_exists or EXPENSE_FILE.stat().st_size == 0:
            writer.writeheader()
        writer.writerow(expense)


def load_expenses() -> List[Dict]:
    if not EXPENSE_FILE.exists():
        return []

    try:
        with EXPENSE_FILE.open("r", newline="", encoding="utf-8") as file:
            return list(csv.DictReader(file))
    except (OSError, csv.Error):
        return []


def format_money(amount: Decimal, currency: str) -> str:
    return f"{Decimal(str(amount)):,.2f} {currency.upper()}"


def holiday_message(holidays: List[Dict]) -> str:
    if not holidays:
        return "No public holiday was found during the selected travel dates."

    names = []
    for holiday in holidays:
        holiday_date = holiday.get("date", "unknown date")
        name = holiday.get("name", "Public holiday")
        names.append(f"- {name} ({holiday_date})")

    return "Public holiday warning:\n" + "\n".join(names)
