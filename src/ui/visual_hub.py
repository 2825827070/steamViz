import json
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, QComboBox,
    QPushButton, QMenu, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QColor
from src.charts.matplotlib_widget import MatplotlibWidget


# 仪表盘页面
class VisualHubPage(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self._current_theme = 'dark'
        self.setAttribute(Qt.WA_StaticContents)
        self.init_ui()

    def set_theme(self, theme_name: str):
        self._current_theme = theme_name
        is_dark = theme_name == 'dark'
        
        # 更新标题颜色
        color = "#fafafa" if is_dark else "#18181b"
        self.title_label.setStyleSheet(f"color:{color}; font-size:20px; font-weight:600; padding:4px 0;")
        
        # 更新图表
        for chart in self.charts.values():
            chart.set_theme(is_dark)
            
        # 重新渲染仪表盘以适应新主题
        self._render_dashboard()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 16, 20, 12)

        self.title_label = QLabel("Steam 数据概览")
        self.title_label.setStyleSheet("color:#fafafa; font-size:20px; font-weight:600; padding:4px 0;")
        layout.addWidget(self.title_label)

        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)
        self.card_values = {}
        cards_data = [
            ('total', '游戏总数', '0', '#3b82f6'),
            ('avg_price', '平均价格', '$0', '#10b981'),
            ('avg_rating', '平均好评率', '0%', '#f59e0b'),
            ('reviews', '总评论数', '0', '#ef4444'),
        ]
        for key, label, default, color in cards_data:
            card, val_lbl = self._make_card(label, default, color)
            cards_layout.addWidget(card)
            self.card_values[key] = val_lbl
        layout.addLayout(cards_layout)

        chart_layout = QGridLayout()
        chart_layout.setSpacing(16)
        chart_layout.setRowStretch(0, 1)
        chart_layout.setRowStretch(1, 1)
        chart_layout.setColumnStretch(0, 1)
        chart_layout.setColumnStretch(1, 1)

        self.charts = {}
        chart_ids = ['trend', 'genre', 'price', 'rating']
        positions = [(0, 0), (0, 1), (1, 0), (1, 1)]
        for cid, pos in zip(chart_ids, positions):
            chart = MatplotlibWidget()
            chart.set_theme(True)
            self.charts[cid] = chart
            chart_layout.addWidget(chart, pos[0], pos[1])

        container = QFrame()
        container.setLayout(chart_layout)
        layout.addWidget(container, 1)

    def _make_card(self, label, default, color):
        card = QFrame()
        card.setFixedHeight(80)
        card.setProperty('class', 'stat-card')
        cl = QVBoxLayout(card)
        cl.setContentsMargins(16, 8, 16, 8)
        cl.setSpacing(2)
        v = QLabel(default)
        v.setStyleSheet(f"color:{color}; font-size:26px; font-weight:bold; background:transparent; border:none;")
        cl.addWidget(v)
        l = QLabel(label)
        l.setStyleSheet("color:#71717a; font-size:12px; background:transparent; border:none;")
        cl.addWidget(l)
        return card, v

    def refresh_data(self):
        stats = self.db.get_stats()
        self._animate_counter('total', stats['total_games'], lambda v: f"{int(v):,}")
        self._animate_counter('avg_price', stats['avg_price'], lambda v: f"${v:.2f}")
        self._animate_counter('avg_rating', float(stats['avg_positive_rate']), lambda v: f"{v:.1f}%")
        self._animate_counter('reviews', stats['total_reviews'], lambda v: f"{int(v):,}")

        if self.db.get_game_count() == 0:
            return

        self._render_dashboard()

    def _animate_counter(self, key, target, fmt_fn, steps=30, interval_ms=20):
        def tick(counter=[0]):
            counter[0] += 1
            t = counter[0] / steps
            t_ease = 1 - (1 - t) ** 3
            val = target * t_ease
            label = self.card_values.get(key)
            if label:
                label.setText(fmt_fn(val))
            if counter[0] < steps:
                QTimer.singleShot(interval_ms, lambda: tick(counter))
            else:
                label.setText(fmt_fn(target))
        QTimer.singleShot(interval_ms, lambda: tick())

    def _render_dashboard(self):
        release = self.db.get_release_by_year()
        if release and 'trend' in self.charts:
            self.charts['trend'].draw_line(
                [d['year'] for d in release],
                [d['count'] for d in release],
                title='年度发行趋势',
                xlabel='年份', ylabel='游戏数量',
                color='#60a5fa'
            )

        genres = self.db.get_genre_distribution()
        if genres and 'genre' in self.charts:
            top = genres[:8]
            colors = ['#60a5fa', '#34d399', '#fbbf24', '#f87171', '#a78bfa', '#fb923c', '#2dd4bf', '#e879f9']
            self.charts['genre'].draw_pie(
                [d['name'] for d in top],
                [d['count'] for d in top],
                title='游戏类型分布',
                colors=colors[:len(top)]
            )

        games = self.db.get_all_games()
        if games and 'price' in self.charts:
            pbins = {}
            for g in games:
                if g['is_free'] or g['price_final'] <= 0:
                    continue
                b = min(int(g['price_final'] / 100 / 5) * 5, 100)
                pbins[b] = pbins.get(b, 0) + 1
            sb = sorted(pbins.items())
            if sb:
                self.charts['price'].draw_bar(
                    [f'${b[0]}-{b[0]+5}' for b in sb],
                    [b[1] for b in sb],
                    title='价格分布',
                    xlabel='价格区间', ylabel='游戏数量',
                    color='#60a5fa'
                )

        if 'rating' in self.charts:
            rd = self.db.get_rating_distribution()
            if rd:
                cm = {'好评如潮': '#34d399', '特别好评': '#60a5fa', '多半好评': '#2dd4bf',
                      '褒贬不一': '#fbbf24', '多半差评': '#f87171', '差评如潮': '#ef4444'}
                colors = [cm.get(d['rating_level'], '#60a5fa') for d in rd]
                self.charts['rating'].draw_pie(
                    [d['rating_level'] for d in rd],
                    [d['count'] for d in rd],
                    title='评分等级分布',
                    colors=colors
                )


