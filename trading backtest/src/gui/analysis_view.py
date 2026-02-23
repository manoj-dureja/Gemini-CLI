from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QComboBox, 
                             QPushButton, QLabel, QFrame, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QScrollArea, QSplitter)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
import pyqtgraph as pg
import pandas as pd
import numpy as np
from src.utils.metrics_calculator import MetricsCalculator

class MetricCard(QFrame):
    def __init__(self, title, value, unit="", is_percent=False, scale_factor=1.0):
        super().__init__()
        self.scale_factor = scale_factor
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet(f"""
            MetricCard {{
                background-color: #1e222d;
                border: 1px solid #363c4e;
                border-radius: {int(8 * scale_factor)}px;
                padding: {int(15 * scale_factor)}px;
            }}
        """)
        layout = QVBoxLayout(self)
        
        self.title_label = QLabel(title.upper())
        self.title_label.setStyleSheet(f"color: #787b86; font-size: {int(11 * scale_factor)}px; font-weight: bold;")
        
        display_val = f"{value * 100:.2f}%" if is_percent else f"{value:.2f}"
        self.val_label = QLabel(f"{display_val}{unit}")
        self.val_label.setStyleSheet(f"color: #d1d4dc; font-size: {int(22 * scale_factor)}px; font-weight: bold;")
        
        if is_percent:
            color = "#00b894" if value >= 0 else "#ff7675"
            self.val_label.setStyleSheet(f"color: {color}; font-size: {int(22 * scale_factor)}px; font-weight: bold;")
            
        layout.addWidget(self.title_label)
        layout.addWidget(self.val_label)

