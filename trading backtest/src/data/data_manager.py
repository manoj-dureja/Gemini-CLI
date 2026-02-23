import pandas as pd
import os
import glob
import yfinance as yf

class DataManager:
    def __init__(self, data_dir='data'):
        """
        Initializes the DataManager with the directory structure:
        data/
          daily/ (contains CSVs)
        """
        self.data_dir = data_dir
        self.daily_dir = os.path.join(data_dir, 'daily')
        
        # Ensure directory exists
        if not os.path.exists(self.daily_dir):
            os.makedirs(self.daily_dir, exist_ok=True)
        
        # Dictionaries for fast access
        self.daily_data = {}
        self.weekly_data = {}
        self.monthly_data = {}
        
        self.load_and_resample_all()

    def load_and_resample_all(self):
        """
        Loads all CSV files from data/daily, resamples them, and populates the dictionaries.
        """
        csv_files = glob.glob(os.path.join(self.daily_dir, "*.csv"))
        if not csv_files:
            print(f"Warning: No CSV files found in {self.daily_dir}")
            return

        print(f"Loading and resampling {len(csv_files)} files...")
        for file_path in csv_files:
            ticker = os.path.basename(file_path).replace(".csv", "")
            try:
                # Robust loading: check first few lines to see if we need to skip rows
                with open(file_path, 'r') as f:
                    first_line = f.readline()
                
                if "Ticker" in first_line or "Price," in first_line:
                    # Skip the metadata rows in original files (Ticker and Date rows)
                    df_daily = pd.read_csv(file_path, skiprows=[1, 2], index_col=0, parse_dates=True)
                else:
                    # Normal yfinance style or index file
                    df_daily = pd.read_csv(file_path, index_col=0, parse_dates=True)
                
                if df_daily.empty:
                    continue
                
                # Standardize columns to lowercase for easier access
                df_daily.columns = [col.lower() for col in df_daily.columns]
                
                # Verify that we have a DatetimeIndex
                if not isinstance(df_daily.index, pd.DatetimeIndex):
                    df_daily.index = pd.to_datetime(df_daily.index, errors='coerce')
                    df_daily = df_daily.dropna(subset=None)
                
                # Store Daily
                self.daily_data[ticker] = df_daily
                
                # Resample to Weekly and Monthly ONCE per session
                self.weekly_data[ticker] = self._resample_data(df_daily, 'W-FRI')
                self.monthly_data[ticker] = self._resample_data(df_daily, 'ME')
                
            except Exception as e:
                print(f"Error processing {ticker}: {e}")

    def _resample_data(self, df, timeframe):
        """
        Resamples OHLCV data to a given timeframe.
        """
        resampler = df.resample(timeframe)
        resampled_df = resampler.agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
        return resampled_df

    def get_data(self, ticker, timeframe='daily'):
        """
        Returns the requested dataframe from memory.
        """
        if timeframe == 'daily':
            return self.daily_data.get(ticker)
        elif timeframe == 'weekly':
            return self.weekly_data.get(ticker)
        elif timeframe == 'monthly':
            return self.monthly_data.get(ticker)
        return None

    def get_all_tickers(self):
        return sorted(list(self.daily_data.keys()))

    def download_nifty_index(self):
        """
        Downloads max historical data for the Nifty 50 Index (^NSEI) and saves to data/daily.
        """
        ticker = "^NSEI"
        print(f"Downloading data for Index: {ticker}...")
        try:
            df = yf.download(ticker, period="max")
            if not df.empty:
                filename = os.path.join(self.daily_dir, f"{ticker}.csv")
                df.to_csv(filename)
                print(f"Saved Nifty Index to {filename}")
                return True
        except Exception as e:
            print(f"Error downloading Nifty Index: {e}")
        return False

if __name__ == "__main__":
    dm = DataManager()
    tickers = dm.get_all_tickers()
    if tickers:
        print(f"Loaded {len(tickers)} tickers.")
