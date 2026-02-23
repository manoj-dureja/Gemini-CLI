from src.data.data_manager import DataManager

def main():
    dm = DataManager()
    
    # 1. Fetch Nifty 50 list first to show ticker names
    print("Fetching Nifty 50 Ticker List...")
    nifty50_tickers = dm.get_nifty_50_tickers()
    
    if nifty50_tickers:
        print(f"Total tickers found: {len(nifty50_tickers)}")
        print(f"Tickers: {', '.join(nifty50_tickers)}")
        
        # 2. Download all data for these tickers (max history)
        print("\nStarting download for all Nifty 50 stocks (max history)...")
        dm.download_all_nifty_data(index_type='nifty50')
    else:
        print("Failed to fetch ticker list.")

if __name__ == "__main__":
    main()
