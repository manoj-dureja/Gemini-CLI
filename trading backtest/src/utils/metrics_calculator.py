import pandas as pd
import numpy as np

class MetricsCalculator:
    @staticmethod
    def calculate_returns(series):
        return series.pct_change().dropna()

    @staticmethod
    def filter_data_by_years(data, years):
        """
        Slices data to the last N years. If years='max', returns all data.
        """
        if years == 'max' or years is None:
            return data
        
        end_date = data.index[-1]
        start_date = end_date - pd.DateOffset(years=years)
        
        filtered_data = data[data.index >= start_date]
        return filtered_data

    @staticmethod
    def calculate_metrics(data, risk_free_rate=0.06):
        """
        Calculates key financial metrics for the provided (potentially sliced) OHLC data.
        """
        if data is None or data.empty or len(data) < 2:
            return {}

        returns = MetricsCalculator.calculate_returns(data['close'])
        if returns.empty:
            return {}

        # 1. CAGR (Compounded Annual Growth Rate)
        total_return = (data['close'].iloc[-1] / data['close'].iloc[0]) - 1
        days = (data.index[-1] - data.index[0]).days
        
        # Standard CAGR formula: (Ending Value / Beginning Value) ^ (1 / Years) - 1
        years_elapsed = days / 365.25
        if years_elapsed > 0:
            cagr = (data['close'].iloc[-1] / data['close'].iloc[0]) ** (1 / years_elapsed) - 1
        else:
            cagr = 0
        
        # 2. Risk Metrics (Annualized Volatility)
        volatility = returns.std() * np.sqrt(252)
        
        # 3. Risk-Adjusted Metrics
        excess_return = cagr - risk_free_rate
        sharpe_ratio = excess_return / volatility if volatility > 0 else 0
        
        # 4. Drawdown
        roll_max = data['close'].cummax()
        drawdowns = (data['close'] - roll_max) / roll_max
        max_drawdown = drawdowns.min()

        return {
            'total_return': total_return,
            'cagr': cagr,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'returns_series': returns,
            'drawdown_series': drawdowns,
            'years_actual': years_elapsed
        }

    @staticmethod
    def get_monthly_returns_matrix(returns):
        """
        Converts daily returns into a Year x Month matrix.
        """
        if returns.empty:
            return pd.DataFrame()
            
        monthly_df = returns.resample('ME').apply(lambda x: (1 + x).prod() - 1)
        matrix = monthly_df.to_frame(name='return')
        matrix['year'] = matrix.index.year
        matrix['month'] = matrix.index.month
        
        pivot_table = matrix.pivot(index='year', columns='month', values='return')
        month_names = {1:'Jan', 2:'Feb', 3:'Mar', 4:'Apr', 5:'May', 6:'Jun', 
                       7:'Jul', 8:'Aug', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Dec'}
        pivot_table.rename(columns=month_names, inplace=True)
        return pivot_table
