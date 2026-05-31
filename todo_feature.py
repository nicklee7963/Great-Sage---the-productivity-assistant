"""
大賢者（Great Sage）- 待辦清單模組

本模組提供待辦清單管理功能：
  • 建立、編輯、刪除工作任務
  • 任務優先度分類（緊急、常規、低優先度）
  • 工作狀態追蹤（待處理、進行中、已完成）
  • 小型行事曆與日期篩選
  • 三列佈局（清單、顯示、編輯）
"""

import os
import json
import uuid
import calendar
from datetime import datetime, timedelta, date
from PyQt5 import QtWidgets, QtCore, QtGui


def _screen_geometry():
    app = QtWidgets.QApplication.instance()
    if app is not None:
        screen = app.primaryScreen()
        if screen is not None:
            return screen.availableGeometry()
    return QtCore.QRect(0, 0, 1600, 900)


def _screen_scale():
    geometry = _screen_geometry()
    scale = min(geometry.width() / 1600.0, geometry.height() / 900.0, 1.0)
    return max(0.62, scale)


def _scaled(value, scale):
    return max(1, int(round(value * scale)))


class ClickableContainer(QtWidgets.QWidget):
    """可點擊的容器 - 處理背景點擊事件"""
    background_clicked = QtCore.pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayout(QtWidgets.QVBoxLayout(self))
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)
    
    def mousePressEvent(self, event):
        """處理滑鼠點擊 - 檢查是否點擊在背景"""
        # 取得點擊位置下的 widget
        clicked_widget = self.childAt(event.pos())
        
        # 如果點擊的是 TaskCard 或其子 widget，讓事件繼續傳遞
        if clicked_widget:
            child = clicked_widget
            while child:
                if isinstance(child, TaskCard):
                    # 是任務卡片，讓事件繼續傳遞
                    return super().mousePressEvent(event)
                child = child.parent() if hasattr(child, 'parent') else None
        
        # 點擊在背景上
        self.background_clicked.emit()
        event.accept()


