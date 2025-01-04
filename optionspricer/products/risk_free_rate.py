import pandas as pd
import requests
from datetime import datetime, date, timedelta
import numpy as np
import yfinance as yf
from abc import ABC, abstractmethod
import warnings


class RateSource(ABC):
    @abstractmethod
    def get_rate(self, maturity_years=None):
        pass


class USTreasuryRate(RateSource):
    """Generic rate source leveraging Alpha Vantage API."""

    def __init__(self, function="TREASURY_YIELD"):
        self.api_key = "D2Z0OIECSWGP530F"
        self.base_url = "https://www.alphavantage.co/query"
        self.function = function

    def get_rate(self, maturity="3month"):
        """Retrieve rate for a specific maturity using Alpha Vantage."""
        try:
            params = {
                "function": self.function,
                "interval": "daily",
                "maturity": maturity,
                "apikey": self.api_key,
            }
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()

            # Extract the most recent rate
            yield_data = data.get("data", [])
            if not yield_data:
                return None
            latest_entry = yield_data[0]
            return float(latest_entry["value"]) / 100  # Convert to decimal
        except Exception as e:
            print(f"Error fetching rate from Alpha Vantage: {e}")
            return None


class FreeRate:
    """
    Since the ECB API does not yet allow querying ESTR, I used an external development project.
    """
    def __init__(self):
        self.api_key = '4DKvYP+ZoE4QBMuBd98Pew==Hyn2jkemvEU3IrQq'
        self.base_url = "https://api.api-ninjas.com/v1/interestrate?name={}"

    def get_rate(self, nom_tx):
        try:
            response = requests.get(self.base_url.format(nom_tx), headers={'X-Api-Key': self.api_key})
            response.raise_for_status()
            data = response.json()
            if 'non_central_bank_rates' in data and data['non_central_bank_rates']:
                return data['non_central_bank_rates'][0]['rate_pct'] / 100
            else:
                print(f"No rate data found for {nom_tx}")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching rate for {nom_tx}: {e}")



class ProxyRateSource(RateSource):
    """Proxy rate source for currencies without direct rate feeds"""

    def __init__(self, base_currency, proxy_currency="USD"):
        self.base_currency = base_currency
        self.proxy_currency = proxy_currency

    def get_rate(self):
        try:
            # Get proxy currency rate (usually USD rate)
            proxy_source = USTreasuryRate()
            proxy_rate = proxy_source.get_rate()

            if proxy_rate is None:
                return None

            # Get spot exchange rates
            fx_pair1 = f"{self.proxy_currency}{self.base_currency}=X"
            fx_pair2 = f"{self.base_currency}{self.proxy_currency}=X"

            try:
                # Try direct rate
                spot_rate = yf.Ticker(fx_pair1).info["regularMarketPrice"]
                rate_adjustment = np.log(spot_rate)
            except:
                try:
                    # Try inverse rate
                    spot_rate = yf.Ticker(fx_pair2).info["regularMarketPrice"]
                    rate_adjustment = -np.log(spot_rate)
                except:
                    return None

            # Adjust proxy rate based on exchange rate difference
            adjusted_rate = proxy_rate + rate_adjustment * 0.1
            return max(adjusted_rate, 0)  # Ensure non-negative rate

        except Exception as e:
            print(f"Error calculating proxy rate for {self.base_currency}: {e}")
            return None


