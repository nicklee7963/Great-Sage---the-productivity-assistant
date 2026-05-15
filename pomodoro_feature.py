import os
import json
from datetime import datetime

from PyQt5 import QtWidgets, QtCore, QtGui, QtMultimedia


ACTIVITY_NEON_COLORS = {
    '讀書中': QtGui.QColor(0, 255, 200),
    '修習中': QtGui.QColor(0, 255, 200),
    '健身中': QtGui.QColor(0, 200, 255),
    '休息中': QtGui.QColor(100, 200, 255),
    '工作中': QtGui.QColor(0, 230, 200),
    '冥想中': QtGui.QColor(0, 180, 255),
}


def _ui_size(normal_size, compact_size, compact_mode):
    return compact_size if compact_mode else normal_size


def get_neon_color(activity_text):
    return ACTIVITY_NEON_COLORS.get(activity_text, QtGui.QColor(0, 255, 150))


class DailyPieChart(QtWidgets.QWidget):
    """顯示當日活動時間分配的圓餅圖（左邊圓餅圖，右邊圖例）"""
    def __init__(self, parent=None, compact_mode=False):
        super().__init__(parent)
        self.compact_mode = compact_mode
        self.data = {}
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.setMinimumSize(540 if compact_mode else 720, 580 if compact_mode else 760)
        self.setMinimumHeight(100)
        self.current_date = datetime.now().date()
        self.view_mode = 'day'

    def set_data(self, activities_data, date=None, view_mode='day'):
        self.data = activities_data
        self.view_mode = view_mode
        if date:
            self.current_date = date
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        margin_x = 14 if self.compact_mode else 24
        margin_y = 12 if self.compact_mode else 18
        inner_rect = self.rect().adjusted(margin_x, margin_y, -margin_x, -margin_y)

        title_height = 26 if self.compact_mode else 34
        legend_top_gap = 12 if self.compact_mode else 18
        legend_item_height = 20 if self.compact_mode else 26
        legend_swatch = 12 if self.compact_mode else 16
        legend_rows = max(1, sum(1 for value in self.data.values() if value > 0))
        legend_height = legend_rows * legend_item_height + 10

        available_width = max(1, inner_rect.width())
        available_height = max(1, inner_rect.height() - title_height - legend_height - legend_top_gap)
        chart_side = min(available_width, available_height)
        pie_scale = 0.60 if self.compact_mode else 0.75
        pie_size = max(140 if self.compact_mode else 180, int(chart_side * pie_scale))
        pie_x = inner_rect.center().x() - pie_size / 2
        pie_y = inner_rect.top() + title_height + max(0, (available_height - pie_size) / 2)
        pie_rect = QtCore.QRectF(pie_x, pie_y, pie_size, pie_size)

        legend_start_y = int(pie_rect.bottom() + legend_top_gap)
        legend_block_width = max(1, int(inner_rect.width() * 0.82))
        legend_x = int(inner_rect.center().x() - legend_block_width / 2)
        legend_width = legend_block_width

        if not self.data or sum(self.data.values()) == 0:
            painter.setPen(QtGui.QColor(255, 255, 255))
            painter.setFont(QtGui.QFont('Microsoft JhengHei', _ui_size(18, 12, self.compact_mode), QtGui.QFont.Bold))
            view_text = {'day': '今日', 'week': '本週', 'month': '本月', 'year': '本年'}.get(self.view_mode, '本期')
            painter.drawText(self.rect(), QtCore.Qt.AlignCenter, f'{view_text}\n暫無統計數據')
            return

        painter.setFont(QtGui.QFont('Microsoft JhengHei', _ui_size(14, 11, self.compact_mode), QtGui.QFont.Bold))
        painter.setPen(QtGui.QColor(255, 255, 255))
        date_str = self.current_date.strftime('%Y年%m月%d日')
        painter.drawText(inner_rect.left(), inner_rect.top(), inner_rect.width(), title_height, QtCore.Qt.AlignCenter, date_str)

        total = sum(self.data.values())
        start_angle = 0

        for activity, minutes in self.data.items():
            if minutes <= 0:
                continue
            angle = (minutes / total) * 360 * 16
            color = get_neon_color(activity)

            painter.setBrush(color)
            painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255, 120), 2))
            painter.drawPie(pie_rect, int(start_angle), int(angle))
            start_angle += angle

        painter.setFont(QtGui.QFont('Microsoft JhengHei', _ui_size(10, 8, self.compact_mode), QtGui.QFont.Bold))

        sorted_items = sorted(self.data.items(), key=lambda x: x[1], reverse=True)
        legend_y = legend_start_y
        for idx, (activity, minutes) in enumerate(sorted_items):
            if minutes <= 0:
                continue
            color = get_neon_color(activity)

            painter.setBrush(color)
            painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255, 200), 1))
            painter.drawRect(QtCore.QRectF(legend_x, legend_y + 4, legend_swatch, legend_swatch))

            painter.setPen(QtGui.QColor(255, 255, 255))
            label_text = f'{activity} {minutes}m'
            painter.drawText(int(legend_x + legend_swatch + 6), legend_y, legend_width - legend_swatch - 6, legend_item_height,
                             QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, label_text)
            legend_y += legend_item_height


