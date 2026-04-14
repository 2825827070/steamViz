import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib import font_manager
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
import os

font_path = None
for f in font_manager.fontManager.ttflist:
    if 'Microsoft YaHei' in f.name or 'SimHei' in f.name or 'WenQuanYi' in f.name:
        font_path = f.fname
        break

if font_path and os.path.exists(font_path):
    prop = font_manager.FontProperties(fname=font_path)
    matplotlib.rcParams['font.family'] = prop.get_name()
else:
    matplotlib.rcParams['font.family'] = 'sans-serif'

matplotlib.rcParams['axes.unicode_minus'] = False


class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=6, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor='#18181b')
        self.ax = self.fig.add_subplot(111)
        self.fig.patch.set_facecolor('#18181b')
        self.ax.set_facecolor('#18181b')
        self._text_color = '#fafafa'
        super().__init__(self.fig)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def update_theme(self, bg_color='#18181b', text_color='#fafafa'):
        self._text_color = text_color
        self.fig.patch.set_facecolor(bg_color)
        self.ax.set_facecolor(bg_color)
        self.ax.spines['bottom'].set_color(text_color)
        self.ax.spines['left'].set_color(text_color)
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.tick_params(colors=text_color, labelcolor=text_color)
        self.ax.xaxis.label.set_color(text_color)
        self.ax.yaxis.label.set_color(text_color)
        self.ax.title.set_color(text_color)
        self.ax.set_xlabel(self.ax.get_xlabel(), color=text_color)
        self.ax.set_ylabel(self.ax.get_ylabel(), color=text_color)
        self.ax.grid(alpha=0.3, linestyle='--', linewidth=0.5, color=text_color)
        for label in self.ax.get_xticklabels():
            label.set_color(text_color)
        for label in self.ax.get_yticklabels():
            label.set_color(text_color)


class MatplotlibWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._dark = True
        self._text_color = '#fafafa'
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.canvas = MplCanvas(width=5, height=4, dpi=100)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

    def set_theme(self, is_dark):
        self._dark = is_dark
        if is_dark:
            self._text_color = '#fafafa'
            self.canvas.update_theme('#18181b', '#fafafa')
        else:
            self._text_color = '#18181b'
            self.canvas.update_theme('#ffffff', '#18181b')
        self.canvas.draw()

    def clear(self):
        self.canvas.ax.clear()
        self.canvas.ax.set_facecolor('#18181b' if self._dark else '#ffffff')
        self.canvas.draw()

    def draw_bar(self, x_data, y_data, title='', xlabel='', ylabel='', color='#60a5fa'):
        self.clear()
        ax = self.canvas.ax
        tc = self._text_color
        ax.bar(x_data, y_data, color=color, edgecolor='none', linewidth=0)
        if title:
            ax.set_title(title, fontsize=12, fontweight='bold', pad=10, color=tc)
        if xlabel:
            ax.set_xlabel(xlabel, fontsize=10, color=tc)
        if ylabel:
            ax.set_ylabel(ylabel, fontsize=10, color=tc)
        ax.tick_params(axis='x', rotation=45, labelsize=9, colors=tc)
        ax.tick_params(axis='y', labelsize=9, colors=tc)
        for label in ax.get_xticklabels():
            label.set_color(tc)
        for label in ax.get_yticklabels():
            label.set_color(tc)
        ax.grid(alpha=0.3, linestyle='--', linewidth=0.5, color=tc)
        self.canvas.draw()

    def draw_pie(self, labels, sizes, title='', colors=None, explode_idx=None):
        self.clear()
        ax = self.canvas.ax
        tc = self._text_color
        explode = [0.05 if explode_idx == i else 0 for i in range(len(sizes))]
        if colors is None:
            colors = ['#60a5fa', '#34d399', '#fbbf24', '#f87171', '#a78bfa', '#fb923c'][:len(sizes)]
        _, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors,
                                          explode=explode, startangle=90, textprops={'fontsize': 9, 'color': tc})
        for t in texts:
            t.set_color(tc)
        for at in autotexts:
            at.set_color('#18181b' if self._dark else '#ffffff')
        if title:
            ax.set_title(title, fontsize=12, fontweight='bold', pad=15, color=tc)
        self.canvas.draw()

    def draw_line(self, x_data, y_data, title='', xlabel='', ylabel='', color='#60a5fa', fill=True):
        self.clear()
        ax = self.canvas.ax
        tc = self._text_color
        ax.plot(x_data, y_data, color=color, linewidth=2, marker='o', markersize=3)
        if fill:
            ax.fill_between(x_data, y_data, alpha=0.3, color=color)
        if title:
            ax.set_title(title, fontsize=12, fontweight='bold', pad=10, color=tc)
        if xlabel:
            ax.set_xlabel(xlabel, fontsize=10, color=tc)
        if ylabel:
            ax.set_ylabel(ylabel, fontsize=10, color=tc)
        ax.tick_params(axis='x', rotation=45, labelsize=9, colors=tc)
        ax.tick_params(axis='y', labelsize=9, colors=tc)
        for label in ax.get_xticklabels():
            label.set_color(tc)
        for label in ax.get_yticklabels():
            label.set_color(tc)
        ax.grid(alpha=0.3, linestyle='--', linewidth=0.5, color=tc)
        self.canvas.draw()
