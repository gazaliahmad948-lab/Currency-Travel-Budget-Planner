from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict


class CurrencyConverter:
    """Store a currency rate and convert an amount."""

    def __init__(self, from_currency: str, to_currency: str, rate: Decimal):
        self.from_currency = from_currency.upper()
        self.to_currency = to_currency.upper()
        self.rate = Decimal(str(rate))

        if self.rate <= 0:
            raise ValueError("Exchange rate must be greater than zero.")

    def convert(self, amount: Decimal) -> Decimal:
        amount = Decimal(str(amount))
        if amount < 0:
            raise ValueError("Amount cannot be negative.")
        return (amount * self.rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


@dataclass
class TripBudget:
    """Represent the planned budget for a trip."""

    destination: str
    home_currency: str
    destination_currency: str
    amount: Decimal
    duration: int
    start_date: date
    daily_limit: Decimal = field(init=False)

    def __post_init__(self):
        self.amount = Decimal(str(self.amount))
        self.duration = int(self.duration)

        if self.amount < 0:
            raise ValueError("Budget amount cannot be negative.")
        if self.duration <= 0:
            raise ValueError("Trip duration must be at least 1 day.")

        self.home_currency = self.home_currency.upper()
        self.destination_currency = self.destination_currency.upper()
        self.daily_limit = (self.amount / self.duration).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

    @property
    def end_date(self) -> date:
        from datetime import timedelta
        return self.start_date + timedelta(days=self.duration - 1)

    def to_dict(self) -> Dict:
        return {
            "destination": self.destination,
            "home_currency": self.home_currency,
            "destination_currency": self.destination_currency,
            "amount": str(self.amount),
            "duration": self.duration,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "daily_limit": str(self.daily_limit),
        }


@dataclass
class Expense:
    """Represent one travel expense."""

    category: str
    description: str
    amount: Decimal
    currency: str
    expense_date: date

    def __post_init__(self):
        self.amount = Decimal(str(self.amount))
        self.currency = self.currency.upper()
        self.category = self.category.strip()
        self.description = self.description.strip()

        if self.amount <= 0:
            raise ValueError("Expense amount must be greater than zero.")
        if not self.category:
            raise ValueError("Expense category is required.")
        if not self.description:
            raise ValueError("Expense description is required.")

    def to_dict(self) -> Dict:
        return {
            "date": self.expense_date.isoformat(),
            "category": self.category,
            "description": self.description,
            "amount": str(self.amount),
            "currency": self.currency,
        }


class BudgetReport:
    """Calculate totals and remaining budget from a trip and its expenses."""

    def __init__(self, trip: TripBudget, expenses: List[Expense] | None = None):
        self.trip = trip
        self.expenses = expenses or []

    def total_expenses(self) -> Decimal:
        total = Decimal("0")
        for expense in self.expenses:
            if expense.currency == self.trip.home_currency:
                total += expense.amount
        return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def remaining_budget(self) -> Decimal:
        remaining = self.trip.amount - self.total_expenses()
        return remaining.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def expenses_by_category(self) -> Dict[str, Decimal]:
        result: Dict[str, Decimal] = {}
        for expense in self.expenses:
            if expense.currency != self.trip.home_currency:
                continue
            result[expense.category] = result.get(expense.category, Decimal("0")) + expense.amount

        return {
            category: amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            for category, amount in result.items()
        }