class CalendarWidget(QtWidgets.QWidget):
    """小型行事曆 - 顯示月份、標示有任務的日期、支持日期點擊"""
    date_selected = QtCore.pyqtSignal(str)  # 信號：傳送選中的日期字符串 (YYYY-MM-DD)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui_scale = _screen_scale()
        self.current_date = date.today()
        self.selected_date = None
        self.today = date.today()  # 今天的日期
        self.task_dates = set()  # 有任務的日期集合
        self.date_buttons = {}  # 日期按鈕映射
        
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(_scaled(8, self.ui_scale), _scaled(8, self.ui_scale), _scaled(8, self.ui_scale), _scaled(8, self.ui_scale))
        layout.setSpacing(_scaled(8, self.ui_scale))
        
        # 月份導航
        nav_layout = QtWidgets.QHBoxLayout()
        
        self.btn_prev = QtWidgets.QPushButton('◀')
        self.btn_prev.setFixedSize(_scaled(24, self.ui_scale), _scaled(24, self.ui_scale))
        self.btn_prev.setStyleSheet('''
            QPushButton {
                background: rgba(7, 16, 29, 220);
                color: #e6fbff;
                border: 1px solid rgba(110, 214, 255, 90);
                border-radius: 4px;
                font-size: 12px;
                padding: 0px;
            }
            QPushButton:hover {
                border: 1px solid rgba(0, 242, 255, 200);
            }
        ''')
        self.btn_prev.clicked.connect(self._prev_month)
        nav_layout.addWidget(self.btn_prev)
        
        self.month_label = QtWidgets.QLabel()
        self.month_label.setStyleSheet('color: #e6fbff; font-weight: bold; font-size: 13px;')
        self.month_label.setAlignment(QtCore.Qt.AlignCenter)
        nav_layout.addWidget(self.month_label, stretch=1)
        
        self.btn_next = QtWidgets.QPushButton('▶')
        self.btn_next.setFixedSize(_scaled(24, self.ui_scale), _scaled(24, self.ui_scale))
        self.btn_next.setStyleSheet('''
            QPushButton {
                background: rgba(7, 16, 29, 220);
                color: #e6fbff;
                border: 1px solid rgba(110, 214, 255, 90);
                border-radius: 4px;
                font-size: 12px;
                padding: 0px;
            }
            QPushButton:hover {
                border: 1px solid rgba(0, 242, 255, 200);
            }
        ''')
        self.btn_next.clicked.connect(self._next_month)
        nav_layout.addWidget(self.btn_next)
        
        layout.addLayout(nav_layout)
        
        # 星期標題
        weekday_header = QtWidgets.QHBoxLayout()
        weekday_header.setSpacing(_scaled(2, self.ui_scale))
        for weekday in ['一', '二', '三', '四', '五', '六', '日']:
            label = QtWidgets.QLabel(weekday)
            label.setStyleSheet('color: #b0e0ff; font-size: 11px; font-weight: bold;')
            label.setAlignment(QtCore.Qt.AlignCenter)
            label.setFixedHeight(_scaled(18, self.ui_scale))
            weekday_header.addWidget(label)
        layout.addLayout(weekday_header)
        
        # 日期格子容器
        self.calendar_grid = QtWidgets.QGridLayout()
        self.calendar_grid.setSpacing(_scaled(2, self.ui_scale))
        self.calendar_grid.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(self.calendar_grid)
        
        layout.addStretch()
        
        self._render_calendar()
    
    def _render_calendar(self):
        """繪製日期格子"""
        # 清空舊的按鈕
        while self.calendar_grid.count():
            item = self.calendar_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.date_buttons.clear()
        
        # 更新月份標籤
        self.month_label.setText(f'{self.current_date.year} 年 {self.current_date.month} 月')
        
        # 獲取該月份的日期
        year, month = self.current_date.year, self.current_date.month
        cal = calendar.monthcalendar(year, month)
        
        row = 0
        for week in cal:
            col = 0
            for day in week:
                if day == 0:
                    # 不屬於該月份的日期
                    empty = QtWidgets.QLabel('')
                    empty.setFixedSize(_scaled(24, self.ui_scale), _scaled(24, self.ui_scale))
                    self.calendar_grid.addWidget(empty, row, col)
                else:
                    # 該月份的日期
                    btn = QtWidgets.QPushButton(str(day))
                    btn.setFixedSize(_scaled(24, self.ui_scale), _scaled(24, self.ui_scale))
                    btn.setProperty('date', date(year, month, day))
                    
                    # 檢查這一天是否有任務
                    day_str = f'{year:04d}-{month:02d}-{day:02d}'
                    
                    btn.clicked.connect(lambda checked=False, d=day: self._on_date_clicked(d))
                    self.calendar_grid.addWidget(btn, row, col)
                    self.date_buttons[day_str] = btn
                
                col += 1
            row += 1
        
        # 更新按鈕樣式（包括選中狀態和任務標記）
        self._update_button_styles()
    
    def _on_date_clicked(self, day):
        """日期點擊事件"""
        year, month = self.current_date.year, self.current_date.month
        selected = date(year, month, day)
        self.selected_date = selected
        date_str = f'{year:04d}-{month:02d}-{day:02d}'
        # 更新該日期按鈕的樣式
        self._update_button_styles()
        self.date_selected.emit(date_str)
    
    def _update_button_styles(self):
        """更新所有按鈕的樣式（包括選中狀態、今天標記、任務標記）"""
        for date_str, btn in self.date_buttons.items():
            day_str = date_str
            has_task = day_str in self.task_dates
            is_selected = (self.selected_date and 
                          f'{self.selected_date.year:04d}-{self.selected_date.month:02d}-{self.selected_date.day:02d}' == day_str)
            # 檢查是否是今天
            is_today = f'{self.today.year:04d}-{self.today.month:02d}-{self.today.day:02d}' == day_str
            
            if is_selected:
                # 選中的日期：使用金色/黃色高亮（最高優先級）
                btn.setStyleSheet('''
                    QPushButton {
                        background: rgba(255, 200, 0, 180);
                        color: #000000;
                        border: 2px solid rgba(255, 220, 100, 255);
                        border-radius: 3px;
                        font-size: 11px;
                        padding: 0px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background: rgba(255, 220, 80, 220);
                    }
                ''')
            elif is_today:
                # 今天的日期：使用紅色高亮（無論有沒有任務）
                btn.setStyleSheet('''
                    QPushButton {
                        background: rgba(255, 100, 100, 150);
                        color: #ffffff;
                        border: 2px solid rgba(255, 150, 150, 255);
                        border-radius: 3px;
                        font-size: 11px;
                        padding: 0px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background: rgba(255, 120, 120, 200);
                    }
                ''')
            elif has_task:
                # 有任務的日期：青綠色
                btn.setStyleSheet('''
                    QPushButton {
                        background: rgba(0, 200, 150, 150);
                        color: #000000;
                        border: 1px solid rgba(0, 200, 150, 200);
                        border-radius: 3px;
                        font-size: 11px;
                        padding: 0px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background: rgba(0, 220, 180, 200);
                    }
                ''')
            else:
                # 普通日期
                btn.setStyleSheet('''
                    QPushButton {
                        background: rgba(7, 16, 29, 220);
                        color: #e6fbff;
                        border: 1px solid rgba(110, 214, 255, 60);
                        border-radius: 3px;
                        font-size: 11px;
                        padding: 0px;
                    }
                    QPushButton:hover {
                        border: 1px solid rgba(0, 242, 255, 200);
                    }
                ''')
    
    def _prev_month(self):
        """上一個月份"""
        if self.current_date.month == 1:
            self.current_date = self.current_date.replace(year=self.current_date.year - 1, month=12)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month - 1)
        self._render_calendar()
    
    def _next_month(self):
        """下一個月份"""
        if self.current_date.month == 12:
            self.current_date = self.current_date.replace(year=self.current_date.year + 1, month=1)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month + 1)
        self._render_calendar()
    
    def update_task_dates(self, tasks):
        """更新任務日期集合"""
        self.task_dates.clear()
        today = date.today()
        
        for task in tasks:
            if task.get('type') == 'urgent':
                # 緊急任務：使用 created_date
                created = task.get('created_date', '')
                if created:
                    try:
                        task_date = datetime.fromisoformat(created).date()
                        self.task_dates.add(f'{task_date.year:04d}-{task_date.month:02d}-{task_date.day:02d}')
                    except:
                        pass
            elif task.get('type') == 'routine':
                # 常規任務：使用 routine_days
                routine_days = task.get('routine_days', [])
                for day_offset in range(-30, 30):  # 顯示前後30天
                    check_date = today + timedelta(days=day_offset)
                    if check_date.weekday() in routine_days:
                        self.task_dates.add(f'{check_date.year:04d}-{check_date.month:02d}-{check_date.day:02d}')
        
        self._update_button_styles()


