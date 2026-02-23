import pyqtgraph as pg
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QComboBox, 
                             QPushButton, QLabel, QFrame, QListWidget, QMenu)
from PySide6.QtCore import Qt, QPointF
import pandas as pd
import numpy as np
from datetime import datetime

class DateAxisItem(pg.AxisItem):
    def __init__(self, dates, scale_factor, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dates = dates
        self.setTickFont(pg.QtGui.QFont("Arial", int(10 * scale_factor)))

    def tickStrings(self, values, scale, spacing):
        strings = []
        for v in values:
            idx = int(v)
            if 0 <= idx < len(self.dates):
                strings.append(self.dates[idx].strftime('%d %b %y'))
            else:
                strings.append("")
        return strings

class CandlestickItem(pg.GraphicsObject):
    def __init__(self, data, scale_factor):
        pg.GraphicsObject.__init__(self)
        self.data = data
        self.scale_factor = scale_factor
        self.picture = None
        self.generatePicture()

    def generatePicture(self):
        self.picture = pg.QtGui.QPicture()
        p = pg.QtGui.QPainter(self.picture)
        width = 0.7
        pen_w = max(1, 0.8 * self.scale_factor)
        for i, (idx, row) in enumerate(self.data.iterrows()):
            open_p, close_p = row['open'], row['close']
            high_p, low_p = row['high'], row['low']
            color = pg.mkColor(0, 184, 148) if close_p >= open_p else pg.mkColor(255, 118, 117)
            p.setPen(pg.mkPen(color, width=pen_w))
            p.setBrush(pg.mkBrush(color))
            p.drawLine(QPointF(i, low_p), QPointF(i, high_p))
            p.drawRect(pg.QtCore.QRectF(i - width/2, open_p, width, close_p - open_p))
        p.end()

    def paint(self, p, *args):
        if self.picture: p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return pg.QtCore.QRectF(self.picture.boundingRect()) if self.picture else pg.QtCore.QRectF()

class ChartView(QWidget):
    def __init__(self, data_manager):
        super().__init__()
        self.dm = data_manager
        self.current_ticker = None
        self.current_timeframe = 'weekly'
        self.data = None
        self.active_studies = {'SMA 8', 'SMA 20', 'SMA 50'} 
        self.scale_factor = 1.2
        
        self.p1 = None
        self.p2 = None
        self.vLine = None
        self.hLine = None
        
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Watchlist
        self.watchlist = QListWidget()
        self.watchlist.setFixedWidth(int(220 * self.scale_factor))
        self.watchlist.setStyleSheet(f"""
            QListWidget {{ background-color: #1e222d; color: #d1d4dc; border: none; font-size: {int(13 * self.scale_factor)}px; }}
            QListWidget::item {{ padding: {int(12 * self.scale_factor)}px; border-bottom: 1px solid #2a2e39; }}
            QListWidget::item:selected {{ background-color: #2a2e39; color: #2962ff; border-left: {int(4 * self.scale_factor)}px solid #2962ff; }}
        """)
        tickers = self.dm.get_all_tickers()
        self.watchlist.addItems(tickers)
        self.watchlist.currentTextChanged.connect(self.update_chart)
        
        # 2. Chart Area
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        toolbar = QFrame()
        toolbar.setFixedHeight(int(55 * self.scale_factor))
        toolbar.setStyleSheet("background-color: #1e222d; border-bottom: 1px solid #363c4e;")
        t_layout = QHBoxLayout(toolbar)
        
        self.ticker_label = QLabel("SYMBOL")
        self.ticker_label.setStyleSheet(f"color: #d1d4dc; font-weight: bold; font-size: {int(18 * self.scale_factor)}px;")
        
        self.tf_selector = QComboBox()
        self.tf_selector.addItems(['Daily', 'Weekly', 'Monthly'])
        self.tf_selector.setCurrentText('Weekly')
        self.tf_selector.setStyleSheet(f"QComboBox {{ font-size: {int(13 * self.scale_factor)}px; padding: 5px; }}")
        self.tf_selector.currentTextChanged.connect(self.change_timeframe)
        
        self.studies_btn = QPushButton("Studies ▼")
        self.studies_btn.setMenu(self.create_studies_menu())
        self.studies_btn.setStyleSheet(f"background-color: #2962ff; color: white; padding: 6px 15px; border-radius: 4px; font-size: {int(13 * self.scale_factor)}px;")

        self.legend = QLabel("O: - H: - L: - C: -")
        self.legend.setStyleSheet(f"color: #d1d4dc; font-family: monospace; font-size: {int(14 * self.scale_factor)}px;")
        
        t_layout.addWidget(self.ticker_label)
        t_layout.addWidget(self.tf_selector)
        t_layout.addWidget(self.studies_btn)
        t_layout.addStretch()
        t_layout.addWidget(self.legend)
        layout.addWidget(toolbar)

        self.win = pg.GraphicsLayoutWidget()
        self.win.setBackground('#131722')
        layout.addWidget(self.win)
        
        self.study_legend_label = QLabel(self.win)
        self.study_legend_label.setStyleSheet(f"background-color: rgba(30, 34, 45, 180); color: #d1d4dc; padding: 8px; font-size: {int(12 * self.scale_factor)}px; border-radius: 4px;")
        self.study_legend_label.move(20, 20)
        self.study_legend_label.setAttribute(Qt.WA_TransparentForMouseEvents)

        main_layout.addWidget(self.watchlist)
        main_layout.addWidget(container)

        default_ticker = "^NSEI" if "^NSEI" in tickers else (tickers[0] if tickers else None)
        if default_ticker:
            items = self.watchlist.findItems(default_ticker, Qt.MatchExactly)
            if items: self.watchlist.setCurrentItem(items[0])
            else: self.watchlist.setCurrentRow(0)

    def create_studies_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet(f"QMenu {{ font-size: {int(12 * self.scale_factor)}px; }}")
        for s in ['SMA 8', 'SMA 20', 'SMA 50', 'SMA 100', 'SMA 200', 'Clear All']:
            action = menu.addAction(s)
            action.triggered.connect(lambda checked=False, name=s: self.toggle_study(name))
        return menu

    def toggle_study(self, name):
        if name == 'Clear All': self.active_studies.clear()
        else:
            if name in self.active_studies: self.active_studies.remove(name)
            else: self.active_studies.add(name)
        self.update_chart(self.current_ticker)

    def change_timeframe(self, tf):
        self.current_timeframe = tf.lower()
        self.update_chart(self.current_ticker)

    def update_y_range(self):
        if self.data is None or self.data.empty or self.p1 is None: return
        vb = self.p1.vb
        rect = vb.viewRect()
        idx_min = max(0, int(rect.left()))
        idx_max = min(len(self.data), int(rect.right()) + 1)
        if idx_min >= idx_max: return
        visible_data = self.data.iloc[idx_min:idx_max]
        if visible_data.empty: return
        v_min, v_max = visible_data['low'].min(), visible_data['high'].max()
        if np.isnan(v_min) or np.isnan(v_max): return
        padding = (v_max - v_min) * 0.05
        if padding == 0: padding = v_max * 0.01
        self.p1.setYRange(v_min - padding, v_max + padding, padding=0)

    def update_chart(self, ticker):
        if not ticker: return
        self.current_ticker = ticker
        self.ticker_label.setText(ticker)
        self.data = self.dm.get_data(ticker, self.current_timeframe)
        if self.data is None or self.data.empty: return

        self.win.ci.clear()
        
        # P1: Price Plot (Top)
        self.p1 = self.win.addPlot(row=0, col=0)
        # P2: Volume Plot with Date Axis (Bottom)
        axis = DateAxisItem(self.data.index, scale_factor=self.scale_factor, orientation='bottom')
        self.p2 = self.win.addPlot(row=1, col=0, axisItems={'bottom': axis})
        
        self.p2.setXLink(self.p1)
        self.p1.hideAxis('bottom') # Hide P1 bottom axis, let P2 show the dates
        self.win.ci.layout.setRowStretchFactor(0, 4)
        self.win.ci.layout.setRowStretchFactor(1, 1)

        pen_grid = pg.mkPen(color='#363c4e', width=1)
        for p in [self.p1, self.p2]:
            p.showGrid(x=True, y=True, alpha=0.1)
            p.getAxis('left').setTextPen('#d1d4dc')
            p.getAxis('bottom').setTextPen('#d1d4dc')
            p.getAxis('left').setPen(pen_grid)

        self.p1.addItem(CandlestickItem(self.data, self.scale_factor))
        v_colors = [(0, 184, 148, 120) if r['close'] >= r['open'] else (255, 118, 117, 120) for _, r in self.data.iterrows()]
        self.p2.addItem(pg.BarGraphItem(x=np.arange(len(self.data)), height=self.data['volume'], width=0.6, brushes=v_colors))

        # Studies
        legend_items = []
        colors = {8: '#00d2d3', 20: '#f1c40f', 50: '#ff9f43', 100: '#54a0ff', 200: '#ee5253'}
        sorted_studies = sorted(list(self.active_studies), key=lambda x: int(x.split()[1]) if len(x.split()) > 1 else 0)
        for s in sorted_studies:
            try:
                period = int(s.split()[1])
                vals = self.data['close'].rolling(window=period).mean()
                color = colors.get(period, '#ffffff')
                y_vals, x_vals = vals.values, np.arange(len(self.data))
                mask = ~np.isnan(y_vals)
                self.p1.plot(x_vals[mask], y_vals[mask], pen=pg.mkPen(color, width=max(1.5, 1.2*self.scale_factor)))
                legend_items.append(f"<span style='color:{color}'>{s}</span>")
            except: continue

        if legend_items:
            self.study_legend_label.setText(" • ".join(legend_items))
            self.study_legend_label.show()
            self.study_legend_label.raise_()
            self.study_legend_label.adjustSize()
        else: self.study_legend_label.hide()

        total_len = len(self.data)
        zoom_range = 200
        if total_len > zoom_range: self.p1.setXRange(total_len - zoom_range, total_len, padding=0)
        else: self.p1.autoRange()

        self.p1.sigXRangeChanged.connect(self.update_y_range)
        self.update_y_range()

        ch_pen = pg.mkPen('#787b86', width=max(1, 0.8 * self.scale_factor), style=Qt.DashLine)
        self.vLine = pg.InfiniteLine(angle=90, movable=False, pen=ch_pen)
        self.hLine = pg.InfiniteLine(angle=0, movable=False, pen=ch_pen)
        self.p1.addItem(self.vLine, ignoreBounds=True)
        self.p1.addItem(self.hLine, ignoreBounds=True)
        self.proxy = pg.SignalProxy(self.p1.scene().sigMouseMoved, rateLimit=60, slot=self.mouseMoved)

    def mouseMoved(self, evt):
        pos = evt[0]
        if self.p1 and self.p1.sceneBoundingRect().contains(pos):
            mousePoint = self.p1.vb.mapSceneToView(pos)
            index = int(mousePoint.x())
            if self.data is not None and 0 <= index < len(self.data):
                row = self.data.iloc[index]
                self.vLine.setPos(mousePoint.x())
                self.hLine.setPos(mousePoint.y())
                date_str = self.data.index[index].strftime('%Y-%m-%d')
                color = "#00b894" if row['close'] >= row['open'] else "#ff7675"
                self.legend.setText(f"<span style='color:#787b86'>{date_str}</span> | O: <span style='color:{color}'>{row['open']:.2f}</span> H: <span style='color:{color}'>{row['high']:.2f}</span> L: <span style='color:{color}'>{row['low']:.2f}</span> C: <span style='color:{color}'>{row['close']:.2f}</span>")

if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    from src.data.data_manager import DataManager
    app = QApplication(sys.argv)
    dm = DataManager()
    view = ChartView(dm)
    view.show()
    sys.exit(app.exec())
