import sys
import os

# Add the root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget, QVBoxLayout, QWidget
from src.data.data_manager import DataManager
from src.gui.chart_view import ChartView
from src.gui.backtest_view import BacktestView
from src.gui.analysis_view import AnalysisView

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Indian Equities Backtest Framework - Agent 01")
        self.setGeometry(100, 100, 2560, 1440)
        
        # Initialize Data
        print("Initializing Data Manager...")
        self.dm = DataManager()
        
        self.init_ui()

    def init_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        
        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("QTabBar::tab { padding: 10px 40px; font-size: 14px; }")
        self.layout.addWidget(self.tabs)
        
        # 1. Chart Tab
        self.chart_view = ChartView(self.dm)
        self.tabs.addTab(self.chart_view, "Chart View")
        
        # 2. Backtest Tab
        self.backtest_view = BacktestView(self.dm)
        self.tabs.addTab(self.backtest_view, "Backtest Engine")
        
        # 3. Analysis Tab
        self.analysis_view = AnalysisView(self.dm)
        self.tabs.addTab(self.analysis_view, "Analytics")
        self.portfolio_tab = QWidget()
        self.tabs.addTab(self.portfolio_tab, "Portfolio")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Optional: Apply a global dark theme style
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