class DataListPage(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.current_page = 0
        self.page_size = 50
        self.sort_key = 'name'
        self.sort_order = 'asc'
        self.filter_text = ''
        self.filter_rating = '全部'
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 16, 20, 12)

        self.title_label = QLabel("游戏数据库")
        self.title_label.setStyleSheet("color:#fafafa; font-size:20px; font-weight:600; padding:4px 0;")
        layout.addWidget(self.title_label)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(12)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索游戏名称...")
        self.search_input.setFixedWidth(200)
        self.search_input.textChanged.connect(self._on_search)
        toolbar.addWidget(self.search_input)

        self.rating_filter = QComboBox()
        self.rating_filter.addItems(['全部', '好评如潮', '特别好评', '多半好评', '褒贬不一', '多半差评', '差评如潮'])
        self.rating_filter.currentTextChanged.connect(self._on_filter_change)
        toolbar.addWidget(QLabel("评分:"))
        toolbar.addWidget(self.rating_filter)

        toolbar.addStretch()

        self.page_label = QLabel("第 1 页")
        self.page_label.setStyleSheet("color:#71717a; font-size:13px;")
        toolbar.addWidget(self.page_label)

        prev_btn = QPushButton("上一页")
        prev_btn.clicked.connect(self._prev_page)
        toolbar.addWidget(prev_btn)

        next_btn = QPushButton("下一页")
        next_btn.clicked.connect(self._next_page)
        toolbar.addWidget(next_btn)

        layout.addLayout(toolbar)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(['名称', '价格', '好评率', '评论数', '发行年份', '类型', '标签'])
        
        # 优化列宽分配
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        self.table.setColumnWidth(0, 220)  # 名称
        self.table.setColumnWidth(1, 80)   # 价格
        self.table.setColumnWidth(2, 140)  # 好评率
        self.table.setColumnWidth(3, 100)  # 评论数
        self.table.setColumnWidth(4, 80)   # 发行年份
        self.table.setColumnWidth(5, 150)  # 类型
        header.setStretchLastSection(True) # 最后一列自动填充
        
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._on_context_menu)
        self.table.horizontalHeader().sectionClicked.connect(self._on_header_clicked)
        self._update_table_style()
        layout.addWidget(self.table, 1)

    def set_theme(self, theme_name: str):
        self._current_theme = theme_name
        is_dark = theme_name == 'dark'
        color = "#fafafa" if is_dark else "#18181b"
        self.title_label.setStyleSheet(f"color:{color}; font-size:20px; font-weight:600; padding:4px 0;")
        self._update_table_style()

    def _update_table_style(self):
        is_dark = getattr(self, '_current_theme', 'dark') == 'dark'
        bg = "#18181b" if is_dark else "#ffffff"
        fg = "#fafafa" if is_dark else "#18181b"
        h_bg = "#27272a" if is_dark else "#f4f4f5"
        border = "rgba(255,255,255,0.06)" if is_dark else "rgba(0,0,0,0.06)"
        
        self.table.setStyleSheet(f"""
            QTableWidget {{ background-color: {bg}; border: 1px solid {border}; border-radius: 8px; color: {fg}; }}
            QHeaderView::section {{ background-color: {h_bg}; color: #71717a; border: none; border-bottom: 1px solid {border}; padding: 10px; }}
            QTableWidget::item {{ padding: 8px; border-bottom: 1px solid {border.replace('0.06', '0.03')}; }}
            QTableWidget::item:selected {{ background: rgba(59,130,246,0.15); }}
        """)

    def _on_search(self, text):
        self.filter_text = text
        self.current_page = 0
        self.refresh_data()

    def _on_filter_change(self, text):
        self.filter_rating = text
        self.current_page = 0
        self.refresh_data()

    def _prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.refresh_data()

    def _next_page(self):
        self.current_page += 1
        self.refresh_data()

    def _on_header_clicked(self, index):
        keys = ['name', 'price_final', 'ratio', 'total_reviews', 'release_date', 'genres', 'tags']
        if index < len(keys):
            new_key = keys[index]
            if self.sort_key == new_key:
                self.sort_order = 'desc' if self.sort_order == 'asc' else 'asc'
            else:
                self.sort_key = new_key
                # 默认数值型降序，名称型升序
                self.sort_order = 'desc' if index in [1, 2, 3, 4] else 'asc'
            self.refresh_data()

    def _on_context_menu(self, pos: QPoint):
        item = self.table.itemAt(pos)
        if not item:
            return
        
        row = self.table.currentRow()
        game_name = self.table.item(row, 0).text()
        
        # 寻找对应的 appid
        # 因为我们是分页显示的，需要根据当前页和行号找到原始数据
        games = self._get_filtered_games()
        start = self.current_page * self.page_size
        if start + row >= len(games):
            return
            
        game_data = games[start + row]
        appid = game_data.get('appid')

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background-color: #27272a; color: #fafafa; border: 1px solid #3f3f46; border-radius: 4px; padding: 4px; }
            QMenu::item { padding: 6px 24px; border-radius: 2px; }
            QMenu::item:selected { background-color: #3b82f6; }
        """)
        
        view_reviews_action = menu.addAction(f"查看 '{game_name[:15]}...' 的评价")
        del_action = menu.addAction(f"删除游戏")
        
        action = menu.exec_(self.table.viewport().mapToGlobal(pos))
        
        if action == view_reviews_action:
            # 找到主窗口并切换页面
            main_win = self.window()
            if hasattr(main_win, 'page_review_list') and hasattr(main_win, 'stack'):
                main_win.page_review_list.show_game_reviews(game_name)
                main_win.stack.setCurrentWidget(main_win.page_review_list)
                # 同时更新侧边栏选中状态
                if hasattr(main_win, 'nav_tree'):
                    for i in range(main_win.nav_tree.topLevelItemCount()):
                        item = main_win.nav_tree.topLevelItem(i)
                        d = item.data(0, Qt.UserRole)
                        if d and d[2] == 'review_list':
                            main_win.nav_tree.setCurrentItem(item)
                            break

        elif action == del_action:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle('确认删除')
            msg_box.setText(f"确定要删除游戏 '{game_name}' 吗？")
            msg_box.setInformativeText("这将同时删除相关的评论和同步日志。")
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg_box.setDefaultButton(QMessageBox.No)
            msg_box.setIcon(QMessageBox.Question)
            
            # 显式应用样式以确保文字在不同主题下可见
            is_dark = getattr(self, '_current_theme', 'dark') == 'dark'
            bg = "#18181b" if is_dark else "#ffffff"
            fg = "#fafafa" if is_dark else "#18181b"
            msg_box.setStyleSheet(f"""
                QWidget {{ background-color: {bg}; color: {fg}; }}
                QLabel {{ background: transparent; color: {fg}; font-size: 13px; }}
                QPushButton {{ background-color: #3b82f6; color: white; padding: 6px 18px; border-radius: 4px; }}
                QPushButton:hover {{ background-color: #2563eb; }}
            """)
            
            reply = msg_box.exec_()
            
            if reply == QMessageBox.Yes:
                if self.db.delete_game_full(appid):
                    self.refresh_data()
                    # 通知主窗口刷新统计 (如果需要)
                    if self.parent() and hasattr(self.parent(), 'refresh_stats'):
                        self.parent().refresh_stats()

    def refresh_stats(self):
        self.refresh_data()

    def refresh_data(self):
        games = self._get_filtered_games()
        total = len(games)
        total_pages = max(1, (total + self.page_size - 1) // self.page_size)
        if self.current_page >= total_pages:
            self.current_page = total_pages - 1

        self.page_label.setText(f"第 {self.current_page + 1} / {total_pages} 页 共 {total} 条")

        start = self.current_page * self.page_size
        end = min(start + self.page_size, total)
        page_games = games[start:end] if total > 0 else []

        self.table.setRowCount(len(page_games))
        for row, g in enumerate(page_games):
            self.table.setItem(row, 0, QTableWidgetItem(g['name'][:50]))
            price = '免费' if g['is_free'] else f"${g['price_final']/100:.2f}"
            self.table.setItem(row, 1, QTableWidgetItem(price))
            
            total_r = g['total_reviews']
            if total_r > 0:
                ratio = g['ratio']
                rate_str = f"{ratio*100:.1f}%"
                if total_r >= 10:
                    # 重新计算 level 以便展示
                    if ratio >= 0.95: level = '好评如潮'
                    elif ratio >= 0.80: level = '特别好评'
                    elif ratio >= 0.70: level = '多半好评'
                    elif ratio >= 0.40: level = '褒贬不一'
                    elif ratio >= 0.20: level = '多半差评'
                    else: level = '差评如潮'
                    rate_str += f" ({level})"
                else:
                    rate_str += " (评价不足)"
            else:
                rate_str = "N/A"
            
            self.table.setItem(row, 2, QTableWidgetItem(rate_str))
            self.table.setItem(row, 3, QTableWidgetItem(f"{total_r:,}"))
            self.table.setItem(row, 4, QTableWidgetItem(str(g['release_date'])[:4] if g['release_date'] else 'N/A'))
            try:
                genres = json.loads(g['genres']) if isinstance(g['genres'], str) else g['genres']
                genre_str = ', '.join([g if isinstance(g, str) else g.get('description', '') for g in genres[:3]])
            except:
                genre_str = ''
            self.table.setItem(row, 5, QTableWidgetItem(genre_str))

    def _get_filtered_games(self):
        all_games = self.db.get_all_games()
        if not all_games:
            return []

        result = []
        for g in all_games:
            # 预计算一些展示和排序需要的字段
            pos = g.get('positive_reviews', 0)
            neg = g.get('negative_reviews', 0)
            g['total_reviews'] = pos + neg
            g['ratio'] = pos / g['total_reviews'] if g['total_reviews'] > 0 else 0
            
            if self.filter_text and self.filter_text.lower() not in g['name'].lower():
                continue
            
            # 计算实时评分等级
            if g['total_reviews'] < 10:
                level = '评价不足'
            else:
                if g['ratio'] >= 0.95: level = '好评如潮'
                elif g['ratio'] >= 0.80: level = '特别好评'
                elif g['ratio'] >= 0.70: level = '多半好评'
                elif g['ratio'] >= 0.40: level = '褒贬不一'
                elif g['ratio'] >= 0.20: level = '多半差评'
                else: level = '差评如潮'
            
            if self.filter_rating != '全部' and level != self.filter_rating:
                continue
            
            result.append(g)

        reverse = self.sort_order == 'desc'
        # 处理可能的 None 值
        result.sort(key=lambda x: (x.get(self.sort_key) if x.get(self.sort_key) is not None else ""), reverse=reverse)
        return result


# 评价展示页面
class ReviewListPage(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.current_page = 0
        self.page_size = 50
        self.filter_game_name = ""
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 16, 20, 12)

        # 标题
        self.title_label = QLabel("用户评价中心")
        self.title_label.setStyleSheet("color:#fafafa; font-size:20px; font-weight:600;")
        layout.addWidget(self.title_label)

        # 工具栏
        toolbar = QHBoxLayout()
        toolbar.setSpacing(12)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索游戏名称...")
        self.search_input.setFixedWidth(220)
        self.search_input.textChanged.connect(self._on_search_changed)
        toolbar.addWidget(self.search_input)

        toolbar.addStretch()

        self.page_label = QLabel("第 1 页")
        self.page_label.setStyleSheet("color:#71717a; font-size:13px;")
        toolbar.addWidget(self.page_label)

        self.btn_prev = QPushButton("上一页")
        self.btn_prev.clicked.connect(self._prev_page)
        toolbar.addWidget(self.btn_prev)

        self.btn_next = QPushButton("下一页")
        self.btn_next.clicked.connect(self._next_page)
        toolbar.addWidget(self.btn_next)

        layout.addLayout(toolbar)

        # 表格
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(['所属游戏', '评价内容', '是否推荐', '时长 (分钟)', '发布时间'])
        
        h = self.table.horizontalHeader()
        h.setSectionResizeMode(QHeaderView.Interactive)
        self.table.setColumnWidth(0, 150) # 游戏名
        self.table.setColumnWidth(1, 400) # 内容
        self.table.setColumnWidth(2, 80)  # 推荐
        self.table.setColumnWidth(3, 100) # 时长
        h.setStretchLastSection(True)
        
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setWordWrap(True)
        # 移除 ResizeToContents 以提升性能，改用固定行高或按需调整
        self.table.verticalHeader().setDefaultSectionSize(60) 
        
        self._update_table_style()
        layout.addWidget(self.table, 1)

    def set_theme(self, theme_name: str):
        self._current_theme = theme_name
        is_dark = theme_name == 'dark'
        color = "#fafafa" if is_dark else "#18181b"
        self.title_label.setStyleSheet(f"color:{color}; font-size:20px; font-weight:600;")
        self._update_table_style()

    def _update_table_style(self):
        is_dark = getattr(self, '_current_theme', 'dark') == 'dark'
        bg = "#18181b" if is_dark else "#ffffff"
        fg = "#fafafa" if is_dark else "#18181b"
        h_bg = "#27272a" if is_dark else "#f4f4f5"
        border = "rgba(255,255,255,0.06)" if is_dark else "rgba(0,0,0,0.06)"

        self.table.setStyleSheet(f"""
            QTableWidget {{ background-color: {bg}; border: 1px solid {border}; border-radius: 8px; color: {fg}; }}
            QHeaderView::section {{ background-color: {h_bg}; color: #71717a; border: none; border-bottom: 1px solid {border}; padding: 10px; }}
            QTableWidget::item {{ padding: 8px; border-bottom: 1px solid {border.replace('0.06', '0.03')}; }}
            QTableWidget::item:selected {{ background: rgba(59,130,246,0.15); }}
        """)

    def _on_search_changed(self, text):
        self.filter_game_name = text.strip()
        self.current_page = 0
        self.refresh_data()

    def _prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.refresh_data()

    def _next_page(self):
        self.current_page += 1
        self.refresh_data()

    # 显示指定游戏的评价
    def show_game_reviews(self, game_name):
        self.search_input.setText(game_name) # 这会触发 _on_search_changed -> refresh_data

    # 刷新数据
    def refresh_data(self):
        # 获取所有评价并过滤
        all_reviews = self.db.get_all_reviews()
        
        filtered = []
        if self.filter_game_name:
            search_key = self.filter_game_name.lower()
            for r in all_reviews:
                if search_key in r['game_name'].lower():
                    filtered.append(r)
        else:
            filtered = all_reviews

        total = len(filtered)
        total_pages = max(1, (total + self.page_size - 1) // self.page_size)
        
        if self.current_page >= total_pages:
            self.current_page = total_pages - 1
        if self.current_page < 0:
            self.current_page = 0

        self.page_label.setText(f"第 {self.current_page + 1} / {total_pages} 页 (共 {total} 条)")
        self.btn_prev.setEnabled(self.current_page > 0)
        self.btn_next.setEnabled(self.current_page < total_pages - 1)

        start = self.current_page * self.page_size
        end = min(start + self.page_size, total)
        page_items = filtered[start:end]

        self.table.setRowCount(len(page_items))
        for row, r in enumerate(page_items):
            self.table.setItem(row, 0, QTableWidgetItem(r['game_name']))
            
            text_item = QTableWidgetItem(r['review_text'])
            text_item.setToolTip(r['review_text'])
            self.table.setItem(row, 1, text_item)
            
            is_up = "推荐" if r['voted_up'] else "不推荐"
            up_item = QTableWidgetItem(is_up)
            up_item.setForeground(QColor("#10b981") if r['voted_up'] else QColor("#ef4444"))
            self.table.setItem(row, 2, up_item)
            
            self.table.setItem(row, 3, QTableWidgetItem(f"{r['author_playtime']} min"))
            
            dt = datetime.fromtimestamp(r['timestamp_created']).strftime('%Y-%m-%d %H:%M')
            self.table.setItem(row, 4, QTableWidgetItem(dt))
