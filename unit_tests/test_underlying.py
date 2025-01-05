import yfinance as yf
import pandas as pd
import datetime as dt
import numpy as np
import unittest
from optionspricer.products.underlying import Product


class TestProduct(unittest.TestCase):

    def setUp(self):
        self.my_product = Product("AAPL")
        self.historic = "1y"
        self.expiry_date = list(yf.Ticker("AAPL").options)[0]
        self.type = 'call'

    def test_get_stock_data(self):
        self.assertIsInstance(
            self.my_product.get_stock_data(self.historic), pd.DataFrame
        )
        self.assertTrue(
            "Close" in list(self.my_product.get_stock_data(self.historic).columns)
        )
        self.assertTrue(
            "Dividends" in list(self.my_product.get_stock_data(self.historic).columns)
        )

    def test_calls_puts_for_maturity(self):
        self.assertIsInstance(
            self.my_product.calls_puts_for_maturity(expiration_date=self.expiry_date, type=self.type),
            pd.DataFrame,
        )

    def test_get_volatility(self):
        self.assertIsInstance(self.my_product.get_volatility, float)

    def test_last_price(self):
        self.assertIsInstance(self.my_product.last_price, float|int)

    def test_get_dividend_yield(self):
        self.assertIsInstance(self.my_product.get_dividend_yield, float|int)

if __name__ == "__main__":
    unittest.main()