class MultiCurrencyRiskFreeRate:
    """Main class for fetching risk-free rates for different currencies"""

    def __init__(self):
        self.primary_sources = {
            "USD": USTreasuryRate().get_rate(),
            "EUR": FreeRate().get_rate('ester'),
            "GBP": FreeRate().get_rate('sonia'),
            "JPY": FreeRate().get_rate('tonar'),
            "CHF": FreeRate().get_rate('saron'),
        }

        # Reference rates and central banks for major currencies
        self.currency_info = {
            "USD": {
                "name": "US Dollar",
                "reference_rate": "US Treasury Bills Rate",
                "central_bank": "Federal Reserve",
            },
            "EUR": {
                "name": "Euro",
                "reference_rate": "€STR",
                "central_bank": "European Central Bank",
            },
            "GBP": {
                "name": "British Pound",
                "reference_rate": "SONIA",
                "central_bank": "Bank of England",
            },
            "JPY": {
                "name": "Japanese Yen",
                "reference_rate": "TONAR",
                "central_bank": "Bank of Japan",
            },
            "CHF": {
                "name": "Swiss Franc",
                "reference_rate": "SARON",
                "central_bank": "Swiss National Bank",
            },
            "AUD": {
                "name": "Australian Dollar",
                "reference_rate": "AONIA",
                "central_bank": "Reserve Bank of Australia",
            },
            "CAD": {
                "name": "Canadian Dollar",
                "reference_rate": "CORRA",
                "central_bank": "Bank of Canada",
            },
            # Ajoutez d'autres devises selon vos besoins
        }

    def get_risk_free_rate(self, currency, fallback_method="proxy"):
        """
        Get risk-free rate for specified currency and maturity

        Parameters:
        -----------
        currency : str
            Currency code (e.g., 'USD', 'EUR', 'GBP', etc.)
        maturity_years : float, optional
            Maturity in years (e.g., 0.25 for 3 months)
        fallback_method : str
            Method to use for non-primary currencies:
            - 'proxy': Use proxy rate based on USD rate and FX
            - 'nearest': Use nearest major currency rate

        Returns:
        --------
        dict : Dictionary containing rate information
        """
        # Check if it's a primary currency
        if currency in self.primary_sources:
            rate = self.primary_sources[currency]
            source_type = "primary"
            rate_source = self.currency_info[currency]["reference_rate"]

        # Handle non-primary currencies
        else:
            if fallback_method == "proxy":
                proxy_source = ProxyRateSource(currency)
                rate = proxy_source.get_rate()
                source_type = "proxy"
                rate_source = f"Proxy based on USD rate and {currency}/USD FX"

            elif fallback_method == "nearest":
                # Find nearest major currency by timezone/region
                nearest_currency = self._find_nearest_currency(currency)
                rate = self.primary_sources[nearest_currency].get_rate()
                source_type = "nearest"
                rate_source = f"Approximated using {nearest_currency} rate"

            else:
                raise ValueError(f"Invalid fallback method: {fallback_method}")

        if rate is not None:
            result = {
                "currency": currency,
                "rate": rate,
                "rate_source": rate_source,
                "source_type": source_type,
                "maturity_years": "3month",
                "fetch_date": date.today().isoformat(),
            }

            if currency in self.currency_info:
                result.update(
                    {
                        "currency_name": self.currency_info[currency]["name"],
                        "central_bank": self.currency_info[currency]["central_bank"],
                    }
                )

            # Add warning for non-primary currencies
            if source_type != "primary":
                warnings.warn(
                    f"Using {source_type} rate for {currency}. "
                    "This is an approximation and should be used with caution."
                )

            return result

        return None

    def _find_nearest_currency(self, currency):
        """Find nearest major currency based on region/timezone.
        This is a pretty "brute force" way of doing it but 
        should work for most cases."""
        # Simplified mapping of currencies to major currencies
        currency_mapping = {
            # Asia/Pacific
            "JPY": "USD",
            "CNY": "USD",
            "HKD": "USD",
            "SGD": "USD",
            "KRW": "USD",
            "TWD": "USD",
            "INR": "USD",
            # Europe
            "CHF": "EUR",
            "SEK": "EUR",
            "NOK": "EUR",
            "DKK": "EUR",
            "PLN": "EUR",
            "CZK": "EUR",
            "HUF": "EUR",
            # Americas
            "CAD": "USD",
            "MXN": "USD",
            "BRL": "USD",
            # Oceania
            "AUD": "USD",
            "NZD": "USD",
        }

        return currency_mapping.get(currency, "USD")