class TodoListPanel(QtWidgets.QWidget):
    """待辦清單主面板 - 三列佈局：左(清單表) + 中(任務顯示) + 右(編輯面板)"""
    
    # 任務狀態常數
    STATUS_PENDING = 'pending'      # 紅色 - 未執行
    STATUS_IN_PROGRESS = 'in_progress'  # 黃色 - 執行中
    STATUS_COMPLETED = 'completed'  # 綠色 - 已完成
    
    # 任務類型常數
    TYPE_URGENT = 'urgent'          # 特定時間完成（緊急任務）
    TYPE_ROUTINE = 'routine'        # 每天或有規律完成的（常規任務）
    
    # 狀態顏色定義
    STATUS_COLORS = {
        STATUS_PENDING: QtGui.QColor(255, 100, 100),        # 紅色
        STATUS_IN_PROGRESS: QtGui.QColor(255, 200, 100),    # 黃色
        STATUS_COMPLETED: QtGui.QColor(100, 255, 150),      # 綠色
    }
    
    # 狀態中文名稱
    STATUS_NAMES = {
        STATUS_PENDING: '未執行',
        STATUS_IN_PROGRESS: '執行中',
        STATUS_COMPLETED: '已完成',
    }
    
    # 任務類型中文名稱
    TYPE_NAMES = {
        TYPE_URGENT: '緊急任務',
        TYPE_ROUTINE: '常規任務',
    }
    
    def __init__(self, parent=None, compact_mode=False, main_window=None):
        super().__init__(parent)
        self.compact_mode = compact_mode
        self.main_window = main_window  # 主窗口引用
        self._data_file = os.path.join(os.path.dirname(__file__), 'todo_records.json')
        self.tasks = []  # 所有任務
        self.current_selected_task = None  # 當前選中的任務
        self.filtered_date = None  # 當前篩選的日期 (YYYY-MM-DD 字符串)
        
        self._load_tasks()
        
        # 主佈局：二列（移除左側面板）
        main_layout = QtWidgets.QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)
        
        # 中間面板：任務顯示區
        self.middle_panel = self._build_middle_panel()
        main_layout.addWidget(self.middle_panel, stretch=1)
        
        # 右側面板：編輯面板
        self.right_panel = self._build_right_panel()
        main_layout.addWidget(self.right_panel, stretch=0)
        
        self.refresh_display()
    
    def _load_tasks(self):
        """從JSON文件加載任務"""
        if os.path.isfile(self._data_file):
            try:
                with open(self._data_file, 'r', encoding='utf-8') as f:
                    self.tasks = json.load(f)
            except Exception as e:
                print(f"Error loading tasks: {e}")
                self.tasks = []
        else:
            self.tasks = []
    
    def _save_tasks(self):
        """將任務保存到JSON文件"""
        try:
            with open(self._data_file, 'w', encoding='utf-8') as f:
                json.dump(self.tasks, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving tasks: {e}")
    
    def get_tasks_for_display(self):
        """獲取用於顯示在左邊視窗的任務列表"""
        return self._get_sorted_tasks()
    
    def get_filtered_tasks_for_display(self):
        """獲取根據篩選日期過濾後的任務列表（用於中間窗口）"""
        all_tasks = self._get_sorted_tasks()
        if not self.filtered_date:
            # 無篩選，返回所有任務
            return all_tasks, None
        
        # 返回篩選後的任務和篩選日期
        filtered = [t for t in all_tasks if self._is_task_matching_filter(t)]
        return filtered, self.filtered_date
    
    def get_filtered_date_display_text(self):
        """獲取篩選日期的顯示文本"""
        if not self.filtered_date:
            return None
        
        try:
            date_obj = datetime.strptime(self.filtered_date, '%Y-%m-%d').date()
            weekday_names = ['一', '二', '三', '四', '五', '六', '日']
            weekday = weekday_names[date_obj.weekday()]
            return f'{self.filtered_date} (星期{weekday})'
        except:
            return self.filtered_date
    
    def select_task_by_id(self, task_id):
        """外部調用：根據ID選中任務"""
        self._select_task_by_id(task_id)
    
    def _build_middle_panel(self):
        """建構中間面板 - 任務顯示區（按類型和字母順序排列）"""
        panel = QtWidgets.QFrame()
        panel.setStyleSheet('background: rgba(9, 18, 31, 220); border: none; border-radius: 8px;')
        
        layout = QtWidgets.QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # 標題
        title = QtWidgets.QLabel('任務清單')
        title.setStyleSheet('color: #e6fbff; font-weight: bold; font-size: 21px;')
        layout.addWidget(title)
        
        # 任務卡片容器（可滾動）
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet('''
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: rgba(14, 28, 50, 200);
                border: 1px solid rgba(110, 214, 255, 60);
                border-radius: 4px;
                width: 12px;
            }
            QScrollBar::handle:vertical {
                background: rgba(110, 214, 255, 120);
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(110, 214, 255, 180);
            }
        ''')
        
        self.middle_container = ClickableContainer()
        self.middle_container.background_clicked.connect(self._on_middle_background_clicked)
        self.middle_layout = self.middle_container.layout()
        self.middle_layout.setContentsMargins(0, 0, 0, 0)
        self.middle_layout.setSpacing(8)
        
        scroll.setWidget(self.middle_container)
        layout.addWidget(scroll)
        
        return panel
    
    def _build_right_panel(self):
        """建構右側面板 - 編輯面板"""
        panel = QtWidgets.QFrame()
        panel.setStyleSheet('background: rgba(9, 18, 31, 220); border: none; border-radius: 8px;')
        self.ui_scale = _screen_scale()
        panel.setMinimumWidth(_scaled(240, self.ui_scale))
        panel.setMaximumWidth(_scaled(320, self.ui_scale))
        
        layout = QtWidgets.QVBoxLayout(panel)
        layout.setContentsMargins(_scaled(12, self.ui_scale), _scaled(12, self.ui_scale), _scaled(12, self.ui_scale), _scaled(12, self.ui_scale))
        layout.setSpacing(_scaled(10, self.ui_scale))
        
        # ===== 行事曆區域 =====
        self.calendar = CalendarWidget()
        self.calendar.date_selected.connect(self._on_calendar_date_selected)
        layout.addWidget(self.calendar)
        
        # 分隔線
        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.HLine)
        separator.setStyleSheet('color: rgba(110, 214, 255, 60);')
        layout.addWidget(separator)
        
        # ===== 任務編輯區域 =====
        title = QtWidgets.QLabel('編輯任務')
        title.setStyleSheet('color: #e6fbff; font-weight: bold; font-size: 14px;')
        layout.addWidget(title)
        
        # 當前選中日期標籤
        self.selected_date_label = QtWidgets.QLabel('選中日期: 無')
        self.selected_date_label.setStyleSheet('color: #ffcc00; font-size: 13px; font-weight: 600;')
        layout.addWidget(self.selected_date_label)
        
        layout.addWidget(QtWidgets.QLabel('任務名稱:', parent=panel))
        layout.itemAt(layout.count() - 1).widget().setStyleSheet('color: #b0e0ff; font-size: 15px; font-weight: 600;')
        self.task_name_input = QtWidgets.QLineEdit()
        self.task_name_input.setStyleSheet('''
            QLineEdit {
                background: rgba(7, 16, 29, 220);
                color: #e6fbff;
                border: 1px solid rgba(110, 214, 255, 90);
                border-radius: 4px;
                padding: 10px;
                font-size: 15px;
                font-weight: 500;
            }
            QLineEdit:focus {
                border: 1px solid rgba(0, 242, 255, 200);
            }
        ''')
        self.task_name_input.setPlaceholderText('輸入任務名稱...')
        layout.addWidget(self.task_name_input)
        
        # 任務類型選擇
        layout.addWidget(QtWidgets.QLabel('類型:', parent=panel))
        layout.itemAt(layout.count() - 1).widget().setStyleSheet('color: #b0e0ff; font-size: 15px; font-weight: 600;')
        self.task_type_combo = QtWidgets.QComboBox()
        self.task_type_combo.addItem(self.TYPE_NAMES[self.TYPE_URGENT], self.TYPE_URGENT)
        self.task_type_combo.addItem(self.TYPE_NAMES[self.TYPE_ROUTINE], self.TYPE_ROUTINE)
        self.task_type_combo.setStyleSheet('''
            QComboBox {
                background: rgba(7, 16, 29, 220);
                color: #e6fbff;
                border: 1px solid rgba(110, 214, 255, 90);
                border-radius: 4px;
                padding: 6px;
                            font-size: 15px;
                            font-weight: 500;
            }
        ''')
        self.task_type_combo.currentIndexChanged.connect(self._on_task_type_changed)
        layout.addWidget(self.task_type_combo)
        
        # 任務狀態選擇
        layout.addWidget(QtWidgets.QLabel('狀態:', parent=panel))
        layout.itemAt(layout.count() - 1).widget().setStyleSheet('color: #b0e0ff; font-size: 15px; font-weight: 600;')
        self.task_status_combo = QtWidgets.QComboBox()
        self.task_status_combo.addItem(self.STATUS_NAMES[self.STATUS_PENDING], self.STATUS_PENDING)
        self.task_status_combo.addItem(self.STATUS_NAMES[self.STATUS_IN_PROGRESS], self.STATUS_IN_PROGRESS)
        self.task_status_combo.addItem(self.STATUS_NAMES[self.STATUS_COMPLETED], self.STATUS_COMPLETED)
        self.task_status_combo.setStyleSheet('''
                            font-size: 15px;
                            font-weight: 500;
            QComboBox {
                background: rgba(7, 16, 29, 220);
                color: #e6fbff;
                border: 1px solid rgba(110, 214, 255, 90);
                border-radius: 4px;
                padding: 6px;
            }
        ''')
        layout.addWidget(self.task_status_combo)
        
        # 描述輸入
        layout.addWidget(QtWidgets.QLabel('描述:', parent=panel))
        layout.itemAt(layout.count() - 1).widget().setStyleSheet('color: #b0e0ff; font-size: 15px; font-weight: 600;')
        self.task_desc_input = QtWidgets.QPlainTextEdit()
        self.task_desc_input.setStyleSheet('''
            QPlainTextEdit {
                background: rgba(7, 16, 29, 220);
                color: #e6fbff;
                border: 1px solid rgba(110, 214, 255, 90);
                border-radius: 4px;
                padding: 10px;
                font-size: 15px;
                font-weight: 500;
            }
            QPlainTextEdit:focus {
                border: 1px solid rgba(0, 242, 255, 200);
            }
        ''')
        self.task_desc_input.setPlaceholderText('輸入任務描述...')
        self.task_desc_input.setMinimumHeight(_scaled(72, self.ui_scale))
        self.task_desc_input.setMaximumHeight(_scaled(120, self.ui_scale))
        layout.addWidget(self.task_desc_input)

        # 常規任務的每週日期選擇
        self.weekday_container = QtWidgets.QWidget()
        weekday_layout = QtWidgets.QVBoxLayout(self.weekday_container)
        weekday_layout.setContentsMargins(0, 0, 0, 0)
        weekday_layout.setSpacing(6)

        weekday_label = QtWidgets.QLabel('每週日期:')
        weekday_label.setStyleSheet('color: #b0e0ff; font-size: 15px; font-weight: 600;')
        weekday_layout.addWidget(weekday_label)

        self.weekday_buttons = []
        weekday_button_row = QtWidgets.QHBoxLayout()
        weekday_button_row.setSpacing(6)
        weekday_button_row.setContentsMargins(0, 0, 0, 0)

        weekday_items = [('一', 0), ('二', 1), ('三', 2), ('四', 3), ('五', 4), ('六', 5), ('日', 6)]
        for text, day_index in weekday_items:
            button = QtWidgets.QToolButton()
            button.setText(text)
            button.setCheckable(True)
            button.setFixedSize(_scaled(34, self.ui_scale), _scaled(34, self.ui_scale))
            button.setFont(QtGui.QFont('Microsoft JhengHei', 8, QtGui.QFont.Bold))
            button.setStyleSheet('''
                QToolButton {
                    background: rgba(7, 16, 29, 220);
                    color: #e6fbff;
                    border: 2px solid rgba(110, 214, 255, 150);
                    border-radius: 17px;
                }
                QToolButton:hover {
                    border: 2px solid rgba(0, 242, 255, 220);
                }
                QToolButton:checked {
                    background: rgba(100, 255, 200, 150);
                    color: #000000;
                    border: 3px solid rgba(0, 242, 255, 255);
                    font-weight: bold;
                }
            ''')
            button.toggled.connect(self._on_weekday_button_toggled)
            button.weekday_index = day_index
            weekday_button_row.addWidget(button)
            self.weekday_buttons.append(button)

        weekday_button_row.addStretch()
        weekday_layout.addLayout(weekday_button_row)
        layout.addWidget(self.weekday_container)
        
        # 按鈕區
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.setSpacing(8)
        
        self.btn_add = QtWidgets.QPushButton('新增')
        self.btn_add.setStyleSheet('''
            QPushButton {
                background: rgba(14, 28, 50, 220);
                color: #effcff;
                border: 1px solid rgba(110, 214, 255, 90);
                border-radius: 6px;
                padding: 8px;
            }
            QPushButton:hover {
                background: rgba(0, 200, 150, 120);
                border: 1px solid rgba(0, 200, 150, 200);
            }
        ''')
        self.btn_add.clicked.connect(self._on_add_task)
        button_layout.addWidget(self.btn_add)
        
        self.btn_update = QtWidgets.QPushButton('更新')
        self.btn_update.setStyleSheet('''
            QPushButton {
                background: rgba(14, 28, 50, 220);
                color: #effcff;
                border: 1px solid rgba(110, 214, 255, 90);
                border-radius: 6px;
                padding: 8px;
            }
            QPushButton:hover {
                background: rgba(0, 150, 200, 120);
                border: 1px solid rgba(0, 150, 200, 200);
            }
        ''')
        self.btn_update.clicked.connect(self._on_update_task)
        button_layout.addWidget(self.btn_update)
        
        self.btn_delete = QtWidgets.QPushButton('刪除')
        self.btn_delete.setStyleSheet('''
            QPushButton {
                background: rgba(14, 28, 50, 220);
                color: #effcff;
                border: 1px solid rgba(110, 214, 255, 90);
                border-radius: 6px;
                padding: 8px;
            }
            QPushButton:hover {
                background: rgba(200, 100, 100, 120);
                border: 1px solid rgba(200, 100, 100, 200);
            }
        ''')
        self.btn_delete.clicked.connect(self._on_delete_task)
        button_layout.addWidget(self.btn_delete)
        
        layout.addLayout(button_layout)
        layout.addStretch()
        
        self._clear_edit_form()
        self._update_button_state()
        self._update_weekday_selector_visibility()
        
        return panel
    
    def _update_button_state(self):
        """更新按鈕顯示狀態"""
        if self.current_selected_task is None:
            # 未選中任務：只顯示新增
            self.btn_add.show()
            self.btn_update.hide()
            self.btn_delete.hide()
        else:
            # 已選中任務：顯示更新和刪除
            self.btn_add.hide()
            self.btn_update.show()
            self.btn_delete.show()
    
    def _on_middle_background_clicked(self):
        """中間面板背景被點擊"""
        self._clear_edit_form()
        self._update_button_state()
        self._update_weekday_selector_visibility()

    def _on_task_type_changed(self):
        """任務類型變更時更新常規任務日期選擇器"""
        self._update_weekday_selector_visibility()

    def _on_weekday_button_toggled(self, checked):
        """切換常規任務的每週日期選擇狀態"""
        # 按鈕本身已經是可切換狀態，這裡只需要在更新任務時讀取即可
        return

    def _get_selected_weekdays(self):
        return [button.weekday_index for button in self.weekday_buttons if button.isChecked()]

    def _set_selected_weekdays(self, selected_weekdays):
        selected = set(selected_weekdays or [])
        for button in self.weekday_buttons:
            button.setChecked(button.weekday_index in selected)

    def _update_weekday_selector_visibility(self):
        is_routine = self.task_type_combo.currentData() == self.TYPE_ROUTINE
        self.weekday_container.setVisible(is_routine)
        for button in self.weekday_buttons:
            button.setEnabled(is_routine)
            if not is_routine:
                button.setChecked(False)
    
    def _select_task_by_id(self, task_id):
        """根據ID選中任務"""
        for task in self.tasks:
            if task.get('id') == task_id:
                self.current_selected_task = task
                self._fill_edit_form(task)
                self._highlight_task_in_middle(task_id)
                self._update_button_state()
                break
    
    def _fill_edit_form(self, task):
        """用任務信息填充編輯表單"""
        self.task_name_input.setText(task.get('name', ''))
        
        # 設置類型
        type_index = self.task_type_combo.findData(task.get('type', self.TYPE_URGENT))
        if type_index >= 0:
            self.task_type_combo.setCurrentIndex(type_index)
        
        # 設置狀態
        status_index = self.task_status_combo.findData(task.get('status', self.STATUS_PENDING))
        if status_index >= 0:
            self.task_status_combo.setCurrentIndex(status_index)
        
        self.task_desc_input.setPlainText(task.get('description', ''))
        self._set_selected_weekdays(task.get('routine_days', []))
        self._update_weekday_selector_visibility()
    
    def _clear_edit_form(self):
        """清空編輯表單"""
        self.task_name_input.clear()
        self.task_type_combo.setCurrentIndex(0)
        self.task_status_combo.setCurrentIndex(0)
        self.task_desc_input.clear()
        self._set_selected_weekdays([])
        self.current_selected_task = None
        self._update_button_state()
        self._update_weekday_selector_visibility()
    
    def _on_add_task(self):
        """添加新任務"""
        name = self.task_name_input.text().strip()
        if not name:
            QtWidgets.QMessageBox.warning(self, '警告', '請輸入任務名稱')
            return
        
        # 確定任務的日期（對於緊急任務）
        task_created_date = None
        if self.task_type_combo.currentData() == self.TYPE_URGENT and self.filtered_date:
            # 如果是緊急任務且有選中的日期，使用該日期
            try:
                selected_date_obj = datetime.strptime(self.filtered_date, '%Y-%m-%d').date()
                task_created_date = datetime.combine(selected_date_obj, datetime.min.time()).isoformat()
            except:
                task_created_date = datetime.now().isoformat()
        else:
            task_created_date = datetime.now().isoformat()
        
        task = {
            'id': str(uuid.uuid4()),
            'name': name,
            'type': self.task_type_combo.currentData(),
            'status': self.task_status_combo.currentData(),
            'description': self.task_desc_input.toPlainText().strip(),
            'routine_days': self._get_selected_weekdays() if self.task_type_combo.currentData() == self.TYPE_ROUTINE else [],
            'created_date': task_created_date,
            'completed_date': None,
        }
        
        self.tasks.append(task)
        self._save_tasks()
        self._clear_edit_form()
        self.refresh_display()
        
        # 顯示成功提示
        if self.filtered_date:
            QtWidgets.QMessageBox.information(self, '成功', f'已新增任務到 {self.filtered_date}')
        else:
            QtWidgets.QMessageBox.information(self, '成功', '已新增任務')
    
    def _on_update_task(self):
        """更新選中的任務"""
        if not self.current_selected_task:
            QtWidgets.QMessageBox.warning(self, '警告', '請先選擇要更新的任務')
            return
        
        name = self.task_name_input.text().strip()
        if not name:
            QtWidgets.QMessageBox.warning(self, '警告', '請輸入任務名稱')
            return
        
        self.current_selected_task['name'] = name
        self.current_selected_task['type'] = self.task_type_combo.currentData()
        self.current_selected_task['status'] = self.task_status_combo.currentData()
        self.current_selected_task['description'] = self.task_desc_input.toPlainText().strip()
        self.current_selected_task['routine_days'] = self._get_selected_weekdays() if self.task_type_combo.currentData() == self.TYPE_ROUTINE else []
        
        # 如果是緊急任務且有選中的日期，更新該日期
        if self.task_type_combo.currentData() == self.TYPE_URGENT and self.filtered_date:
            try:
                selected_date_obj = datetime.strptime(self.filtered_date, '%Y-%m-%d').date()
                self.current_selected_task['created_date'] = datetime.combine(selected_date_obj, datetime.min.time()).isoformat()
            except:
                pass
        
        self._save_tasks()
        self.refresh_display()
        QtWidgets.QMessageBox.information(self, '成功', '已更新任務')
    
    def _on_delete_task(self):
        """刪除選中的任務"""
        if not self.current_selected_task:
            QtWidgets.QMessageBox.warning(self, '警告', '請先選擇要刪除的任務')
            return
        
        task_name = self.current_selected_task.get('name', '任務')
        reply = QtWidgets.QMessageBox.question(self, '確認', f'確定要刪除「{task_name}」嗎？',
                                               QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            delete_date = None
            if self.current_selected_task.get('type') == self.TYPE_URGENT:
                created = self.current_selected_task.get('created_date', '')
                if created:
                    try:
                        task_date = datetime.fromisoformat(created).date()
                        delete_date = f'{task_date.year:04d}-{task_date.month:02d}-{task_date.day:02d}'
                    except:
                        pass
            
            self.tasks = [t for t in self.tasks if t.get('id') != self.current_selected_task.get('id')]
            self._save_tasks()
            self._clear_edit_form()
            self.refresh_display()
            
            if delete_date:
                QtWidgets.QMessageBox.information(self, '成功', f'已刪除 {delete_date} 的任務')
            else:
                QtWidgets.QMessageBox.information(self, '成功', '已刪除任務')
    
    def _highlight_task_in_middle(self, task_id):
        """在中間面板中高亮任務"""
        for i in range(self.middle_layout.count()):
            widget = self.middle_layout.itemAt(i).widget()
            if isinstance(widget, TaskCard) and widget.task.get('id') == task_id:
                widget.setStyleSheet(widget.get_selected_style())
            elif isinstance(widget, TaskCard):
                widget.setStyleSheet(widget.get_normal_style())
    
    def _get_sorted_tasks(self):
        """按類型和名稱排序任務"""
        # 先按類型排序（緊急任務在前），再按名稱排序
        sorted_tasks = sorted(self.tasks, key=lambda t: (
            0 if t.get('type') == self.TYPE_URGENT else 1,
            t.get('name', '').lower()
        ))
        return sorted_tasks
    
    def refresh_display(self):
        """刷新顯示"""
        # 更新行事曆的任務日期標記
        if hasattr(self, 'calendar'):
            self.calendar.update_task_dates(self.tasks)
        self._refresh_middle_panel()
        self._sync_main_window_todo_display()

    def _sync_main_window_todo_display(self):
        """同步更新大賢者視窗中的待辦清單顯示"""
        if self.main_window is not None:
            try:
                self.main_window.show_todo_list(self)
            except Exception as e:
                print(f"Error syncing todo list display: {e}")
    
    def _refresh_middle_panel(self):
        """刷新中間面板 - 任務卡片"""
        # 清空現有卡片
        while self.middle_layout.count():
            widget = self.middle_layout.takeAt(0).widget()
            if widget:
                widget.deleteLater()
        
        # 獲取要顯示的任務（應用日期篩選）
        all_tasks = self._get_sorted_tasks()
        displayed_tasks = [t for t in all_tasks if self._is_task_matching_filter(t)]
        
        # 按類型分組
        urgent_tasks = [t for t in displayed_tasks if t.get('type') == self.TYPE_URGENT]
        routine_tasks = [t for t in displayed_tasks if t.get('type') == self.TYPE_ROUTINE]
        
        # 添加緊急任務部分
        if urgent_tasks:
            section_label = QtWidgets.QLabel(self.TYPE_NAMES[self.TYPE_URGENT])
            section_label.setStyleSheet('color: #ff6464; font-weight: bold; font-size: 19px; margin-top: 8px;')
            self.middle_layout.addWidget(section_label)
            
            for task in urgent_tasks:
                card = TaskCard(task, self.STATUS_COLORS, self.STATUS_NAMES)
                card.clicked.connect(lambda task_id=task.get('id'): self._select_task_by_id(task_id))
                self.middle_layout.addWidget(card)
        
        # 添加常規任務部分
        if routine_tasks:
            section_label = QtWidgets.QLabel(self.TYPE_NAMES[self.TYPE_ROUTINE])
            section_label.setStyleSheet('color: #64b4ff; font-weight: bold; font-size: 19px; margin-top: 12px;')
            self.middle_layout.addWidget(section_label)
            
            for task in routine_tasks:
                card = TaskCard(task, self.STATUS_COLORS, self.STATUS_NAMES)
                card.clicked.connect(lambda task_id=task.get('id'): self._select_task_by_id(task_id))
                self.middle_layout.addWidget(card)
        
        # 如果沒有任務，顯示提示
        if not displayed_tasks:
            if self.filtered_date:
                empty_label = QtWidgets.QLabel(f'該日期無任務\n{self.filtered_date}')
            else:
                empty_label = QtWidgets.QLabel('暫無任務\n點擊右側「新增」按鈕建立任務')
            empty_label.setAlignment(QtCore.Qt.AlignCenter)
            empty_label.setStyleSheet('color: #8fb5d4; font-size: 19px; padding: 40px;')
            self.middle_layout.addWidget(empty_label)
        
        self.middle_layout.addStretch()
    
    def _is_task_matching_filter(self, task):
        """檢查任務是否匹配當前日期篩選"""
        if not self.filtered_date:
            # 無篩選，顯示所有任務
            return True
        
        task_type = task.get('type')
        
        if task_type == self.TYPE_URGENT:
            # 緊急任務：檢查 created_date 是否與篩選日期相同
            created = task.get('created_date', '')
            if created:
                try:
                    task_date = datetime.fromisoformat(created).date()
                    task_date_str = f'{task_date.year:04d}-{task_date.month:02d}-{task_date.day:02d}'
                    return task_date_str == self.filtered_date
                except:
                    return False
            return False
        
        elif task_type == self.TYPE_ROUTINE:
            # 常規任務：檢查 routine_days 是否包含篩選日期的星期
            routine_days = task.get('routine_days', [])
            try:
                filter_date = datetime.strptime(self.filtered_date, '%Y-%m-%d').date()
                weekday = filter_date.weekday()  # 0=Monday, 6=Sunday
                return weekday in routine_days
            except:
                return False
        
        return False
    
    def _on_calendar_date_selected(self, date_str):
        """行事曆日期被點擊"""
        self.filtered_date = date_str
        # 更新顯示選中日期的標籤
        if hasattr(self, 'selected_date_label'):
            self.selected_date_label.setText(f'選中日期: {date_str}')
        self._refresh_middle_panel()
        self._sync_main_window_todo_display()
    
    def _clear_date_filter(self):
        """清除日期篩選（不再使用）"""
    
    def _clear_date_filter(self):
        """清除日期篩選（不再使用）"""
        pass


class TaskCard(QtWidgets.QWidget):
    """任務卡片 - 顯示單個任務的信息"""
    clicked = QtCore.pyqtSignal(str)  # 發出任務ID信號
    
    def __init__(self, task, status_colors, status_names, parent=None):
        super().__init__(parent)
        self.task = task
        self.status_colors = status_colors
        self.status_names = status_names
        self.is_selected = False
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(0)
        
        # 任務標題 + 狀態顏色點
        title_layout = QtWidgets.QHBoxLayout()
        
        status = task.get('status', 'pending')
        status_color = status_colors.get(status, QtGui.QColor(255, 255, 255))
        status_name = status_names.get(status, 'Unknown')
        
        # 狀態點
        status_label = QtWidgets.QLabel('●')
        status_label.setStyleSheet(f'color: rgb({status_color.red()}, {status_color.green()}, {status_color.blue()}); font-size: 27px;')
        title_layout.addWidget(status_label)
        
        # 任務名稱
        name_label = QtWidgets.QLabel(task.get('name', 'Untitled'))
        name_label.setStyleSheet('color: #e6fbff; font-weight: 600; font-size: 23px;')
        name_label.setWordWrap(True)
        title_layout.addWidget(name_label, 1)
        
        layout.addLayout(title_layout)
        
        
        self.setStyleSheet(self.get_normal_style())
        self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
    
    def get_normal_style(self):
        """正常樣式"""
        return '''
            TaskCard {
                background: rgba(14, 28, 50, 180);
                border: none;
                border-radius: 6px;
            }
            TaskCard:hover {
                background: rgba(33, 62, 95, 200);
                border: none;
            }
        '''
    
    def get_selected_style(self):
        """選中樣式"""
        return '''
            TaskCard {
                background: rgba(0, 242, 255, 60);
                border: none;
                border-radius: 6px;
            }
        '''
    
    def mousePressEvent(self, event):
        """任務卡片被點擊"""
        self.clicked.emit(self.task.get('id', ''))
        super().mousePressEvent(event)
