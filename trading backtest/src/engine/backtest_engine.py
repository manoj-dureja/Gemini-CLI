import pandas as pd
import numpy as np

class BacktestEngine:
    def __init__(self, initial_capital=100000, brokerage=0.0005, stt=0.001):
        """
        initial_capital: Starting cash in INR
        brokerage: Percentage per trade (default 0.05%)
        stt: Securities Transaction Tax (approx 0.1% for delivery)
        """
        self.initial_capital = initial_capital
        self.brokerage = brokerage
        self.stt = stt
        
        self.reset()

    def reset(self):
        self.cash = self.initial_capital
        self.position = 0  # Number of shares held
        self.portfolio_value = self.initial_capital
        self.trades = []   # List of trade details
        self.equity_curve = []

    def run(self, data, signals):
        """
        data: DataFrame with OHLC
        signals: Series/DataFrame with 1 (Buy), -1 (Sell), 0 (Hold)
        """
        self.reset()
        
        # Ensure data and signals are aligned
        df = data.copy()
        df['signal'] = signals
        
        for i in range(len(df)):
            current_price = df['close'].iloc[i]
            signal = df['signal'].iloc[i]
            current_date = df.index[i]

            # 1. Execute Sell Signal
            if signal == -1 and self.position > 0:
                sell_value = self.position * current_price
                costs = sell_value * (self.brokerage + self.stt)
                self.cash += (sell_value - costs)
                
                self.trades.append({
                    'type': 'SELL',
                    'date': current_date,
                    'price': current_price,
                    'units': self.position,
                    'value': sell_value,
                    'costs': costs
                })
                self.position = 0

            # 2. Execute Buy Signal
            elif signal == 1 and self.position == 0:
                # Buy with all available cash
                # (Leaving a small buffer for costs)
                max_buy_value = self.cash * 0.995 
                units_to_buy = int(max_buy_value // current_price)
                
                if units_to_buy > 0:
                    buy_value = units_to_buy * current_price
                    costs = buy_value * self.brokerage # STT usually not on buy for delivery
                    self.cash -= (buy_value + costs)
                    self.position = units_to_buy
                    
                    self.trades.append({
                        'type': 'BUY',
                        'date': current_date,
                        'price': current_price,
                        'units': units_to_buy,
                        'value': buy_value,
                        'costs': costs
                    })

            # 3. Update Equity Curve
            current_val = self.cash + (self.position * current_price)
            self.equity_curve.append(current_val)

        return self.get_results()

    def get_results(self):
        if not self.equity_curve:
            return {}
            
        final_value = self.equity_curve[-1]
        total_return = (final_value - self.initial_capital) / self.initial_capital * 100
        
        # Convert equity curve to series for easier analysis
        equity_series = pd.Series(self.equity_curve)
        
        # Max Drawdown
        roll_max = equity_series.cummax()
        drawdown = (equity_series - roll_max) / roll_max
        max_drawdown = drawdown.min() * 100
        
        return {
            'initial_capital': self.initial_capital,
            'final_value': final_value,
            'total_return_pct': total_return,
            'max_drawdown_pct': max_drawdown,
            'total_trades': len(self.trades),
            'equity_curve': self.equity_curve
        }
