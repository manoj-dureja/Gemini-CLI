from abc import ABC, abstractmethod
import pandas as pd

class Strategy(ABC):
    def __init__(self, name):
        self.name = name
        self.data = None
        self.signals = None

    @abstractmethod
    def generate_signals(self, data):
        """
        This method should be implemented by subclasses to define trading logic.
        It should return a DataFrame with signals (e.g., 1 for Buy, -1 for Sell, 0 for Hold).
        """
        pass

    def set_data(self, data):
        self.data = data
