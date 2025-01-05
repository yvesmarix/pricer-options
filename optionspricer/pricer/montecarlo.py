import numpy as np

class MonteCarlo:

    def pricer(S, K, T, r, q, sigma, n_simulations, option_type='call'):
        """
        Monte Carlo simulation for European option pricing.
        
        Parameters:
        - S: float, initial price of the underlying asset
        - K: float, strike price of the option
        - T: float, time to maturity in years
        - r: float, annual risk-free rate
        - q: float, annualized dividend yield
        - sigma: float, volatility of the underlying asset
        - n_simulations: int, number of Monte Carlo simulations
        - option_type: str, 'call' or 'put'
        
        Returns:
        - float, estimated option price
        """
        if q is None:
            q=0
        # Generate random price paths using Geometric Brownian Motion
        z = np.random.standard_normal(n_simulations)
        ST = S * np.exp((r - q - 0.5 * sigma**2) * T + sigma * np.sqrt(T) * z)
        
        # Calculate the payoff
        if option_type == 'call':
            payoffs = np.maximum(ST - K, 0)
        elif option_type == 'put':
            payoffs = np.maximum(K - ST, 0)
        else:
            raise ValueError("option_type must be 'call' or 'put'")
        
        # Discount payoffs to present value
        option_price = np.exp(-r * T) * np.mean(payoffs)
        return option_price
