import sys
import ctypes
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QLabel, QFrame,
    QPushButton, QTreeWidget, QTreeWidgetItem
)
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QIcon
import os

from src.data.database import SteamDatabase
from src.ui.styles import DARK_THEME, LIGHT_THEME
from src.ui.visual_hub import VisualHubPage, DataListPage, ReviewListPage
from src.ui.data_page import DataPage


# 主窗口
class MainWindow(QMainWindow):
    PAGE_CONFIG = [
        ('数据概览', 'visual', 'dashboard', []),
        ('游戏列表', 'native', 'data_list', []),
        ('用户评价', 'native', 'review_list', []),
        ('数据管理', 'native', 'data', []),
    ]

    def __init__(self):
        super().__init__()
        self.db = SteamDatabase()
        self._current_theme = 'dark'  # 记录当前主题，默认为暗色系

        # 设置窗口图标
        if getattr(sys, 'frozen', False):
            base_dir = sys._MEIPASS
        else:
            base_dir = os.getcwd()
        icon_path = os.path.join(base_dir, 'icon', 'icon.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # 保留 Windows 原生边框样式，用 WM_NCCALCSIZE 隐藏其视觉，让 Aero Snap/双击最大化全部正常，优化windows操作体验
        self.setWindowFlags(Qt.Window | Qt.WindowSystemMenuHint | Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint)

        self.setWindowTitle("Steam 数据分析器")
        self.setMinimumSize(1000, 640)
        self.resize(1400, 880)
        self.setStyleSheet(DARK_THEME)
        self.setAttribute(Qt.WA_StaticContents)  # 优化缩放稳定性

        self._build_ui()  # 构建主页面
        self._setup_hidden_frame()  # 设置隐藏框架

        def _init_nav():
            first_item = self.nav_tree.topLevelItem(0)
            if first_item:
                self.nav_tree.setCurrentItem(first_item)
                self._on_nav_clicked(first_item, 0)
        QTimer.singleShot(100, _init_nav)

    # 无边框支持
    def _setup_hidden_frame(self):
        if sys.platform != 'win32':
            return 
        try:
            import ctypes.wintypes
            hwnd = int(self.winId())  # 获取PyQt的windows句柄，用于后续调用windows api

            # 1. 将 DWM 在阴影层内扩展整个客户区
            class MARGINS(ctypes.Structure):
                _fields_ = [('l', ctypes.c_int), ('r', ctypes.c_int),
                             ('t', ctypes.c_int), ('b', ctypes.c_int)]
            m = MARGINS(-1, -1, -1, -1)  # -1 = extend in all directions
            ctypes.windll.dwmapi.DwmExtendFrameIntoClientArea(hwnd, ctypes.byref(m))

            # 2. 刷新窗口帧，使 DWM 更改生效
            ctypes.windll.user32.SetWindowPos(
                hwnd, None, 0, 0, 0, 0,
                0x0002 | 0x0001 | 0x0020 | 0x0040  # SWP_NOMOVE|SWP_NOSIZE|SWP_FRAMECHANGED|SWP_NOOWNERZORDER
            )
        except Exception as e:
            print(f'[DWM] setup failed: {e}')

    # 拦截windows消息，返回 bool, int，前者True表示消息已处理，False表示继续传递
    def nativeEvent(self, eventType, message):
        retval, result = super().nativeEvent(eventType, message)
        if sys.platform != 'win32' or eventType != b'windows_generic_MSG':
            return retval, result
        try:
            WM_ERASEBKGND      = 0x0014
            WM_SIZING          = 0x0214   # 模态 resize 循环中持续发送
            WM_NCCALCSIZE      = 0x0083
            WM_NCHITTEST       = 0x0084
            WM_NCLBUTTONDBLCLK = 0x00A3

            HTCAPTION = 2
            HTLEFT, HTRIGHT = 10, 11
            HTTOP, HTTOPLEFT, HTTOPRIGHT = 12, 13, 14
            HTBOTTOM, HTBOTTOMLEFT, HTBOTTOMRIGHT = 15, 16, 17

            class MSG(ctypes.Structure):
                _fields_ = [
                    ('hWnd',    ctypes.c_void_p),   # 窗口句柄
                    ('message', ctypes.c_uint),     # 消息类型
                    ('wParam',  ctypes.c_size_t),   # 附加信息1
                    ('lParam',  ctypes.c_size_t),   # 附加信息2
                    ('time',    ctypes.c_uint),     # 消息产生时间
                    ('pt_x',    ctypes.c_long),     # 鼠标 X 坐标
                    ('pt_y',    ctypes.c_long),     # 鼠标 Y 坐标
                ]

            msg = ctypes.cast(int(message), ctypes.POINTER(MSG)).contents

            # 禁止背景擦除，并确保不进入后续 Qt 逻辑
            if msg.message == WM_ERASEBKGND:
                return True, 1

            # WM_SIZING 在 Windows 模态拖动循环中持续发送
            if msg.message == WM_SIZING:
                return retval, result  # 不拦截，让 Qt 继续处理

            # WM_NCCALCSIZE 返回 0 → 客户区覆盖整个窗口（隐藏原生标题栏）
            if msg.message == WM_NCCALCSIZE and msg.wParam:
                return True, 0

            # 双击标题栏最大化 / 还原
            if msg.message == WM_NCLBUTTONDBLCLK and msg.wParam == HTCAPTION:
                self._toggle_maximize()
                return True, 0

            if msg.message == WM_NCHITTEST:
                # 获取屏幕 DPI 缩放比，转换物理像素为逻辑像素
                dpr = self.devicePixelRatioF()
                pos = self.mapFromGlobal(QPoint(int(msg.pt_x / dpr), int(msg.pt_y / dpr)))
                px, py = pos.x(), pos.y()
                w, h = self.width(), self.height()

                # 排除主题切换按钮区域 (46x36，紧邻侧边栏右侧)
                # 侧边栏宽度 210，按钮宽 46
                if 210 <= px < 256 and py < 36:
                    return False, 0  # 让 Qt 正常处理按钮点击

                if self.isMaximized():
                    if (px < 210 and py < 95) or (py < 36 and px < w - 145):
                        return True, HTCAPTION
                    return retval, result

                edge = 8

                if py < edge:
                    if px < edge:     return True, HTTOPLEFT
                    if px > w - edge: return True, HTTOPRIGHT
                    return True, HTTOP
                if py > h - edge:
                    if px < edge:     return True, HTBOTTOMLEFT
                    if px > w - edge: return True, HTBOTTOMRIGHT
                    return True, HTBOTTOM
                if px < edge:         return True, HTLEFT
                if px > w - edge:     return True, HTRIGHT

                if (px < 210 and py < 95) or (py < 36 and px < w - 145):
                    return True, HTCAPTION
        except:
            pass
        return retval, result

    def _toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def resizeEvent(self, event):
        # WM_SIZING 已经处理拖动期间的 resize。这里主要处理非拖动情况（如窗口最大化/还原）
        super().resizeEvent(event)


    # 构建 UI
    def _build_ui(self):
        central = QWidget()
        central.setObjectName('main_central_widget')
        central.setAttribute(Qt.WA_StaticContents)  # 静态内容保护，减少缩放闪烁
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 侧边栏 ─ 固定宽度，resize 时只纵向伸缩
        sidebar = QFrame()
        sidebar.setObjectName('sidebar')
        sidebar.setFixedWidth(210)  # 锁死横向宽度，消除拖动时侧边栏的无效重绘
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        # Logo 区
        logo_frame = QFrame()
        logo_frame.setObjectName('logo_frame')
        logo_frame.setFixedHeight(95)
        logo_layout = QVBoxLayout(logo_frame)
        logo_layout.setContentsMargins(16, 16, 12, 8)
        logo_layout.setSpacing(2)

        self.logo_title = QLabel("STEAM")
        self.logo_title.setStyleSheet(
            "color: #3b82f6; font-size: 22px; font-weight: 800;"
            " letter-spacing: 4px; background: transparent;"
        )
        self.logo_title.setAttribute(Qt.WA_TransparentForMouseEvents)
        logo_layout.addWidget(self.logo_title)

        self.logo_subtitle = QLabel("全景数据工作站")
        self.logo_subtitle.setStyleSheet("color: #48484a; font-size: 11px; background: transparent;")
        self.logo_subtitle.setAttribute(Qt.WA_TransparentForMouseEvents)
        logo_layout.addWidget(self.logo_subtitle)

        sidebar_layout.addWidget(logo_frame)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: rgba(255,255,255,0.06);")
        sidebar_layout.addWidget(sep)

        # 导航树
        self.nav_tree = QTreeWidget()
        self.nav_tree.setObjectName('nav_tree')
        self.nav_tree.setHeaderHidden(True)
        self.nav_tree.setIndentation(16)
        self.nav_tree.setAnimated(True)

        for name, r_type, sub, children in self.PAGE_CONFIG:
            parent = QTreeWidgetItem([name])
            parent.setData(0, Qt.UserRole, (r_type, sub, None))
            for c_name, c_id in children:
                child = QTreeWidgetItem([c_name])
                child.setData(0, Qt.UserRole, (r_type, sub, c_id))
                parent.addChild(child)
            self.nav_tree.addTopLevelItem(parent)
            if children:
                parent.setExpanded(True)

        self.nav_tree.itemClicked.connect(self._on_nav_clicked)
        sidebar_layout.addWidget(self.nav_tree, 1)

        # 版本号（底部）
        ver = QLabel("0.1.0")
        ver.setStyleSheet("color: #3a3a3c; font-size: 10px; padding: 8px; background: transparent;")
        ver.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(ver)

        main_layout.addWidget(sidebar)

        # 内容区
        content_widget = QWidget()
        content_widget.setObjectName('content_area')
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # 顶部标题栏（含关闭/最大化/最小化）
        self._title_bar = QFrame()
        self._title_bar.setObjectName('title_bar')
        self._title_bar.setFixedHeight(36)
        self._title_bar.setStyleSheet("QFrame#title_bar { background: transparent; border: none; }")
        tb_layout = QHBoxLayout(self._title_bar)
        tb_layout.setContentsMargins(0, 0, 2, 0)
        tb_layout.setSpacing(0)
        tb_layout.addStretch()

        # 改进的窗口控制按钮
        btn_style = (
            "QPushButton {{"
            "  background: transparent; color: #636366;"
            "  border: none; font-size: {fs}px;"
            "  font-family: 'Segoe UI Symbol', 'Arial Unicode MS', sans-serif;"
            "  min-width: {w}px; max-width: {w}px;"
            "  min-height: 36px; max-height: 36px;"
            "  padding: 0; border-radius: 0;"
            "}}"
            "QPushButton:hover {{ background: {hvr}; color: {hc}; }}"
            "QPushButton:pressed {{ background: {prs}; }}"
        )

        self._btn_min = QPushButton("⎯")
        self._btn_min.setFixedSize(46, 36)
        self._btn_min.setStyleSheet(btn_style.format(
            fs=12, w=46,
            hvr="rgba(255,255,255,0.08)", hc="#e5e5ea",
            prs="rgba(255,255,255,0.12)"
        ))
        self._btn_min.setCursor(Qt.ArrowCursor)
        self._btn_min.clicked.connect(self.showMinimized)

        self._btn_max = QPushButton("⬜")
        self._btn_max.setFixedSize(46, 36)
        self._btn_max.setStyleSheet(btn_style.format(
            fs=11, w=46,
            hvr="rgba(255,255,255,0.08)", hc="#e5e5ea",
            prs="rgba(255,255,255,0.12)"
        ))
        self._btn_max.setCursor(Qt.ArrowCursor)
        self._btn_max.clicked.connect(self._toggle_maximize)

        self._btn_close = QPushButton("✕")
        self._btn_close.setFixedSize(46, 36)
        self._btn_close.setStyleSheet(btn_style.format(
            fs=13, w=46,
            hvr="#c0392b", hc="#ffffff",
            prs="#962d22"
        ))
        self._btn_close.setCursor(Qt.ArrowCursor)
        self._btn_close.clicked.connect(self.close)

        # 主题切换按钮
        self.btn_theme = QPushButton("☀")
        self.btn_theme.setFixedSize(46, 36)
        self.btn_theme.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #636366;
                border: none;
                font-size: 16px;
                min-width: 46px;
                max-width: 46px;
                min-height: 36px;
                max-height: 36px;
                border-radius: 0;
            }
            QPushButton:hover {
                background: transparent;
                color: #fafafa;
            }
            QPushButton:pressed {
                background: transparent;
            }
        """)
        self.btn_theme.setCursor(Qt.PointingHandCursor)
        self.btn_theme.clicked.connect(self._switch_theme)

        for b in [self._btn_min, self._btn_max, self._btn_close]:
            tb_layout.addWidget(b)

        tb_layout.insertWidget(0, self.btn_theme)

        content_layout.addWidget(self._title_bar)

        # 页面栈
        self.stack = QStackedWidget()
        self.page_visual_hub = VisualHubPage(self.db)
        self.page_data_list = DataListPage(self.db)
        self.page_review_list = ReviewListPage(self.db)
        self.page_data = DataPage(self.db)

        self.stack.addWidget(self.page_visual_hub)
        self.stack.addWidget(self.page_data_list)
        self.stack.addWidget(self.page_review_list)
        self.stack.addWidget(self.page_data)
        content_layout.addWidget(self.stack, 1)

        # 内置状态栏（不用 QMainWindow.setStatusBar，避免脱离圆角容器）
        self._status_bar = QLabel("系统就绪")
        self._status_bar.setFixedHeight(24)
        self._status_bar.setStyleSheet(
            "background: #131316; color: #48484a; font-size: 11px;"
            " padding: 0 16px; border-top: 1px solid rgba(255,255,255,0.05);"
            " border-bottom-right-radius: 10px;"
        )
        content_layout.addWidget(self._status_bar)

        main_layout.addWidget(content_widget, 1)

    # 导航

    def _on_nav_clicked(self, item, column):
        data = item.data(0, Qt.UserRole)
        if not data:
            return
        r_type, sub, _ = data
        if r_type == 'visual':
            self.stack.setCurrentWidget(self.page_visual_hub)
            self.page_visual_hub.refresh_data()
        elif sub == 'data_list':
            self.stack.setCurrentWidget(self.page_data_list)
            self.page_data_list.refresh_data()
        elif sub == 'review_list':
            self.stack.setCurrentWidget(self.page_review_list)
            self.page_review_list.refresh_data()
        elif sub == 'data':
            self.stack.setCurrentWidget(self.page_data)
            self.page_data.refresh_stats()

    # 切换主题
    def _switch_theme(self):
        if self._current_theme == 'dark':
            self._current_theme = 'light'
            self.setStyleSheet(LIGHT_THEME)
            self.btn_theme.setText("🌙")
            self.logo_subtitle.setStyleSheet("color: #71717a; font-size: 11px; background: transparent;")
            self._status_bar.setStyleSheet(
                "background: #f4f4f5; color: #71717a; font-size: 11px;"
                " padding: 0 16px; border-top: 1px solid rgba(0,0,0,0.05);"
                " border-bottom-right-radius: 10px;"
            )
        else:
            self._current_theme = 'dark'
            self.setStyleSheet(DARK_THEME)
            self.btn_theme.setText("☀")
            self.logo_subtitle.setStyleSheet("color: #48484a; font-size: 11px; background: transparent;")
            self._status_bar.setStyleSheet(
                "background: #131316; color: #48484a; font-size: 11px;"
                " padding: 0 16px; border-top: 1px solid rgba(255,255,255,0.05);"
                " border-bottom-right-radius: 10px;"
            )
            
        # 通知所有堆栈页面
        for i in range(self.stack.count()):
            page = self.stack.widget(i)
            if hasattr(page, 'set_theme'):
                page.set_theme(self._current_theme)


if __name__ == '__main__':
    MainWindow().show()