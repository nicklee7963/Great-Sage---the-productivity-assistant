import calendar
import json
import os
from datetime import datetime

from PyQt5 import QtWidgets, QtCore, QtGui


def _ui_size(normal_size, compact_size, compact_mode):
    return compact_size if compact_mode else normal_size


class CalendarEventStore:
    def __init__(self, storage_path=None):
        self.storage_path = storage_path or os.path.join(os.path.dirname(__file__), 'calendar_events.json')
        self._events_by_date = {}
        self.load()

    def _date_key(self, date_value):
        if isinstance(date_value, str):
            return date_value
        return date_value.isoformat()

    def _normalize_time(self, time_text):
        candidate = (time_text or '').strip()
        if not candidate:
            return ''
        for time_format in ('HH:mm', 'H:mm', 'H:m'):
            parsed = QtCore.QTime.fromString(candidate, time_format)
            if parsed.isValid():
                return parsed.toString('HH:mm')
        return ''

    def _normalize_text(self, task_text):
        return (task_text or '').strip()

    def load(self):
        self._events_by_date = {}
        try:
            if os.path.isfile(self.storage_path):
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                if isinstance(loaded, dict):
                    for date_key, events in loaded.items():
                        normalized_events = []
                        if isinstance(events, list):
                            for event in events:
                                if not isinstance(event, dict):
                                    continue
                                time_value = self._normalize_time(event.get('time', ''))
                                task_value = self._normalize_text(event.get('task', event.get('text', '')))
                                if time_value and task_value:
                                    normalized_events.append({'time': time_value, 'task': task_value})
                        self._events_by_date[date_key] = sorted(normalized_events, key=lambda item: item['time'])
        except Exception:
            self._events_by_date = {}

    def save(self):
        try:
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(self._events_by_date, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def events_for_date(self, date_value):
        key = self._date_key(date_value)
        return [dict(event) for event in self._events_by_date.get(key, [])]

    def has_events_for_date(self, date_value):
        key = self._date_key(date_value)
        return bool(self._events_by_date.get(key, []))

    def set_events_for_date(self, date_value, events):
        key = self._date_key(date_value)
        normalized = []
        for event in events:
            if not isinstance(event, dict):
                continue
            time_value = self._normalize_time(event.get('time', ''))
            task_value = self._normalize_text(event.get('task', event.get('text', '')))
            if time_value and task_value:
                normalized.append({'time': time_value, 'task': task_value})
        self._events_by_date[key] = sorted(normalized, key=lambda item: item['time'])
        self.save()

    def add_event(self, date_value, time_text, task_text):
        time_value = self._normalize_time(time_text)
        task_value = self._normalize_text(task_text)
        if not time_value or not task_value:
            return False
        key = self._date_key(date_value)
        self._events_by_date.setdefault(key, []).append({'time': time_value, 'task': task_value})
        self._events_by_date[key] = sorted(self._events_by_date[key], key=lambda item: item['time'])
        self.save()
        return True

    def update_event(self, date_value, index, time_text, task_text):
        events = self.events_for_date(date_value)
        if index < 0 or index >= len(events):
            return False
        time_value = self._normalize_time(time_text)
        task_value = self._normalize_text(task_text)
        if not time_value or not task_value:
            return False
        events[index] = {'time': time_value, 'task': task_value}
        self.set_events_for_date(date_value, events)
        return True

    def delete_event(self, date_value, index):
        events = self.events_for_date(date_value)
        if index < 0 or index >= len(events):
            return False
        del events[index]
        self.set_events_for_date(date_value, events)
        return True


class CalendarPanel(QtWidgets.QFrame):
    dateOpened = QtCore.pyqtSignal(object)
    backRequested = QtCore.pyqtSignal()
    eventsChanged = QtCore.pyqtSignal(object)

    def __init__(self, compact_mode=False, parent=None):
        super().__init__(parent)
        self.compact_mode = compact_mode
        self.store = CalendarEventStore()
        today = datetime.now().date()
        self._current_date = today.replace(day=1)
        self._selected_date = today
        self._build_ui()
        self.setMinimumHeight(920 if compact_mode else 1120)
        self.refresh_month(self._current_date)
        self.show_month_view(emit_signal=False)

    def _build_ui(self):
        self.setObjectName('calendarPanel')
        self.setStyleSheet(
            "QFrame#calendarPanel {"
            " background: rgba(7,16,29,205);"
            " border: 1px solid rgba(117,220,255,80);"
            " border-radius: 18px;"
            "}"
            "QLabel { color: #e6fbff; }"
            "QListWidget {"
            " background: rgba(9,18,31,235);"
            " color: #effcff;"
            " border: 1px solid rgba(117,220,255,55);"
            " border-radius: 12px;"
            "}"
            "QLineEdit, QTimeEdit {"
            " background: rgba(9,18,31,235);"
            " color: #effcff;"
            " border: 1px solid rgba(117,220,255,70);"
            " border-radius: 8px;"
            " padding: 6px;"
            "}"
            "QPushButton {"
            " background: rgba(14, 28, 50, 220);"
            " color: #effcff;"
            " border: 1px solid rgba(110, 214, 255, 90);"
            " border-radius: 12px;"
            " padding: 8px 12px;"
            "}"
            "QPushButton:hover { background: rgba(33, 62, 95, 235); border: 1px solid rgba(168, 241, 255, 160); }"
            "QPushButton:pressed { background: rgba(0, 242, 255, 65); color: #000000; }"
        )

        root_layout = QtWidgets.QVBoxLayout(self)
        root_layout.setContentsMargins(16, 16, 16, 16)
        root_layout.setSpacing(12)

        self.title_label = QtWidgets.QLabel('行事曆')
        self.title_label.setAlignment(QtCore.Qt.AlignCenter)
        self.title_label.setStyleSheet(f'font-size: {_ui_size(20, 13, self.compact_mode)}pt; font-weight: 800; letter-spacing: 3px;')
        root_layout.addWidget(self.title_label)

        self.subtitle_label = QtWidgets.QLabel('點日期查看、編輯與移除作息')
        self.subtitle_label.setAlignment(QtCore.Qt.AlignCenter)
        self.subtitle_label.setWordWrap(True)
        self.subtitle_label.setStyleSheet(f'color: #7fdcff; font-size: {_ui_size(11, 8, self.compact_mode)}pt; letter-spacing: 1px;')
        root_layout.addWidget(self.subtitle_label)

        self.stack = QtWidgets.QStackedWidget()
        root_layout.addWidget(self.stack, 1)

        self.month_page = QtWidgets.QWidget()
        self._build_month_page(self.month_page)
        self.stack.addWidget(self.month_page)

        self.editor_page = QtWidgets.QWidget()
        self._build_editor_page(self.editor_page)
        self.stack.addWidget(self.editor_page)

    def _build_month_page(self, page):
        layout = QtWidgets.QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        nav_row = QtWidgets.QHBoxLayout()
        nav_row.setSpacing(8)
        self.month_prev_btn = QtWidgets.QPushButton('◀')
        self.month_prev_btn.setFixedWidth(42 if self.compact_mode else 48)
        self.month_prev_btn.clicked.connect(self._go_previous_month)
        nav_row.addWidget(self.month_prev_btn)

        self.month_label = QtWidgets.QLabel('')
        self.month_label.setAlignment(QtCore.Qt.AlignCenter)
        self.month_label.setStyleSheet(f'font-size: {_ui_size(18, 12, self.compact_mode)}pt; font-weight: 700; color: #dffcff;')
        nav_row.addWidget(self.month_label, 1)

        self.month_next_btn = QtWidgets.QPushButton('▶')
        self.month_next_btn.setFixedWidth(42 if self.compact_mode else 48)
        self.month_next_btn.clicked.connect(self._go_next_month)
        nav_row.addWidget(self.month_next_btn)
        layout.addLayout(nav_row)

        self.grid_frame = QtWidgets.QFrame()
        self.grid_frame.setStyleSheet(
            "QFrame {"
            " background: rgba(9,18,31,235);"
            " border: 1px solid rgba(117,220,255,70);"
            " border-radius: 12px;"
            "}"
        )
        grid_layout = QtWidgets.QGridLayout(self.grid_frame)
        grid_layout.setContentsMargins(8, 8, 8, 8)
        grid_layout.setSpacing(6)

        weekday_names = ['日', '一', '二', '三', '四', '五', '六']
        for column, name in enumerate(weekday_names):
            header = QtWidgets.QLabel(name)
            header.setAlignment(QtCore.Qt.AlignCenter)
            header.setStyleSheet(
                "QLabel {"
                " background: rgba(0,150,255,70);"
                " color: #ffffff;"
                " padding: 6px;"
                " border-radius: 8px;"
                " font-weight: 700;"
                "}"
            )
            header.setMinimumHeight(34 if self.compact_mode else 40)
            header.setFont(QtGui.QFont('Microsoft JhengHei', 10 if self.compact_mode else 12, QtGui.QFont.Bold))
            grid_layout.addWidget(header, 0, column)

        self.day_buttons = []
        button_font = QtGui.QFont('Microsoft JhengHei', 11 if self.compact_mode else 15, QtGui.QFont.Bold)
        for row in range(1, 7):
            for column in range(7):
                button = QtWidgets.QPushButton('')
                button.setFont(button_font)
                button.setCursor(QtCore.Qt.PointingHandCursor)
                button.setMinimumHeight(96 if self.compact_mode else 128)
                button.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
                button.setProperty('dayValue', 0)
                button.clicked.connect(lambda checked=False, b=button: self._on_day_clicked(b))
                grid_layout.addWidget(button, row, column)
                self.day_buttons.append(button)

        layout.addWidget(self.grid_frame, 1)

    def _build_editor_page(self, page):
        layout = QtWidgets.QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        top_row = QtWidgets.QHBoxLayout()
        top_row.setSpacing(8)
        self.back_button = QtWidgets.QPushButton('← 回上頁')
        self.back_button.setMinimumHeight(40 if self.compact_mode else 44)
        self.back_button.clicked.connect(self._on_back_clicked)
        top_row.addWidget(self.back_button, 0, QtCore.Qt.AlignLeft)

        self.detail_date_label = QtWidgets.QLabel('')
        self.detail_date_label.setAlignment(QtCore.Qt.AlignCenter)
        self.detail_date_label.setStyleSheet(f'font-size: {_ui_size(16, 11, self.compact_mode)}pt; font-weight: 800; color: #dffcff;')
        top_row.addWidget(self.detail_date_label, 1)
        layout.addLayout(top_row)

        self.summary_label = QtWidgets.QLabel('08:00 起床\n10:00 上廁所\n')
        self.summary_label.setAlignment(QtCore.Qt.AlignCenter)
        self.summary_label.setWordWrap(True)
        self.summary_label.setStyleSheet(
            f"background: rgba(9,18,31,230); border: 1px solid rgba(117,220,255,60); border-radius: 12px;"
            f"color: #effcff; font-size: {_ui_size(14, 11, self.compact_mode)}pt; font-weight: 700; padding: 12px;"
        )
        self.summary_label.setMinimumHeight(120 if self.compact_mode else 140)
        layout.addWidget(self.summary_label)

        editor_frame = QtWidgets.QFrame()
        editor_frame.setStyleSheet(
            "QFrame {"
            " background: rgba(9,18,31,235);"
            " border: 1px solid rgba(117,220,255,70);"
            " border-radius: 14px;"
            "}"
        )
        editor_layout = QtWidgets.QVBoxLayout(editor_frame)
        editor_layout.setContentsMargins(12, 12, 12, 12)
        editor_layout.setSpacing(8)

        editor_title = QtWidgets.QLabel('編輯作息')
        editor_title.setAlignment(QtCore.Qt.AlignCenter)
        editor_title.setStyleSheet(f'font-size: {_ui_size(16, 11, self.compact_mode)}pt; font-weight: 800;')
        editor_layout.addWidget(editor_title)

        self.event_list = QtWidgets.QListWidget()
        self.event_list.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.event_list.currentRowChanged.connect(self._sync_editor_fields_from_selection)
        editor_layout.addWidget(self.event_list, 1)

        form = QtWidgets.QGridLayout()
        form.setSpacing(8)
        time_label = QtWidgets.QLabel('時間')
        time_label.setStyleSheet(f'font-size: {_ui_size(12, 10, self.compact_mode)}pt; font-weight: 700;')
        form.addWidget(time_label, 0, 0)
        self.time_edit = QtWidgets.QTimeEdit(QtCore.QTime.currentTime())
        self.time_edit.setDisplayFormat('HH:mm')
        self.time_edit.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.time_edit.setMinimumHeight(38 if self.compact_mode else 42)
        form.addWidget(self.time_edit, 0, 1)

        task_label = QtWidgets.QLabel('要做什麼')
        task_label.setStyleSheet(f'font-size: {_ui_size(12, 10, self.compact_mode)}pt; font-weight: 700;')
        form.addWidget(task_label, 1, 0)
        self.task_edit = QtWidgets.QLineEdit()
        self.task_edit.setPlaceholderText('例如：起床、上廁所、讀書')
        self.task_edit.setMinimumHeight(38 if self.compact_mode else 42)
        form.addWidget(self.task_edit, 1, 1)
        form.setColumnStretch(0, 0)
        form.setColumnStretch(1, 1)
        editor_layout.addLayout(form)

        button_row = QtWidgets.QHBoxLayout()
        button_row.setSpacing(6)
        self.add_btn = QtWidgets.QPushButton('加入')
        self.update_btn = QtWidgets.QPushButton('更新')
        self.delete_btn = QtWidgets.QPushButton('移除')
        for button in (self.add_btn, self.update_btn, self.delete_btn):
            button.setMinimumHeight(40 if self.compact_mode else 44)
            button_row.addWidget(button)
        editor_layout.addLayout(button_row)

        self.add_btn.clicked.connect(self._add_event)
        self.update_btn.clicked.connect(self._update_event)
        self.delete_btn.clicked.connect(self._delete_event)

        layout.addWidget(editor_frame, 1)

    def _go_previous_month(self):
        year = self._current_date.year
        month = self._current_date.month - 1
        if month < 1:
            month = 12
            year -= 1
        self.refresh_month(datetime(year, month, 1).date())

    def _go_next_month(self):
        year = self._current_date.year
        month = self._current_date.month + 1
        if month > 12:
            month = 1
            year += 1
        self.refresh_month(datetime(year, month, 1).date())

    def _on_day_clicked(self, button):
        day_value = button.property('dayValue')
        if not day_value:
            return
        try:
            selected_date = datetime(self._current_date.year, self._current_date.month, int(day_value)).date()
        except Exception:
            return
        self._selected_date = selected_date
        self.show_editor_view(selected_date)
        self.dateOpened.emit(selected_date)

    def _on_back_clicked(self):
        self.show_month_view(emit_signal=True)

    def is_detail_view(self):
        return self.stack.currentWidget() == self.editor_page

    def selected_date(self):
        return self._selected_date

    def get_events_for_selected_date(self):
        return self.store.events_for_date(self._selected_date)

    def show_month_view(self, emit_signal=False):
        self.stack.setCurrentWidget(self.month_page)
        self.refresh_month(self._current_date)
        if emit_signal:
            self.backRequested.emit()

    def show_editor_view(self, selected_date=None):
        if selected_date is not None:
            self._selected_date = selected_date
        self._current_date = self._selected_date.replace(day=1)
        self.stack.setCurrentWidget(self.editor_page)
        self.detail_date_label.setText(self._selected_date.strftime('%Y年%m月%d日'))
        self._refresh_editor_view()

    def refresh_month(self, date_value=None):
        if date_value is not None:
            self._current_date = datetime(date_value.year, date_value.month, 1).date()
        year = self._current_date.year
        month = self._current_date.month
        self.month_label.setText(f'{year}年{month:02d}月')

        month_calendar = calendar.Calendar(firstweekday=6).monthdayscalendar(year, month)
        flattened_days = []
        for week in month_calendar:
            flattened_days.extend(week)
        flattened_days.extend([0] * (42 - len(flattened_days)))

        for index, button in enumerate(self.day_buttons):
            day = flattened_days[index] if index < len(flattened_days) else 0
            button.setProperty('dayValue', day)
            if day == 0:
                button.setText('')
                button.setEnabled(False)
                button.setStyleSheet(
                    "QPushButton { background: rgba(7,16,29,90); color: rgba(255,255,255,80); border: 1px solid rgba(117,220,255,25); border-radius: 10px; padding: 4px; }"
                )
                continue

            button.setEnabled(True)
            button.setText(str(day))
            item_date = datetime(year, month, day).date()
            has_events = self.store.has_events_for_date(item_date)
            styles = [
                "QPushButton {",
                " background: rgba(9,18,31,140);",
                " color: #effcff;",
                " border: 1px solid rgba(117,220,255,55);",
                " border-radius: 10px;",
                " padding: 4px;",
                "}",
            ]
            if has_events:
                styles.append("QPushButton { background: rgba(0,150,255,95); color: #ffffff; border: 1px solid rgba(0,242,255,180); }")
            if item_date == self._selected_date:
                styles.append("QPushButton { background: rgba(0,242,255,130); color: #000000; border: 2px solid rgba(0,242,255,240); }")
            styles.append("QPushButton:hover { background: rgba(0,150,255,85); border: 1px solid rgba(117,220,255,130); }")
            styles.append("QPushButton:pressed { background: rgba(0,242,255,115); color: #000000; }")
            button.setStyleSheet("\n".join(styles))

    def _refresh_editor_view(self):
        events = self.get_events_for_selected_date()
        self.event_list.blockSignals(True)
        self.event_list.clear()
        if not events:
            item = QtWidgets.QListWidgetItem('這一天還沒有安排')
            item.setFlags(QtCore.Qt.NoItemFlags)
            self.event_list.addItem(item)
            self.summary_label.setText('這一天還沒有安排')
        else:
            lines = []
            for event in events:
                time_text = event.get('time', '')
                task_text = event.get('task', '')
                self.event_list.addItem(f'{time_text}  {task_text}')
                lines.append(f'{time_text} {task_text}')
            self.summary_label.setText('\n'.join(lines))
            self.event_list.setCurrentRow(0)
        self.event_list.blockSignals(False)
        self._sync_editor_fields_from_selection()

    def _sync_editor_fields_from_selection(self, row=None):
        if row is None:
            row = self.event_list.currentRow()
        events = self.get_events_for_selected_date()
        if row is None or row < 0 or row >= len(events):
            self.time_edit.setTime(QtCore.QTime.currentTime())
            self.task_edit.clear()
            return
        event = events[row]
        parsed_time = QtCore.QTime.fromString(event.get('time', ''), 'HH:mm')
        if parsed_time.isValid():
            self.time_edit.setTime(parsed_time)
        self.task_edit.setText(event.get('task', ''))

    def _add_event(self):
        if self.store.add_event(self._selected_date, self.time_edit.time().toString('HH:mm'), self.task_edit.text()):
            self._refresh_editor_view()
            self.eventsChanged.emit(self._selected_date)

    def _update_event(self):
        row = self.event_list.currentRow()
        if self.store.update_event(self._selected_date, row, self.time_edit.time().toString('HH:mm'), self.task_edit.text()):
            self._refresh_editor_view()
            self.eventsChanged.emit(self._selected_date)

    def _delete_event(self):
        row = self.event_list.currentRow()
        if self.store.delete_event(self._selected_date, row):
            self._refresh_editor_view()
            self.eventsChanged.emit(self._selected_date)