class AnalysisView(QWidget):
    def __init__(self, data_manager):
        super().__init__()
        self.dm = data_manager
        self.scale_factor = 1.2
        self.current_ticker = None
        
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # 1. Header with Selection and Timeframe
        header = QFrame()
        header_layout = QHBoxLayout(header)
        
        self.ticker_selector = QComboBox()
        self.ticker_selector.setFixedWidth(int(250 * self.scale_factor))
        self.ticker_selector.setStyleSheet(f"font-size: {int(14 * self.scale_factor)}px; padding: 5px;")
        tickers = self.dm.get_all_tickers()
        self.ticker_selector.addItems(tickers)
        self.ticker_selector.currentTextChanged.connect(self.on_ticker_changed)
        
        self.period_selector = QComboBox()
        self.period_selector.addItems(['Max', '15 Years', '10 Years', '5 Years', '3 Years', '1 Year'])
        self.period_selector.currentTextChanged.connect(self.on_period_changed)
        self.period_selector.setFixedWidth(int(150 * self.scale_factor))
        
        self.run_btn = QPushButton("Refresh Analysis")
        self.run_btn.setStyleSheet(f"background-color: #2962ff; color: white; padding: 8px 20px; font-weight: bold; border-radius: 4px; font-size: {int(13 * self.scale_factor)}px;")
        self.run_btn.clicked.connect(lambda: self.update_analysis(self.ticker_selector.currentText()))

        header_layout.addWidget(QLabel("Ticker:"))
        header_layout.addWidget(self.ticker_selector)
        header_layout.addWidget(QLabel("Period:"))
        header_layout.addWidget(self.period_selector)
        header_layout.addWidget(self.run_btn)
        header_layout.addStretch()
        main_layout.addWidget(header)

        # 2. Scrollable Dashboard Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        self.dash_content = QWidget()
        self.dash_layout = QVBoxLayout(self.dash_content)
        self.dash_layout.setSpacing(25)
        
        # Section A: Info/Warning Label
        self.info_label = QLabel("Showing Max History")
        self.info_label.setStyleSheet(f"color: #787b86; font-size: {int(14 * self.scale_factor)}px; font-style: italic;")
        self.dash_layout.addWidget(self.info_label)

        # Section B: Metric Cards
        self.cards_layout = QHBoxLayout()
        self.dash_layout.addLayout(self.cards_layout)
        
        # Section C: Charts
        self.splitter = QSplitter(Qt.Vertical)
        self.ret_plot = pg.PlotWidget(title="Cumulative Returns (%)")
        self.ret_plot.setBackground('#131722')
        self.ret_plot.showGrid(x=True, y=True, alpha=0.1)
        self.splitter.addWidget(self.ret_plot)
        
        self.dd_plot = pg.PlotWidget(title="Drawdown (%)")
        self.dd_plot.setBackground('#131722')
        self.dd_plot.showGrid(x=True, y=True, alpha=0.1)
        self.splitter.addWidget(self.dd_plot)
        
        self.dash_layout.addWidget(self.splitter)
        self.splitter.setSizes([600, 300])
        
        # Section D: Monthly Heatmap
        self.heatmap_label = QLabel("MONTHLY RETURNS (%)")
        self.heatmap_label.setStyleSheet(f"color: #d1d4dc; font-weight: bold; font-size: {int(14 * self.scale_factor)}px;")
        self.dash_layout.addWidget(self.heatmap_label)
        
        self.heatmap_table = QTableWidget()
        self.heatmap_table.setStyleSheet("""
            QTableWidget { background-color: #131722; color: #d1d4dc; border: 1px solid #363c4e; gridline-color: #2a2e39; }
            QHeaderView::section { background-color: #1e222d; color: #d1d4dc; padding: 5px; border: 1px solid #363c4e; }
        """)
        self.heatmap_table.setFixedHeight(int(450 * self.scale_factor))
        self.dash_layout.addWidget(self.heatmap_table)
        
        scroll.setWidget(self.dash_content)
        main_layout.addWidget(scroll)

        if tickers:
            default_ticker = "^NSEI" if "^NSEI" in tickers else tickers[0]
            self.ticker_selector.setCurrentText(default_ticker)
            self.update_analysis(default_ticker)

    def on_ticker_changed(self, ticker):
        self.update_analysis(ticker)

    def on_period_changed(self, period):
        self.update_analysis(self.ticker_selector.currentText())

    def update_analysis(self, ticker):
        if not ticker: return
        self.current_ticker = ticker
        raw_data = self.dm.get_data(ticker, 'daily')
        if raw_data is None or raw_data.empty: return
        
        # Determine timeframe
        period_str = self.period_selector.currentText()
        if period_str == 'Max':
            years = 'max'
        else:
            years = int(period_str.split()[0])
            
        # Check actual history
        first_date = raw_data.index[0]
        last_date = raw_data.index[-1]
        available_years = (last_date - first_date).days / 365.25
        
        if years != 'max' and available_years < years:
            self.info_label.setText(f"Warning: Stock only has {available_years:.1f} years of history. Showing MAX history.")
            data = raw_data
            display_period = "MAX HISTORY"
        else:
            self.info_label.setText(f"Analytics for last {period_str}")
            data = MetricsCalculator.filter_data_by_years(raw_data, years)
            display_period = f"LAST {years}Y" if years != 'max' else "MAX HISTORY"

        metrics = MetricsCalculator.calculate_metrics(data)
        if not metrics: return
        
        # A. Update Cards
        while self.cards_layout.count():
            child = self.cards_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
            
        self.cards_layout.addWidget(MetricCard(f"CAGR ({display_period})", metrics['cagr'], is_percent=True, scale_factor=self.scale_factor))
        self.cards_layout.addWidget(MetricCard(f"ANN. VOLATILITY", metrics['volatility'], is_percent=True, scale_factor=self.scale_factor))
        self.cards_layout.addWidget(MetricCard("SHARPE RATIO", metrics['sharpe_ratio'], scale_factor=self.scale_factor))
        self.cards_layout.addWidget(MetricCard("MAX DRAWDOWN", metrics['max_drawdown'], is_percent=True, scale_factor=self.scale_factor))
        
        # B. Update Plots
        self.ret_plot.clear()
        self.dd_plot.clear()
        
        cum_ret = (1 + metrics['returns_series']).cumprod() - 1
        self.ret_plot.plot(np.arange(len(cum_ret)), cum_ret.values * 100, pen=pg.mkPen('#2962ff', width=2))
        self.dd_plot.plot(np.arange(len(metrics['drawdown_series'])), metrics['drawdown_series'].values * 100, pen=pg.mkPen('#ff7675', width=1), fillLevel=0, brush=(255, 118, 117, 50))
        
        # C. Update Heatmap
        matrix = MetricsCalculator.get_monthly_returns_matrix(metrics['returns_series'])
        self.heatmap_table.setRowCount(len(matrix))
        self.heatmap_table.setColumnCount(len(matrix.columns))
        self.heatmap_table.setHorizontalHeaderLabels([str(c) for c in matrix.columns])
        self.heatmap_table.setVerticalHeaderLabels([str(r) for r in matrix.index])
        
        for r_idx, (year, row) in enumerate(matrix.iterrows()):
            for c_idx, val in enumerate(row):
                if pd.isna(val):
                    item = QTableWidgetItem("-")
                else:
                    item = QTableWidgetItem(f"{val*100:.1f}%")
                    if val > 0:
                        alpha = min(255, int(val * 2000))
                        item.setBackground(QColor(0, 184, 148, alpha))
                    else:
                        alpha = min(255, int(abs(val) * 2000))
                        item.setBackground(QColor(255, 118, 117, alpha))
                
                item.setTextAlignment(Qt.AlignCenter)
                self.heatmap_table.setItem(r_idx, c_idx, item)
        
        self.heatmap_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    from src.data.data_manager import DataManager
    app = QApplication(sys.argv)
    dm = DataManager()
    view = AnalysisView(dm)
    view.show()
    sys.exit(app.exec())
