import math


class BinomialPricer:

    def price(
        S: int | float,
        K: int | float,
        r: float,
        T: float,
        q: float,
        sigma: float,
        N: int,
        option_type: str,
        style: str,
    ):
        """
        Prix d'une option européenne ou américaine via le modèle binomial ou
        modèle Cox, Ross, et Rubinstein. Nous ne traitons pas le cas
        d'une option Bermudienne.

        Paramètres :
        ------------
        S0            : prix initial du sous-jacent
        K             : prix d'exercice (strike)
        r             : taux sans risque (en décimal, ex : 0.03 pour 3%)
        T             : temps jusqu’à l’échéance (en années)
        q             : dividend yield annualized
        sigma         : volatilité (en décimal)
        N             : nombre d'étapes dans l'arbre binomial.
                        On peut augmenter le nombre d’étapes N pour améliorer la précision.
                        Attention cependant au coût de calcul (complexité O(N^2)).
        option_type   : 'call' ou 'put'
        style : 'american' ou 'european'

        Retour :
        --------
        La valeur de l'option au temps 0 (prix théorique).
        """
        if q is None:
            q=0
        # Paramètres de la recombinaison binomiale
        dt = T / N
        u = math.exp(sigma * math.sqrt(dt))  # facteur de hausse
        d = math.exp(-sigma * math.sqrt(dt))  # facteur de baisse

#--> rajout possible du dividend yield --> (math.exp((r - y) * dt) - d)/(u - d)
        p = (math.exp((r - q) * dt) - d) / (u - d)  # prob. risque neutre (risk-neutral)
        q = 1 - p
        # Tableaux pour stocker les prix du sous-jacent et l'option
        stock_prices = [0] * (N + 1)
        option_values = [0] * (N + 1)

        # Calcul des prix du sous-jacent aux noeuds terminaux (à l'échéance)
        for i in range(N + 1):
            stock_prices[i] = S * (u ** (N - i)) * (d**i)

        # Payoff à l'échéance en fonction de l'option (call ou put)
        for i in range(N + 1):
            if option_type == "call":
                option_values[i] = max(stock_prices[i] - K, 0)
            elif option_type == "put":
                option_values[i] = max(K - stock_prices[i], 0)
            else:
                raise ValueError("option_type doit être 'call' ou 'put'.")

        # Remontée de l'arbre pour valoriser l'option à t=0
        for step in range(N - 1, -1, -1):
            for i in range(step + 1):
                # Valeur en tenant compte de la probabilité risque neutre (hold value)
                hold_value = math.exp(-r * dt) * (
                    p * option_values[i] + q * option_values[i + 1]
                )

                if style == "american":
                    # Si l'option est américaine, on vérifie la valeur d'exercice immédiat
                    stock_price = S * (u ** (step - i)) * (d**i)
                    if option_type == "call":
                        exercise_value = max(stock_price - K, 0)
                    else:  # put
                        exercise_value = max(K - stock_price, 0)

                    # On garde la valeur max entre tenir l'option (hold_value) ou l'exercer maintenant
                    option_values[i] = max(hold_value, exercise_value)
                else:
                    # Option européenne : on ne peut pas exercer avant l'échéance
                    option_values[i] = hold_value

        # La valeur en 0,0 est le prix de l'option
        return option_values[0]
