from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QComboBox, 
                             QPushButton, QLabel, QFrame, QTableWidget, QTableWidgetItem, QHeaderView)
from PySide6.QtCore import Qt
import pyqtgraph as pg
from src.engine.backtest_engine import BacktestEngine
from src.strategies.sma_strategy import SMAStackStrategy

class BacktestView(QWidget):
    def __init__(self, data_manager):
        super().__init__()
        self.dm = data_manager
        self.engine = BacktestEngine(initial_capital=100000)
        self.strategy = SMAStackStrategy()
        
        # Scaling Factor (Consistent with ChartView)
        self.scale_factor = 1.2
        
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # 1. Configuration Bar
        config_bar = QFrame()
        config_bar.setStyleSheet("background-color: #1e222d; border-radius: 8px;")
        config_layout = QHBoxLayout(config_bar)
        
        self.ticker_selector = QComboBox()
        self.ticker_selector.addItems(self.dm.get_all_tickers())
        self.ticker_selector.setFixedWidth(200)
        
        self.tf_selector = QComboBox()
        self.tf_selector.addItems(['Daily', 'Weekly', 'Monthly'])
        
        self.run_btn = QPushButton("Run Backtest")
        self.run_btn.setStyleSheet("background-color: #2962ff; color: white; padding: 10px 20px; font-weight: bold;")
        self.run_btn.clicked.connect(self.run_backtest)
        
        config_layout.addWidget(QLabel("Ticker:"))
        config_layout.addWidget(self.ticker_selector)
        config_layout.addWidget(QLabel("Timeframe:"))
        config_layout.addWidget(self.tf_selector)
        config_layout.addStretch()
        config_layout.addWidget(self.run_btn)
        
        layout.addWidget(config_bar)

        # 2. Results Dashboard
        dash_layout = QHBoxLayout()
        
        # Stats Table
        self.stats_label = QLabel("Run a backtest to see results...")
        self.stats_label.setStyleSheet(f"font-size: {int(16 * self.scale_factor)}px; color: #d1d4dc;")
        dash_layout.addWidget(self.stats_label)
        
        # Equity Curve Plot
        self.equity_plot = pg.PlotWidget()
        self.equity_plot.setBackground('#131722')
        self.equity_plot.showGrid(x=True, y=True, alpha=0.1)
        self.equity_plot.getAxis('left').setLabel('Portfolio Value (INR)')
        dash_layout.addWidget(self.equity_plot)
        
        layout.addLayout(dash_layout)

        # 3. Trade List Table
        self.trade_table = QTableWidget()
        self.trade_table.setColumnCount(5)
        self.trade_table.setHorizontalHeaderLabels(['Date', 'Type', 'Price', 'Units', 'Costs'])
        self.trade_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.trade_table.setStyleSheet("""
            QTableWidget { background-color: #1e222d; color: #d1d4dc; gridline-color: #2a2e39; }
            QHeaderView::section { background-color: #2a2e39; color: #d1d4dc; padding: 5px; }
        """)
        layout.addWidget(self.trade_table)

    def run_backtest(self):
        ticker = self.ticker_selector.currentText()
        tf = self.tf_selector.currentText().lower()
        
        data = self.dm.get_data(ticker, tf)
        if data is None or data.empty:
            return

        # Generate Signals
        signals = self.strategy.generate_signals(data)
        
        # Run Engine
        results = self.engine.run(data, signals)
        
        # Update Dashboard
        self.update_ui_with_results(results)

    def update_ui_with_results(self, results):
        # Update Stats Text
        ret_color = "#00b894" if results['total_return_pct'] >= 0 else "#ff7675"
        self.stats_label.setText(f"""
            <div style='line-height: 1.5;'>
                <b style='font-size: 20px;'>Summary</b><br>
                Total Return: <span style='color:{ret_color}'>{results['total_return_pct']:.2f}%</span><br>
                Max Drawdown: <span style='color:#ff7675'>{results['max_drawdown_pct']:.2f}%</span><br>
                Final Value: ₹{results['final_value']:.2f}<br>
                Total Trades: {results['total_trades']}
            </div>
        """)
        
        # Update Equity Curve
        self.equity_plot.clear()
        self.equity_plot.plot(results['equity_curve'], pen=pg.mkPen('#2962ff', width=2))
        
        # Update Trade Table
        self.trade_table.setRowCount(0)
        for trade in self.engine.trades:
            row_pos = self.trade_table.rowCount()
            self.trade_table.insertRow(row_pos)
            
            self.trade_table.setItem(row_pos, 0, QTableWidgetItem(trade['date'].strftime('%Y-%m-%d')))
            self.trade_table.setItem(row_pos, 1, QTableWidgetItem(trade['type']))
            self.trade_table.setItem(row_pos, 2, QTableWidgetItem(f"{trade['price']:.2f}"))
            self.trade_table.setItem(row_pos, 3, QTableWidgetItem(str(trade['units'])))
            self.trade_table.setItem(row_pos, 4, QTableWidgetItem(f"{trade['costs']:.2f}"))
            
            # Color coding trade type
            color = "#00b894" if trade['type'] == 'BUY' else "#ff7675"
            self.trade_table.item(row_pos, 1).setForeground(pg.mkColor(color))