class PomodoroController(QtCore.QObject):
    updated = QtCore.pyqtSignal(int, float, bool, str)
    alarmStarted = QtCore.pyqtSignal()
    alarmStopped = QtCore.pyqtSignal()
    sessionRecorded = QtCore.pyqtSignal(str, int, str)
    pieChartUpdateRequested = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.work_minutes = 25
        self.total_seconds = self.work_minutes * 60
        self.remaining_seconds = self.total_seconds
        self.stopwatch_mode = False
        self.running = False
        self.activity_text = '讀書中'
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self._tick)
        try:
            self.player = QtMultimedia.QMediaPlayer()
            self.player.setVolume(50)
        except Exception:
            self.player = None
        self._music_map = self._find_music_files()
        self._music_file = None
        self._session_log_file = os.path.join(os.path.dirname(__file__), 'session_records.json')

    def _emit(self):
        progress = 0.0
        if (not self.stopwatch_mode) and self.total_seconds > 0:
            progress = (self.total_seconds - self.remaining_seconds) / self.total_seconds
        self.updated.emit(self.remaining_seconds, progress, self.running, self.activity_text)

    def _tick(self):
        if self.stopwatch_mode:
            self.remaining_seconds += 1
            self._emit()
            return
        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1
            self._emit()
            if self.remaining_seconds == 0:
                self._emit()
                try:
                    self._on_finish()
                except Exception:
                    pass
                self.stop(record_session=False)
        else:
            self.stop(record_session=False)

    def _on_finish(self):
        try:
            self._record_session(self.total_seconds, '計時器')
            try:
                self._stop_music()
            except Exception:
                pass
            self.alarmStarted.emit()
            self.pieChartUpdateRequested.emit()
        except Exception:
            pass

    def stop_alarm(self):
        try:
            self._stop_music()
        except Exception:
            pass
        try:
            self.alarmStopped.emit()
        except Exception:
            pass

    def _record_session(self, seconds, mode_name):
        try:
            seconds_int = max(0, int(seconds))
            self.sessionRecorded.emit(self.activity_text, seconds_int, mode_name)
            data = []
            if os.path.isfile(self._session_log_file):
                try:
                    with open(self._session_log_file, 'r', encoding='utf-8') as f:
                        loaded = json.load(f)
                    if isinstance(loaded, list):
                        data = loaded
                except Exception:
                    data = []
            data.append({
                'timestamp': QtCore.QDateTime.currentDateTime().toString(QtCore.Qt.ISODate),
                'status': self.activity_text,
                'seconds': seconds_int,
                'mode': mode_name,
            })
            with open(self._session_log_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _find_music_files(self):
        res = {}
        try:
            base = os.path.join(os.path.dirname(__file__), 'assets', 'music')
            if not os.path.isdir(base):
                return res
            for fn in os.listdir(base):
                if fn.lower().endswith('.mp3'):
                    path = os.path.join(base, fn)
                    res[fn] = path
            if 'remiru_movie.mp3' in res:
                res['讀書中'] = res['remiru_movie.mp3']
                res['修習中'] = res['remiru_movie.mp3']
        except Exception:
            return res
        return res

    def _play_music(self):
        if not self.player:
            return
        music_path = None
        try:
            if isinstance(self._music_map, dict):
                music_path = self._music_map.get(self.activity_text)
                if not music_path:
                    for k, v in self._music_map.items():
                        if k not in ('讀書中', '修習中') and not k.endswith('.mp3'):
                            continue
                        if k.lower().endswith('.mp3'):
                            music_path = v
                            break
                    if not music_path:
                        vals = list(self._music_map.values())
                        music_path = vals[0] if vals else None
        except Exception:
            music_path = None

        if not music_path:
            return
        try:
            url = QtCore.QUrl.fromLocalFile(music_path)
            content = QtMultimedia.QMediaContent(url)
            self.player.setMedia(content)
            self.player.play()
        except Exception:
            pass

    def _stop_music(self):
        try:
            if self.player:
                self.player.stop()
        except Exception:
            pass

    def set_work_minutes(self, minutes):
        prev_stopwatch_mode = self.stopwatch_mode
        minutes_int = max(0, int(minutes))
        self.work_minutes = minutes_int
        self.stopwatch_mode = (minutes_int == 0)
        self.total_seconds = self.work_minutes * 60
        if not self.running:
            self.remaining_seconds = 0 if self.stopwatch_mode else self.total_seconds
        elif self.stopwatch_mode and not prev_stopwatch_mode:
            self.remaining_seconds = 0
        elif (not self.stopwatch_mode) and prev_stopwatch_mode:
            self.remaining_seconds = self.total_seconds
        self._emit()

    def set_activity(self, text):
        self.activity_text = text
        self._emit()

    def start(self):
        if not self.running:
            self.running = True
            self.timer.start(1000)
            self._emit()
            try:
                self._play_music()
            except Exception:
                pass

    def stop(self, record_session=False):
        if self.running:
            if self.stopwatch_mode and self.remaining_seconds > 0:
                self._record_session(self.remaining_seconds, '秒錶')
                self.pieChartUpdateRequested.emit()
        self.running = False
        self.timer.stop()
        self._emit()
        try:
            self._stop_music()
        except Exception:
            pass

    def toggle(self):
        if self.running:
            self.stop(record_session=True)
        else:
            self.start()

    def reset(self):
        self.stop(record_session=False)
        self.remaining_seconds = 0 if self.stopwatch_mode else self.total_seconds
        self._emit()


class PomodoroPanel(QtWidgets.QFrame):
    def __init__(self, controller=None, compact_mode=False, parent=None):
        super().__init__(parent)
        self.compact_mode = compact_mode
        self.controller = controller or PomodoroController(self)
        self._add_status_label = '新增...'
        self._status_defaults = ['讀書中', '休息中']
        self._status_file = os.path.join(os.path.dirname(__file__), 'status_options.json')
        self._status_options = self._load_status_options()
        self._view_mode = 'day'
        self.daily_allocations = {}
        self.viewing_date = datetime.now().date()
        self._session_records_file = os.path.join(os.path.dirname(__file__), 'session_records.json')
        self._last_work_minutes = 25
        self._build_ui()
        self.set_active(0)
        self.controller.updated.connect(self._sync_controls)
        self.controller.sessionRecorded.connect(self._on_session_recorded)
        self.controller.pieChartUpdateRequested.connect(self._refresh_pie_chart)
        self.controller.reset()

    def _build_ui(self):
        self.setObjectName('pomodoroCore')
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        form = QtWidgets.QGridLayout()
        time_label = QtWidgets.QLabel('工作時間(分鐘)')
        time_label.setStyleSheet(f'font-size: {_ui_size(14, 12, self.compact_mode)}pt; font-weight: 700;')
        form.addWidget(time_label, 0, 0)
        self.work_input = QtWidgets.QSpinBox()
        self.work_input.setRange(0, 180)
        self.work_input.setValue(25)
        self.work_input.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.work_input.setMinimumHeight(88 if self.compact_mode else 96)
        self.work_input.setStyleSheet(f'font-size: {_ui_size(42, 34, self.compact_mode)}px; font-weight: 700;')
        form.addWidget(self.work_input, 0, 1)
        minute_text = QtWidgets.QLabel('MIN')
        minute_text.setStyleSheet(f'font-size: {_ui_size(20, 16, self.compact_mode)}px; font-weight: 700;')
        form.addWidget(minute_text, 0, 2)
        form.setColumnStretch(0, 1)
        form.setColumnStretch(1, 2)
        form.setColumnStretch(2, 1)
        layout.addLayout(form)

        btn_row = QtWidgets.QHBoxLayout()
        btn_row.setSpacing(10)
        self.toggle_btn = QtWidgets.QPushButton('開始')
        self.reset_btn = QtWidgets.QPushButton('重開')
        btn_style = (
            f"font-size: {_ui_size(24, 20, self.compact_mode)}px; font-weight: 800; background: rgba(7,16,29,205); "
            "border:1px solid rgba(117,220,255,80); color: #e6fbff; border-radius:12px; "
            "padding: 10px;"
        )
        btn_hover_pressed = (
            "QPushButton:hover { background: rgba(33, 62, 95, 235); border: 1px solid rgba(168, 241, 255, 160); }"
            "QPushButton:pressed { background: rgba(0, 200, 255, 150); border: 2px solid rgba(0, 255, 200, 255); }"
        )
        for button in (self.toggle_btn, self.reset_btn):
            button.setMinimumHeight(100 if self.compact_mode else 112)
            button.setStyleSheet(btn_style + btn_hover_pressed)
        btn_row.addWidget(self.toggle_btn)
        btn_row.addWidget(self.reset_btn)
        layout.addLayout(btn_row)

        mode_row = QtWidgets.QHBoxLayout()
        mode_row.setSpacing(8)
        self.mode_combo = QtWidgets.QComboBox()
        self.mode_combo.addItems(self._status_options)
        self.mode_combo.addItem(self._add_status_label)
        self.mode_combo.setMinimumHeight(56 if self.compact_mode else 62)
        self.mode_combo.setStyleSheet(f'background: rgba(7,16,29,205); color: #effcff; padding: 8px; border-radius: 8px; font-size:{_ui_size(16, 14, self.compact_mode)}px;')
        mode_row.addWidget(self.mode_combo, 1)
        self.mode_delete_btn = QtWidgets.QPushButton('-')
        self.mode_delete_btn.setFixedSize(56 if self.compact_mode else 62, 56 if self.compact_mode else 62)
        self.mode_delete_btn.setStyleSheet(f'font-size: {_ui_size(28, 22, self.compact_mode)}px; font-weight: 900; background: rgba(7,16,29,205); border:1px solid rgba(117,220,255,80); color: #e6fbff; border-radius:12px;')
        mode_row.addWidget(self.mode_delete_btn)
        layout.addLayout(mode_row)

        stats_row = QtWidgets.QHBoxLayout()
        stats_row.setSpacing(8)
        self.stats_buttons = []
        button_styles_unchecked = (
            f'font-size: {_ui_size(18, 16, self.compact_mode)}px; font-weight: 800; background: rgba(7,16,29,205); '
            'border:1px solid rgba(117,220,255,80); color: #e6fbff; border-radius:12px;'
        )
        button_styles_checked = (
            f'font-size: {_ui_size(18, 16, self.compact_mode)}px; font-weight: 800; background: rgba(0,255,150,100); '
            'border:2px solid rgba(0,255,150,255); color: #000000; border-radius:12px;'
        )
        button = QtWidgets.QPushButton('當天')
        button.setMinimumHeight(48 if self.compact_mode else 54)
        button.setStyleSheet(button_styles_unchecked + f'\nQPushButton:checked {{ {button_styles_checked} }}')
        button.setCheckable(True)
        button.setChecked(True)
        stats_row.addWidget(button)
        self.stats_buttons.append(button)
        stats_row.addStretch(1)
        layout.addLayout(stats_row)

        self.pie_container = QtWidgets.QFrame()
        self.pie_container.setStyleSheet('background: rgba(7,16,29,180); border: 1px solid rgba(0,255,200,60); border-radius: 12px;')
        self.pie_container.setMinimumHeight(640 if self.compact_mode else 860)
        self.pie_container.hide()
        pie_layout = QtWidgets.QVBoxLayout(self.pie_container)
        pie_layout.setContentsMargins(8, 8, 8, 8)
        pie_layout.setSpacing(8)

        nav_row = QtWidgets.QHBoxLayout()
        nav_row.setSpacing(6)

        self.date_prev_btn = QtWidgets.QPushButton('◀ 前一天')
        self.date_prev_btn.setMinimumSize(116 if self.compact_mode else 128, 36)
        self.date_prev_btn.setMaximumWidth(116 if self.compact_mode else 128)
        self.date_prev_btn.setFont(QtGui.QFont('Microsoft JhengHei', _ui_size(20, 16, self.compact_mode), QtGui.QFont.Bold))
        self.date_prev_btn.setStyleSheet(f'padding: 5px 12px; font-size: {_ui_size(20, 16, self.compact_mode)}px; font-weight: 700; background: rgba(0,150,255,80); border: 1px solid rgba(0,150,255,150); color: #fff; border-radius: 7px;')
        nav_row.addWidget(self.date_prev_btn)

        self.date_display = QtWidgets.QLabel('今日')
        self.date_display.setAlignment(QtCore.Qt.AlignCenter)
        self.date_display.setStyleSheet(f'font-size: {_ui_size(20, 16, self.compact_mode)}px; font-weight: 700; color: #ffffff;')
        nav_row.addWidget(self.date_display, 1)

        self.date_next_btn = QtWidgets.QPushButton('後一天 ▶')
        self.date_next_btn.setMinimumSize(116 if self.compact_mode else 128, 36)
        self.date_next_btn.setMaximumWidth(116 if self.compact_mode else 128)
        self.date_next_btn.setFont(QtGui.QFont('Microsoft JhengHei', _ui_size(20, 16, self.compact_mode), QtGui.QFont.Bold))
        self.date_next_btn.setStyleSheet(f'padding: 5px 12px; font-size: {_ui_size(20, 16, self.compact_mode)}px; font-weight: 700; background: rgba(0,150,255,80); border: 1px solid rgba(0,150,255,150); color: #fff; border-radius: 7px;')
        nav_row.addWidget(self.date_next_btn)

        pie_layout.addLayout(nav_row)

        self.daily_pie_chart = DailyPieChart(compact_mode=self.compact_mode)
        self.daily_pie_chart.setMinimumHeight(560 if self.compact_mode else 820)
        pie_layout.addWidget(self.daily_pie_chart, 1)
        layout.addWidget(self.pie_container, 2)

        self.record_panel = QtWidgets.QFrame()
        self.record_panel.setStyleSheet('background: rgba(7,16,29,180); border: 1px solid rgba(117,220,255,80); border-radius: 16px;')
        record_layout = QtWidgets.QVBoxLayout(self.record_panel)
        record_layout.setContentsMargins(12, 12, 12, 12)
        record_layout.setSpacing(6)
        self.record_title = QtWidgets.QLabel('本次紀錄')
        self.record_title.setAlignment(QtCore.Qt.AlignCenter)
        self.record_title.setStyleSheet(f'font-size: {_ui_size(16, 14, self.compact_mode)}px; color: #ffffff; font-weight: 700;')
        self.record_text = QtWidgets.QLabel('尚未產生紀錄')
        self.record_text.setAlignment(QtCore.Qt.AlignCenter)
        self.record_text.setWordWrap(True)
        self.record_text.setStyleSheet(f'font-size: {_ui_size(36, 28, self.compact_mode)}px; font-weight: 900; color: #ffffff;')
        record_layout.addWidget(self.record_title)
        record_layout.addWidget(self.record_text)
        layout.addWidget(self.record_panel, 1)

        self.toggle_btn.clicked.connect(self._toggle_pomodoro)
        self.reset_btn.clicked.connect(self._reset_pomodoro)
        self.mode_combo.currentTextChanged.connect(self._on_mode_combo_changed)
        self.mode_delete_btn.clicked.connect(self._delete_current_status)
        self.date_prev_btn.clicked.connect(self._on_date_prev)
        self.date_next_btn.clicked.connect(self._on_date_next)
        self.stats_buttons[0].clicked.connect(self._on_show_today)
        self._view_mode = 'day'

    def _load_status_options(self):
        options = list(self._status_defaults)
        try:
            if os.path.isfile(self._status_file):
                with open(self._status_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                loaded = data.get('statuses', []) if isinstance(data, dict) else []
                for item in loaded:
                    if isinstance(item, str):
                        text = self._normalize_status_text(item)
                        if text == '形成解析中':
                            text = '讀書中'
                        if text and text not in options:
                            options.append(text)
        except Exception:
            pass
        return options

    def _normalize_status_text(self, text):
        t = (text or '').strip()
        if not t:
            return ''
        if t == self._add_status_label:
            return t
        if not t.endswith('中'):
            t = f'{t}中'
        return t

    def _save_status_options(self):
        try:
            payload = {'statuses': self._status_options}
            with open(self._status_file, 'w', encoding='utf-8') as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _rebuild_mode_combo(self):
        self.mode_combo.blockSignals(True)
        current = self.mode_combo.currentText().strip() if self.mode_combo.count() else ''
        self.mode_combo.clear()
        self.mode_combo.addItems(self._status_options)
        self.mode_combo.addItem(self._add_status_label)
        if current and current in self._status_options:
            self.mode_combo.setCurrentText(current)
        self.mode_combo.blockSignals(False)

    def _on_mode_combo_changed(self, text):
        selected = (text or '').strip()
        if not selected:
            return
        if selected == self._add_status_label:
            value, ok = self._prompt_new_status()
            if not ok:
                restore = getattr(self.controller, 'activity_text', self._status_options[0])
                self.mode_combo.blockSignals(True)
                self.mode_combo.setCurrentText(restore if restore in self._status_options else self._status_options[0])
                self.mode_combo.blockSignals(False)
                return

            new_text = self._normalize_status_text(value)
            if not new_text:
                self.mode_combo.blockSignals(True)
                self.mode_combo.setCurrentText(getattr(self.controller, 'activity_text', self._status_options[0]))
                self.mode_combo.blockSignals(False)
                return
            if new_text == self._add_status_label:
                new_text = f'{new_text}1'
            if new_text not in self._status_options:
                self._status_options.append(new_text)
                self._save_status_options()
            self._rebuild_mode_combo()
            self.mode_combo.blockSignals(True)
            self.mode_combo.setCurrentText(new_text)
            self.mode_combo.blockSignals(False)
            self.controller.set_activity(new_text)
            return

        self.controller.set_activity(selected)

    def _delete_current_status(self):
        current = (self.mode_combo.currentText() or '').strip()
        if not current or current == self._add_status_label:
            return
        if current in self._status_defaults:
            QtWidgets.QMessageBox.information(self, '提示', '預設狀態不可刪除。')
            return
        if current in self._status_options:
            self._status_options.remove(current)
            self._save_status_options()
            self._rebuild_mode_combo()
            fallback = self._status_defaults[0] if self._status_defaults else (self._status_options[0] if self._status_options else '')
            if fallback:
                self.mode_combo.blockSignals(True)
                self.mode_combo.setCurrentText(fallback)
                self.mode_combo.blockSignals(False)
                self.controller.set_activity(fallback)

    def _prompt_new_status(self):
        dialog = QtWidgets.QInputDialog(self)
        dialog.setWindowTitle('新增狀態')
        dialog.setLabelText('請輸入新的狀態名稱：')
        dialog.setTextValue('')
        dialog.setStyleSheet(
            'QLabel { color: #111111; }'
            'QLineEdit { color: #000000; background: #ffffff; border: 1px solid #888888; padding: 4px; }'
            'QPushButton { color: #111111; background: #f0f0f0; border: 1px solid #999999; padding: 6px 10px; }'
        )
        ok = dialog.exec_() == QtWidgets.QDialog.Accepted
        return dialog.textValue(), ok

    def _build_placeholder(self, text):
        label = QtWidgets.QLabel(text)
        label.setAlignment(QtCore.Qt.AlignCenter)
        label.setWordWrap(True)
        label.setStyleSheet(f'font-size: {_ui_size(13, 11, self.compact_mode)}pt; color: #bdefff; padding: {12 if self.compact_mode else 16}px;')
        return label

    def _on_show_today(self):
        self._view_mode = 'day'
        self.viewing_date = datetime.now().date()
        self.date_prev_btn.show()
        self.date_next_btn.show()
        self.pie_container.show()
        self._refresh_pie_chart()

    def _on_date_prev(self):
        from datetime import timedelta
        self.viewing_date -= timedelta(days=1)
        self.pie_container.show()
        self._refresh_pie_chart()

    def _on_date_next(self):
        from datetime import timedelta
        self.viewing_date += timedelta(days=1)
        self.pie_container.show()
        self._refresh_pie_chart()

    def _refresh_pie_chart(self):
        self._load_daily_statistics()
        self._update_date_display()
        self.daily_pie_chart.set_data(self.daily_allocations, self.viewing_date, self._view_mode)

    def _update_date_display(self):
        today = datetime.now().date()
        if self._view_mode == 'day':
            if self.viewing_date == today:
                date_text = '今日 ' + self.viewing_date.strftime('%Y年%m月%d日')
            elif self.viewing_date == today - __import__('datetime').timedelta(days=1):
                date_text = '昨日 ' + self.viewing_date.strftime('%Y年%m月%d日')
            elif self.viewing_date == today + __import__('datetime').timedelta(days=1):
                date_text = '明日 ' + self.viewing_date.strftime('%Y年%m月%d日')
            else:
                date_text = self.viewing_date.strftime('%Y年%m月%d日')
        elif self._view_mode == 'week':
            date_text = f'{today.strftime("%Y")} 年 第 {today.isocalendar()[1]} 週'
        elif self._view_mode == 'month':
            date_text = f'{today.strftime("%Y-%m")} 月'
        elif self._view_mode == 'year':
            date_text = f'{today.strftime("%Y")} 年'
        else:
            date_text = '統計'
        self.date_display.setText(date_text)

    def _load_daily_statistics(self):
        self.daily_allocations.clear()
        try:
            if os.path.isfile(self._session_records_file):
                with open(self._session_records_file, 'r', encoding='utf-8') as f:
                    records = json.load(f)
                    if isinstance(records, list):
                        for record in records:
                            if isinstance(record, dict):
                                timestamp_str = record.get('timestamp', '')
                                if not timestamp_str:
                                    continue
                                try:
                                    record_date = datetime.fromisoformat(timestamp_str.split('T')[0]).date()
                                except Exception:
                                    continue

                                should_include = False
                                if self._view_mode == 'day':
                                    should_include = record_date == self.viewing_date
                                elif self._view_mode == 'week':
                                    today = datetime.now().date()
                                    target_week = today.isocalendar()[1]
                                    target_year = today.isocalendar()[0]
                                    record_week = record_date.isocalendar()[1]
                                    record_year = record_date.isocalendar()[0]
                                    should_include = (record_week == target_week and record_year == target_year)
                                elif self._view_mode == 'month':
                                    today = datetime.now().date()
                                    should_include = (record_date.year == today.year and record_date.month == today.month)
                                elif self._view_mode == 'year':
                                    today = datetime.now().date()
                                    should_include = record_date.year == today.year

                                if should_include:
                                    status = record.get('status', '')
                                    seconds = record.get('seconds', 0)
                                    if status and seconds > 0:
                                        minutes = int(round(seconds / 60.0))
                                        self.daily_allocations[status] = self.daily_allocations.get(status, 0) + minutes
        except Exception:
            pass

    def _on_session_recorded(self, status_text, seconds, mode_name):
        status_text = self._normalize_status_text(status_text)
        if status_text == '讀書中':
            status_text = '讀書'
        if status_text == '休息中':
            status_text = '休息'
        minutes = max(1, int(round(float(seconds) / 60.0))) if seconds > 0 else 0
        self.record_text.setText(f'{status_text}\n{minutes} 分鐘')
        self._refresh_pie_chart()

    def _toggle_pomodoro(self):
        current_value = self.work_input.value()
        if current_value != self._last_work_minutes:
            self.controller.set_work_minutes(current_value)
            self._last_work_minutes = current_value
            self.record_text.setText('尚未產生紀錄')
        self.controller.toggle()

    def _reset_pomodoro(self):
        current_value = self.work_input.value()
        self.controller.set_work_minutes(current_value)
        self._last_work_minutes = current_value
        self.controller.reset()

    def _sync_controls(self, remaining_seconds, progress, running, activity_text):
        self.toggle_btn.setText('暫停' if running else '開始')
        normalized_activity = self._normalize_status_text(activity_text)
        if normalized_activity and normalized_activity not in self._status_options and normalized_activity != self._add_status_label:
            self._status_options.append(normalized_activity)
            self._save_status_options()
            self._rebuild_mode_combo()
        idx = self.mode_combo.findText(normalized_activity)
        if idx >= 0 and self.mode_combo.currentIndex() != idx:
            self.mode_combo.blockSignals(True)
            self.mode_combo.setCurrentIndex(idx)
            self.mode_combo.blockSignals(False)

    def set_active(self, index):
        if not hasattr(self, 'buttons'):
            return
        for i, button in enumerate(self.buttons):
            button.setChecked(i == index)
        self.editor_stack.setCurrentIndex(index)
        hints = [
            '',
            '待辦清單 尚未接上',
            '進度追蹤 尚未接上',
            '行事曆 尚未接上',
        ]
        self.menu_hint.setText(hints[index])
