import os
from datetime import date
from decimal import Decimal
from typing import Dict, List

import requests


class CurrencyService:
    """Get current exchange rates from the Frankfurter API."""

    BASE_URL = "https://api.frankfurter.dev/v2"

    @staticmethod
    def get_rate(from_currency: str, to_currency: str) -> Decimal:
        from_currency = from_currency.upper().strip()
        to_currency = to_currency.upper().strip()

        if from_currency == to_currency:
            return Decimal("1")

        url = f"{CurrencyService.BASE_URL}/rate/{from_currency}/{to_currency}"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            return Decimal(str(data["rate"]))
        except requests.RequestException as exc:
            raise RuntimeError("Could not retrieve the exchange rate. Check your internet connection.") from exc
        except (ValueError, KeyError, TypeError) as exc:
            raise RuntimeError("The exchange-rate data was missing or invalid.") from exc

    @staticmethod
    def convert(amount: Decimal, from_currency: str, to_currency: str) -> Decimal:
        rate = CurrencyService.get_rate(from_currency, to_currency)
        return (Decimal(str(amount)) * rate).quantize(Decimal("0.01"))


class HolidayService:
    """Check public holidays using the Nager.Date API."""

    BASE_URL = "https://date.nager.at/api/v3/publicholidays"

    @staticmethod
    def get_holidays(year: int, country_code: str) -> List[Dict]:
        url = f"{HolidayService.BASE_URL}/{year}/{country_code.upper()}"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, list):
                raise RuntimeError("Holiday service returned an unexpected response.")
            return data
        except requests.RequestException as exc:
            raise RuntimeError("Could not retrieve public holiday data.") from exc
        except ValueError as exc:
            raise RuntimeError("Public holiday data was not valid JSON.") from exc

    @staticmethod
    def holidays_during_trip(start_date: date, end_date: date, country_code: str) -> List[Dict]:
        years = range(start_date.year, end_date.year + 1)
        holidays: List[Dict] = []

        for year in years:
            for holiday in HolidayService.get_holidays(year, country_code):
                try:
                    holiday_date = date.fromisoformat(holiday["date"])
                except (KeyError, ValueError):
                    continue
                if start_date <= holiday_date <= end_date:
                    holidays.append(holiday)

        return holidays


class GeminiService:
    """Generate travel advice with Google's Gemini REST API."""

    BASE_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models"

    @staticmethod
    def generate_advice(prompt: str) -> str:
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not set. Add it to your environment before using AI advice.")

        model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip() or "gemini-3.8-flash"
        endpoint = f"{GeminiService.BASE_ENDPOINT}/{model}:generateContent"

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ]
        }

        try:
            response = requests.post(
                endpoint,
                params={"key": api_key},
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except requests.RequestException as exc:
            raise RuntimeError("Gemini could not be reached. Check your API key and internet connection.") from exc
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise RuntimeError("Gemini returned an unexpected response.") from exc


COUNTRIES = {
    "Nigeria": "NG",
    "United Kingdom": "GB",
    "United States": "US",
    "Canada": "CA",
    "United Arab Emirates": "AE",
    "Saudi Arabia": "SA",
    "Ghana": "GH",
    "Kenya": "KE",
    "South Africa": "ZA",
    "France": "FR",
    "Germany": "DE",
    "Italy": "IT",
    "Spain": "ES",
    "Turkey": "TR",
    "Egypt": "EG",
    "India": "IN",
    "Japan": "JP",
    "Australia": "AU",
    "Brazil": "BR",
}


def compare_countries(
    home_currency: str,
    country_one: str,
    country_one_daily: Decimal,
    country_two: str,
    country_two_daily: Decimal,
    duration: int,
) -> List[Dict]:
    """Compare user-provided daily travel estimates in the home currency."""
    if duration <= 0:
        raise ValueError("Duration must be greater than zero.")
    if country_one_daily < 0 or country_two_daily < 0:
        raise ValueError("Daily travel estimates cannot be negative.")

    return [
        {
            "country": country_one,
            "daily_cost": Decimal(str(country_one_daily)),
            "trip_cost": (Decimal(str(country_one_daily)) * duration).quantize(Decimal("0.01")),
            "currency": home_currency.upper(),
        },
        {
            "country": country_two,
            "daily_cost": Decimal(str(country_two_daily)),
            "trip_cost": (Decimal(str(country_two_daily)) * duration).quantize(Decimal("0.01")),
            "currency": home_currency.upper(),
        },
    ]
