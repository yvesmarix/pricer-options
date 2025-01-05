"""
A class to represent a financial product, specifically an underlying asset for options trading.

Attributes:
symbol (str): The ticker symbol of the underlying asset.
ticker (yf.Ticker): The Yahoo Finance ticker object for the underlying asset.
options_maturities (list): A list of available options expiration dates for the underlying asset.

Methods:
get_stock_data(historic: str) -> pd.DataFrame:
    Fetch historical stock data for the given period.

calls_puts_for_maturity(type: str, expiration_date: str | dt.date | dt.datetime) -> pd.DataFrame:
    Retrieve the options (calls or puts) table for a given expiration date.

get_volatility:
    Calculate and return the annualized volatility of the underlying asset based on historical data.

last_price:
    Retrieve the last closing price of the underlying asset.
"""

import yfinance as yf
import pandas as pd
import datetime as dt
import numpy as np


class Product:

    def __init__(self, symbol: str):
        self.symbol = symbol
        self.ticker = yf.Ticker(symbol)
        self.options_maturities = list(self.ticker.options)

    def get_stock_data(self, historic: str) -> pd.DataFrame:
        """
        Fetch historical stock data for a given Yahoo identifier.

        Parameters:
        symbol (str): Yahoo identifier for options.
        historic (str): The period for which to retrieve historical data (e.g., '1d', '1mo', '1y').

        Returns:
        pd.DataFrame: A DataFrame containing the historical stock data.
        """
        try:
            data = pd.DataFrame(self.ticker.history(historic))
            if data.empty:
                raise ValueError("No data retrieved for the given period.")
            return data
        except Exception as e:
            raise RuntimeError(f"Error fetching historical stock data: {e}")

    def calls_puts_for_maturity(
        self, type: str, expiration_date: str | dt.date | dt.datetime
    ) -> pd.DataFrame:
        """
        Retrieve the options (calls or puts) table for a given expiration date.
        type: either 'call' or 'put'
        expiration_date: choose one from the options_maturities attribute
        """
        if type.lower() not in ["call", "put"]:
            raise ValueError("Le type de l'option doit être 'call' ou 'put'.")

        if expiration_date not in self.options_maturities:
            raise ValueError(
                "La date d'expiration doit être une des dates disponibles dans options_maturities."
            )

        try:
            option_chain = self.ticker.option_chain(expiration_date)
            if type.lower() == "call":
                return option_chain.calls
            else:
                return option_chain.puts
        except Exception as e:
            raise RuntimeError(f"Erreur lors de la récupération des options: {e}")

    @property
    def get_volatility(self):
        df_vol = self.get_stock_data(historic="1y")
        df_vol["Return"] = np.log(df_vol["Close"].shift(1)) - np.log(df_vol["Close"])
        volatility = df_vol["Return"].std() * np.sqrt(252)
        return float(volatility)

    @property
    def last_price(self):
        return (
            self.ticker.history()
            .sort_values(by=["Date"], ascending=False)["Close"]
            .head(1)[0]
        )

    @property
    def get_dividend_yield(self):
        q = self.ticker.get_info().get("dividendYield")
        if q is None or q == {}:
            return self.get_stock_data(historic="1y")[
                "Dividends"
            ].sum() / self.get_stock_data(historic="1y")["Close"].sort_index(
                ascending=False
            ).head(
                1
            )
        else:
            return q
