"""
This module defines the `Option` class, which represents a financial option and provides methods to retrieve option data and infer option style.

Methods:
    __init__(self, symbol: int):
        Initializes an Option instance with the given option symbol.
        
    get_option_data(self):
        Retrieves and returns option data including spot price, strike price, maturity, volatility, type, currency, and style.
        
    get_free_rate():
        Static method that retrieves the 3-month Treasury bond rate as an approximation of the risk-free rate.
        
    infer_option_style(self):
        Infers whether options on the given ticker symbol are American or European based on the quote type from Yahoo Finance.

Attributes:
    symbol (int): The option symbol.
    underlying (str): The underlying asset symbol.
    ticker (yf.Ticker): The Yahoo Finance ticker object for the option.
    strike (float): The strike price of the option.
    expire_date (datetime.date): The expiration date of the option.
    maturity (float): The maturity of the option in years.
    currency (str): The currency of the option.
    underlying_share (str): The underlying asset symbol.
    volatility (float): The volatility of the underlying asset.
    type (str): The type of the option (e.g., 'Call' or 'Put').
    spot (float): The spot price of the underlying asset.
"""

import yfinance as yf
import pandas as pd
import datetime as dt
from optionspricer.products.underlying import Product


class Option:

    def __init__(self, symbol: int):
        """
        symbol: must be an option symbol --> eg: AAPL250103C00140000
        """
        self.symbol = symbol
        self.ticker = yf.Ticker(symbol)
        self.underlying = self.ticker.get_info().get("underlyingSymbol")
        self.underlying_ticker = yf.Ticker(self.underlying)
        self.underlying_square = self.underlying_ticker.get_info().get("underlyingSymbol")

    def get_option_data(self):

        dict_info = self.ticker.get_info()
        self.strike = dict_info["strikePrice"]

        # Get maturity by years
        self.expire_date = dt.date.fromtimestamp(dict_info["expireDate"])
        self.maturity = (self.expire_date - dt.date.today()).days / 365

        self.currency = dict_info["currency"]
        self.underlying_share = dict_info["underlyingSymbol"]
        self.volatility = Product(self.underlying_share).get_volatility

        # Le dictionnaire peut être différent selon l'option
        if dict_info.get("longName") is not None:
            self.type = dict_info["longName"].split(" ")[-1]
        else:
            self.type = dict_info["shortName"].split(" ")[-1]

        self.spot = Product(self.underlying_share).last_price

        return (
            self.spot,
            self.strike,
            self.maturity,
            self.volatility,
            self.type,
            self.currency
        )

    @staticmethod
    def get_free_rate():
        # Récupère le taux des bons du Trésor à 3 mois (approximation du taux sans risque)
        r = yf.download("^TNX", period="1d")["Close"][0]
        return r

    @property
    def infer_option_style(self):
        """
        Infers whether options on the given ticker_symbol are American or European,
        based on whether it's recognized as an INDEX vs. a STOCK/ETF by Yahoo Finance.

        Returns:
            str: 'American', 'European', or 'Unknown'
        """

        # The 'quoteType' field often indicates 'EQUITY', 'ETF', 'INDEX', etc.
        # Not all symbols have this field populated, so we handle potential KeyError.
        quote_type = yf.Ticker(self.underlying).get_info().get("quoteType")
        quote_type_square = yf.Ticker(self.underlying_square).get_info().get("quoteType")

        if quote_type == 'ETF' and (quote_type_square == 'INDEX' 
        or ('index' in yf.Ticker(self.underlying_square).get_info().get('longBusinessSummary'))):
            return 'european'
        elif quote_type == "INDEX":
            return "european"
        elif quote_type in ["EQUITY", "MUTUALFUND"]:
            return "american"
        else:
            return "unknown"
