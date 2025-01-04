import numpy as np
from scipy.stats import norm


class BlackScholesPricer:
    def __init__(self):
        self.N = norm.cdf

    def price(self, S, K, T, r, sigma, option_type, style):
        """
        Calculate option price using Black-Scholes formula

        Parameters:
        -----------
        S : float
            Current stock price
        K : float
            Strike price
        T : float
            Time to maturity (in years)
        r : float
            Risk-free rate (annual)
        sigma : float
            Volatility (annual)
        option_type : str
            Type of option - 'call' or 'put'

        Returns:
        --------
        float : Option price
        """
        if style == "american":
            print(
                """You're trying to price an american option. 
                  Black-Scholes is built for European ones."""
            )
        else:
            # Ensure T is positive
            T = max(T, 1e-10)  # Avoid division by zero

            d1 = (np.log(S / K) + (r + sigma**2 / 2) * T) / (sigma * np.sqrt(T))
            d2 = d1 - sigma * np.sqrt(T)

            if option_type.lower() == "call":
                price = S * self.N(d1) - K * np.exp(-r * T) * self.N(d2)
            elif option_type.lower() == "put":
                price = K * np.exp(-r * T) * self.N(-d2) - S * self.N(-d1)
            else:
                raise ValueError("option_type must be 'call' or 'put'")

        return price
    @staticmethod
    def calculate_greeks(S, K, T, r, sigma, option_type="call"):
        """
        Calculate option Greeks

        Returns:
        --------
        dict : Dictionary containing all Greeks
        """
        d1 = (np.log(S / K) + (r + (sigma**2) / 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)

        # Calculate normal probability density
        N_prime = norm.pdf

        # Delta
        if option_type.lower() == "call":
            delta = norm.cdf(d1)
        else:
            delta = -norm.cdf(-d1)

        # Gamma
        gamma = N_prime(d1) / (S * sigma * np.sqrt(T))

        # Theta
        if option_type.lower() == "call":
            theta = -S * N_prime(d1) * sigma / (2 * np.sqrt(T)) - r * K * np.exp(
                -r * T
            ) * norm.cdf(d2)
        else:
            theta = -S * N_prime(d1) * sigma / (2 * np.sqrt(T)) + r * K * np.exp(
                -r * T
            ) * norm.cdf(-d2)

        # Vega (same for calls and puts)
        vega = S * np.sqrt(T) * N_prime(d1)

        # Rho
        if option_type.lower() == "call":
            rho = K * T * np.exp(-r * T) * norm.cdf(d2)
        else:
            rho = -K * T * np.exp(-r * T) * norm.cdf(-d2)

        return {
            "delta": delta,
            "gamma": gamma,
            "theta": theta / 365,  # Converting to daily theta
            "vega": vega / 100,  # Converting to 1% vol change
            "rho": rho / 100,  # Converting to 1% rate change
        }
