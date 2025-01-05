import yfinance as yf
import pandas as pd
import datetime as dt
import numpy as np
import unittest
from optionspricer.products.option import Option
from optionspricer.products.option import Product
import warnings
warnings.filterwarnings('ignore')

class TestOption(unittest.TestCase):

    def setUp(self):
        self.my_product = Product("AAPL")
        self.expiry_date = list(yf.Ticker("AAPL").options)[0]
        self.symbol = self.my_product.calls_puts_for_maturity(
            type="call", expiration_date=self.expiry_date
        ).contractSymbol.head(1).values[0]
        self.my_option = Option(self.symbol)

    def test_get_option_data(self):
        self.assertIsInstance(self.my_option.get_option_data(), tuple)

        self.assertIsInstance(self.my_option.get_option_data()[0], int | float)
        self.assertIsInstance(self.my_option.get_option_data()[1], int | float)
        self.assertIsInstance(self.my_option.get_option_data()[2], int | float)
        self.assertIsInstance(self.my_option.get_option_data()[3], int | float)

        self.assertGreater(self.my_option.get_option_data()[0], 0)
        self.assertGreater(self.my_option.get_option_data()[1], 0)
        self.assertGreater(self.my_option.get_option_data()[2], 0)
        self.assertGreater(self.my_option.get_option_data()[3], 0)
        self.assertIn(self.my_option.get_option_data()[4], ["call", "put"])
        self.assertTrue(len(self.my_option.get_option_data()[5]) == 3)

    def test_infer_option_style(self):
        self.assertIsInstance(self.my_option.infer_option_style, str)
        self.assertIn(
            self.my_option.infer_option_style, ["european", "american", "unknown"]
        )


if __name__ == "__main__":
    unittest.main()
