import pandas as pd
from .base_strategy import Strategy

class SMAStackStrategy(Strategy):
    def __init__(self, p_fast=8, p_med=20, p_slow=50):
        super().__init__(f"SMA Stack ({p_fast}, {p_med}, {p_slow})")
        self.p_fast = p_fast
        self.p_med = p_med
        self.p_slow = p_slow

    def generate_signals(self, data):
        """
        Buy: SMA 8 > SMA 20 > SMA 50
        Sell: SMA 8 < SMA 20
        """
        df = data.copy()
        
        # Calculate SMAs
        df['sma_f'] = df['close'].rolling(window=self.p_fast).mean()
        df['sma_m'] = df['close'].rolling(window=self.p_med).mean()
        df['sma_s'] = df['close'].rolling(window=self.p_slow).mean()
        
        signals = pd.Series(0, index=df.index)
        position = 0 # 0: out, 1: in
        
        for i in range(len(df)):
            # Need enough data for the slowest SMA
            if i < self.p_slow:
                continue
                
            row = df.iloc[i]
            
            # Entry Logic: Bullish Stack
            if position == 0:
                if row['sma_f'] > row['sma_m'] > row['sma_s']:
                    signals.iloc[i] = 1
                    position = 1
            
            # Exit Logic: Fast crosses below Medium
            elif position == 1:
                if row['sma_f'] < row['sma_m']:
                    signals.iloc[i] = -1
                    position = 0
                    
        return signals
