from src.data.data_manager import DataManager
import os

if __name__ == "__main__":
    dm = DataManager()
    # Ensure daily directory exists
    if not os.path.exists(dm.daily_dir):
        os.makedirs(dm.daily_dir)
    
    success = dm.download_nifty_index()
    if success:
        print("Successfully downloaded Nifty Index.")
    else:
        print("Failed to download Nifty Index.")
