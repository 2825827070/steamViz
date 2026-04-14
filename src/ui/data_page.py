from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QTextEdit, QSpinBox, QGridLayout, QFrame,
    QLineEdit
)
from PyQt5.QtCore import Qt
from src.data.crawler import CrawlerThread


# 数据管理页面
class DataPage(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.crawler_thread = None
        self.setAttribute(Qt.WA_StaticContents)
        self.init_ui()
        self.refresh_stats()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(24)
        layout.setContentsMargins(24, 16, 24, 24)

        # 页面标题
        header_layout = QVBoxLayout()
        header_layout.setSpacing(4)
        self.title_label = QLabel("数据管理中心")
        self.title_label.setStyleSheet("color: #fafafa; font-size: 24px; font-weight: bold;")
        header_layout.addWidget(self.title_label)

        subtitle = QLabel("管理 Steam 游戏数据的实时获取与本地维护")
        subtitle.setStyleSheet("color: #71717a; font-size: 13px;")
        header_layout.addWidget(subtitle)
        layout.addLayout(header_layout)

        # 统计卡片
        stats_frame = QFrame()
        stats_grid = QGridLayout(stats_frame)
        stats_grid.setContentsMargins(0, 0, 0, 0)
        stats_grid.setSpacing(12)

        self.stat_cards = {}
        cards_info = [
            ('total_games', '游戏总数', '0', '#3b82f6'),
            ('avg_price', '平均价格', '$0.00', '#10b981'),
            ('avg_positive_rate', '平均好评率', '0%', '#f59e0b'),
            ('total_reviews', '总评论数', '0', '#ef4444'),
        ]

        for i, (key, label, default, color) in enumerate(cards_info):
            card, val_lbl = self._create_stat_card(label, default, color)
            stats_grid.addWidget(card, 0, i)
            self.stat_cards[key] = val_lbl

        layout.addWidget(stats_frame)

        # 控制与日志容器
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)

        # 左侧控制区
        self.control_panel = QFrame()
        self.control_panel.setObjectName("control_panel")
        self.control_panel.setStyleSheet("""
            QFrame#control_panel {
                background-color: #18181b;
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 8px;
            }
        """)
        control_layout = QVBoxLayout(self.control_panel)
        control_layout.setSpacing(20)
        control_layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        self.ctrl_title = QLabel("数据获取控制")
        self.ctrl_title.setStyleSheet("color: #fafafa; font-size: 16px; font-weight: 600;")
        control_layout.addWidget(self.ctrl_title)

        # 模式一：批量获取
        batch_layout = QVBoxLayout()
        batch_layout.setSpacing(10)
        
        lbl_batch = QLabel("模式 A: 批量自动获取")
        lbl_batch.setStyleSheet("color: #3b82f6; font-weight: bold; font-size: 13px;")
        batch_layout.addWidget(lbl_batch)

        self.lbl_count = QLabel("获取目标数量 (每款约 1s):")
        self.lbl_count.setStyleSheet("color: #fafafa;")
        batch_layout.addWidget(self.lbl_count)
        
        self.spin_count = QSpinBox()
        self.spin_count.setRange(10, 10000)
        self.spin_count.setValue(500)
        self.spin_count.setSingleStep(100)
        self.spin_count.setSuffix(" 款游戏")
        batch_layout.addWidget(self.spin_count)
        
        self.btn_start = QPushButton("开始批量获取")
        self.btn_start.setObjectName('btn_success')
        self.btn_start.setCursor(Qt.PointingHandCursor)
        self.btn_start.clicked.connect(self.start_batch_fetch)
        batch_layout.addWidget(self.btn_start)
        
        control_layout.addLayout(batch_layout)

        # 分割线
        line1 = QFrame()
        line1.setFrameShape(QFrame.HLine)
        line1.setStyleSheet("background-color: rgba(255, 255, 255, 0.05);")
        control_layout.addWidget(line1)

        # 模式二：按名搜索
        search_layout = QVBoxLayout()
        search_layout.setSpacing(10)
        
        lbl_search_title = QLabel("模式 B: 按游戏名搜索获取")
        lbl_search_title.setStyleSheet("color: #10b981; font-weight: bold; font-size: 13px;")
        search_layout.addWidget(lbl_search_title)

        self.edit_search = QLineEdit()
        self.edit_search.setPlaceholderText("输入游戏名称，如: Cyberpunk 2077")
        search_layout.addWidget(self.edit_search)
        
        self.btn_search_fetch = QPushButton("搜索并同步数据")
        self.btn_search_fetch.setCursor(Qt.PointingHandCursor)
        self.btn_search_fetch.clicked.connect(self.start_search_fetch)
        search_layout.addWidget(self.btn_search_fetch)
        
        control_layout.addLayout(search_layout)

        # 分割线
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setStyleSheet("background-color: rgba(255, 255, 255, 0.05);")
        control_layout.addWidget(line2)

        # 进度与通用控制
        status_layout = QVBoxLayout()
        status_layout.setSpacing(12)
        
        self.btn_stop = QPushButton("停止当前任务")
        self.btn_stop.setObjectName('btn_danger')
        self.btn_stop.setEnabled(False)
        self.btn_stop.setCursor(Qt.PointingHandCursor)
        self.btn_stop.clicked.connect(self.stop_task)
        status_layout.addWidget(self.btn_stop)

        self.progress_label = QLabel("系统就绪")
        self.progress_label.setStyleSheet("color: #a1a1aa; font-size: 13px;")
        status_layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(8)
        status_layout.addWidget(self.progress_bar)
        
        control_layout.addLayout(status_layout)
        control_layout.addStretch()
        
        content_layout.addWidget(self.control_panel, 1)

        # 右侧日志区
        self.log_panel = QFrame()
        self.log_panel.setObjectName("log_panel")
        self.log_panel.setStyleSheet("""
            QFrame#log_panel {
                background-color: #18181b;
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 8px;
            }
        """)
        log_v_layout = QVBoxLayout(self.log_panel)
        log_v_layout.setContentsMargins(20, 20, 20, 20)
        log_v_layout.setSpacing(12)

        self.log_title = QLabel("实时获取日志")
        self.log_title.setStyleSheet("color: #fafafa; font-size: 16px; font-weight: 600;")
        log_v_layout.addWidget(self.log_title)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_v_layout.addWidget(self.log_text)

        content_layout.addWidget(self.log_panel, 2)
        
        layout.addLayout(content_layout, 1)

    # 设置主题
    def set_theme(self, theme_name: str):
        is_dark = theme_name == 'dark'
        fg = "#fafafa" if is_dark else "#18181b"
        bg = "#18181b" if is_dark else "#ffffff"
        border = "rgba(255, 255, 255, 0.05)" if is_dark else "rgba(0, 0, 0, 0.05)"

        self.title_label.setStyleSheet(f"color: {fg}; font-size: 24px; font-weight: bold;")
        self.ctrl_title.setStyleSheet(f"color: {fg}; font-size: 16px; font-weight: 600;")
        self.lbl_count.setStyleSheet(f"color: {fg};")
        self.log_title.setStyleSheet(f"color: {fg}; font-size: 16px; font-weight: 600;")

        self.control_panel.setStyleSheet(f"""
            QFrame#control_panel {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 8px;
            }}
        """)
        self.log_panel.setStyleSheet(f"""
            QFrame#log_panel {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 8px;
            }}
        """)

    # 创建统计卡片
    def _create_stat_card(self, label, value, color):
        card = QFrame()
        card.setFixedHeight(100)
        card.setProperty('class', 'stat-card')
        
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(8)
        card_layout.setContentsMargins(16, 16, 16, 16)

        val_label = QLabel(value)
        val_label.setStyleSheet(f"color: {color}; font-size: 28px; font-weight: bold; background:transparent;")
        val_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(val_label)

        name_label = QLabel(label)
        name_label.setStyleSheet("color: #71717a; font-size: 12px; background:transparent;")
        name_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(name_label)

        return card, val_label

    # 刷新统计数据
    def refresh_stats(self):
        try:
            stats = self.db.get_stats()
            self.stat_cards['total_games'].setText(f"{stats['total_games']:,}")
            self.stat_cards['avg_price'].setText(f"${stats['avg_price']:.2f}")
            self.stat_cards['avg_positive_rate'].setText(f"{stats['avg_positive_rate']}%")
            self.stat_cards['total_reviews'].setText(f"{stats['total_reviews']:,}")
        except Exception as e:
            self.log(f"[ERROR] 刷新统计失败: {e}")

    # 启动批量获取
    def start_batch_fetch(self):
        count = self.spin_count.value()
        self._start_task(target_count=count)
        self.log(f"启动批量获取任务，目标数量: {count}")

    # 启动搜索获取
    def start_search_fetch(self):
        """启动搜索获取"""
        keyword = self.edit_search.text().strip()
        if not keyword:
            self.log("请输入游戏名称后再搜索")
            return
        self._start_task(search_keyword=keyword)
        self.log(f"正在搜索并获取: {keyword}")

    # 通用任务启动逻辑
    def _start_task(self, **kwargs):
        if self.crawler_thread and self.crawler_thread.isRunning():
            return

        self.crawler_thread = CrawlerThread(self.db, **kwargs)
        self.crawler_thread.progress.connect(self.on_progress)
        self.crawler_thread.finished.connect(self.on_finished)
        self.crawler_thread.error.connect(self.on_error)
        self.crawler_thread.game_crawled.connect(self.on_game_crawled)

        self.btn_start.setEnabled(False)
        self.btn_search_fetch.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.progress_bar.setValue(0)
        self.crawler_thread.start()

    # 停止任务
    def stop_task(self):
        if self.crawler_thread:
            self.crawler_thread.stop()
            self.log("正在请求中止任务...")
            self.btn_stop.setEnabled(False)

    # 进度回调
    def on_progress(self, current, total, message):
        if total > 0:
            self.progress_bar.setMaximum(total)
            self.progress_bar.setValue(current)
            self.progress_label.setText(f"[{current}/{total}] {message}")
        else:
            self.progress_label.setText(message)
        self.log(f"正在处理: {message}")

    # 完成回调
    def on_finished(self, success, fail):
        self.btn_start.setEnabled(True)
        self.btn_search_fetch.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.progress_label.setText("任务完成")
        self.log(f"任务结束！成功处理: {success}, 失败: {fail}")
        self.refresh_stats()

    # 错误回调
    def on_error(self, msg):
        self.log(f"错误: {msg}")
        self.btn_start.setEnabled(True)
        self.btn_search_fetch.setEnabled(True)
        self.btn_stop.setEnabled(False)

    # 单个游戏获取完成
    def on_game_crawled(self, game_data):
        if not hasattr(self, '_crawled_count'):
            self._crawled_count = 0
        self._crawled_count += 1
        if self._crawled_count % 5 == 0:
            self.refresh_stats()

    # 写入日志
    def log(self, msg):
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"<span style='color:#52525b'>[{timestamp}]</span> {msg}")
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())

