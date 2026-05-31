"""
大賢者（Great Sage）- 寵物聊天模組

本模組提供 AI 聊天功能，使用 Google Gemini API：
  • 自動從書單、行事曆獲取上下文
  • 生成自然、温暖的寵物對話
  • 背景執行緒避免阻斷 GUI
  • 定期主動與使用者互動
"""

import html
import json
import os
import random
import threading
import time
from datetime import datetime
from pathlib import Path

import requests
from PyQt5 import QtCore, QtGui, QtWidgets


DEFAULT_GEMINI_MODEL = 'gemini-2.0-flash'
CHAT_PROMPT_MIN_MS = 90_000
CHAT_PROMPT_MAX_MS = 240_000
CHAT_PROMPT_TIMEOUT_MS = 5_000
CHAT_RECENT_RESTORE_MS = 15_000
HOVER_POLL_MS = 40
STARTUP_CHAT_DELAY_MS = 1200
CHAT_SYSTEM_PROMPT = (
    '你是一隻可愛、溫和、會主動關心主人的小寵物。'
    '請用繁體中文、簡短自然的口吻回覆，不要太長，不要提到系統提示。'
)

LOCAL_OPENERS = [
    '我剛偷看了你的行程，今天有點事情要記得喔。',
    '我翻了一下你的待辦和行事曆，要不要先處理最重要的那件事？',
    '今天我看到你有安排，先休息一下還是先衝一波？',
    '我發現你的資料裡有幾個提醒，要不要我幫你整理一下？',
    '我想跟你聊聊今天要做什麼，先看書單還是先看行事曆？',
]

BOOK_TOPIC_OPENERS = [
    '你的書單裡有 {topic}，今天要不要先讀一點？',
    '我看到你把 {topic} 放進書單了，這本現在適合開讀嗎？',
    '如果今天時間不多，我猜你會想先碰 {topic}。',
]

CALENDAR_TOPIC_OPENERS = [
    '你 {time} 有「{task}」，我先提醒你一下。',
    '今天行事曆裡有「{task}」，時間是 {time}，別忘了。',
    '我看見 {time} 有個待辦叫「{task}」，要不要先準備？',
]


def _default_settings_path():
    return Path(__file__).resolve().with_name('pet_settings.json')


def load_saved_api_key(settings_path=None):
    path = Path(settings_path) if settings_path else _default_settings_path()
    if not path.exists():
        return ''
    try:
        with path.open('r', encoding='utf-8') as handle:
            payload = json.load(handle)
    except Exception:
        return ''
    return str(payload.get('gemini_api_key', '') or '').strip()


def save_api_key(api_key, settings_path=None):
    path = Path(settings_path) if settings_path else _default_settings_path()
    payload = {'gemini_api_key': (api_key or '').strip()}
    try:
        with path.open('w', encoding='utf-8') as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
    except Exception:
        return False
    return True


def resolve_gemini_api_key(settings_path=None, prompt_if_missing=True):
    env_key = os.environ.get('GEMINI_API_KEY', '').strip()
    if env_key:
        return env_key

    saved_key = load_saved_api_key(settings_path=settings_path)
    if saved_key:
        return saved_key

    if not prompt_if_missing:
        return ''

    try:
        entered_key = input('請輸入 Gemini API Key（直接按 Enter 跳過聊天功能）: ').strip()
    except EOFError:
        entered_key = ''

    if entered_key:
        save_api_key(entered_key, settings_path=settings_path)
    return entered_key


def _safe_json_load(path, default):
    try:
        with Path(path).open('r', encoding='utf-8') as handle:
            return json.load(handle)
    except Exception:
        return default


def load_book_topics(base_dir=None):
    base_path = Path(base_dir) if base_dir else Path(__file__).resolve().parent
    payload = _safe_json_load(base_path / 'book_categories.json', [])
    if not isinstance(payload, list):
        return []
    return [str(item).strip() for item in payload if str(item).strip()]


def load_calendar_events(base_dir=None):
    base_path = Path(base_dir) if base_dir else Path(__file__).resolve().parent
    payload = _safe_json_load(base_path / 'calendar_events.json', {})
    if not isinstance(payload, dict):
        return []

    events = []
    for date_text, items in payload.items():
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            time_text = str(item.get('time', '') or '').strip()
            task_text = str(item.get('task', '') or '').strip()
            if task_text:
                events.append({'date': str(date_text), 'time': time_text, 'task': task_text})
    return events


def build_local_prompt(base_dir=None):
    book_topics = load_book_topics(base_dir=base_dir)
    calendar_events = load_calendar_events(base_dir=base_dir)
    choices = []

    if book_topics:
        topic = random.choice(book_topics)
        template = random.choice(BOOK_TOPIC_OPENERS)
        choices.append(template.format(topic=topic))

    if calendar_events:
        upcoming = random.choice(calendar_events)
        choices.append(random.choice(CALENDAR_TOPIC_OPENERS).format(
            time=upcoming.get('time') or '某個時間',
            task=upcoming.get('task') or '待辦事項',
        ))

    choices.extend(LOCAL_OPENERS)
    return random.choice(choices)


class GeminiChatClient:
    def __init__(self, api_key, model=DEFAULT_GEMINI_MODEL, timeout=30):
        self.api_key = (api_key or '').strip()
        self.model = model
        self.timeout = timeout

    @property
    def enabled(self):
        return bool(self.api_key)

    def generate(self, prompt, history=None):
        if not self.enabled:
            return None

        contents = []
        for role, text in (history or []):
            if not text:
                continue
            contents.append({'role': role, 'parts': [{'text': text}]})
        contents.append({'role': 'user', 'parts': [{'text': prompt}]})

        payload = {
            'systemInstruction': {'parts': [{'text': CHAT_SYSTEM_PROMPT}]},
            'contents': contents,
            'generationConfig': {
                'temperature': 0.9,
                'topP': 0.95,
                'maxOutputTokens': 180,
            },
        }
        url = f'https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent'
        try:
            response = requests.post(url, params={'key': self.api_key}, json=payload, timeout=self.timeout)
            if response.status_code == 429:
                import sys
                print('Gemini API quota exceeded: Your API key has reached the usage limit.', file=sys.stderr)
                return None
            response.raise_for_status()
            data = response.json()
            candidates = data.get('candidates') or []
            if not candidates:
                return None
            parts = ((candidates[0].get('content') or {}).get('parts')) or []
            text = ''.join(part.get('text', '') for part in parts).strip()
            return text or None
        except requests.exceptions.RequestException as e:
            import sys
            print(f'Gemini API error: {e}', file=sys.stderr)
            return None


class _AsyncWorker(QtCore.QObject):
    finished = QtCore.pyqtSignal(object, object)

    def __init__(self, func):
        super().__init__()
        self.func = func

    @QtCore.pyqtSlot()
    def run(self):
        try:
            result = self.func()
            self.finished.emit(result, None)
        except Exception as exc:
            self.finished.emit(None, exc)


class ChatPromptBubble(QtWidgets.QFrame):
    submitted = QtCore.pyqtSignal(str)
    clicked = QtCore.pyqtSignal()
    closed = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.Tool | QtCore.Qt.WindowStaysOnTopHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setObjectName('chatPromptBubble')
        self._expanded = False

        self.prompt_label = QtWidgets.QLabel(self)
        self.prompt_label.setWordWrap(True)
        self.prompt_label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        self.prompt_label.setStyleSheet('QLabel { color: #999999; font-size: 18px; font-weight: 700; }')

        self.expand_hint = QtWidgets.QLabel('點一下開始回覆')
        self.expand_hint.setStyleSheet('QLabel { color: #999999; font-size: 14px; }')

        self.chat_log = QtWidgets.QScrollArea()
        self.chat_log.setWidgetResizable(True)
        self.chat_log.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.chat_log.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.chat_log.setStyleSheet('QScrollArea { background: transparent; border: none; }')

        self.chat_log_container = QtWidgets.QWidget()
        self.chat_log_container.setObjectName('chatLogContainer')
        self.chat_log_layout = QtWidgets.QVBoxLayout(self.chat_log_container)
        self.chat_log_layout.setContentsMargins(2, 2, 2, 2)
        self.chat_log_layout.setSpacing(8)
        self.chat_log_layout.addStretch(1)
        self.chat_log.setWidget(self.chat_log_container)

        self.input_edit = QtWidgets.QLineEdit()
        self.input_edit.setPlaceholderText('在這裡直接輸入回覆')
        self.input_edit.setMinimumHeight(28)
        self.input_edit.setFont(QtGui.QFont('Arial', 11))

        self.send_button = QtWidgets.QPushButton('送出')
        self.send_button.setMinimumHeight(28)
        self.send_button.setFont(QtGui.QFont('Arial', 12))
        self.close_button = QtWidgets.QPushButton('收起')
        self.close_button.setMinimumHeight(28)
        self.close_button.setFont(QtGui.QFont('Arial', 12))

        input_row = QtWidgets.QHBoxLayout()
        input_row.addWidget(self.input_edit, 1)
        input_row.addWidget(self.send_button)
        input_row.addWidget(self.close_button)

        self.details_widget = QtWidgets.QWidget()
        details_layout = QtWidgets.QVBoxLayout(self.details_widget)
        details_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.setSpacing(10)
        details_layout.addWidget(self.chat_log, 1)
        details_layout.addLayout(input_row)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(8)
        layout.addWidget(self.prompt_label)
        layout.addWidget(self.expand_hint)
        layout.addWidget(self.details_widget)

        self.details_widget.hide()

        self.send_button.clicked.connect(self._submit)
        self.input_edit.returnPressed.connect(self._submit)
        self.close_button.clicked.connect(self.collapse_chat)

        self.setStyleSheet(
            'QFrame#chatPromptBubble { background: rgba(255, 255, 255, 255); '
            'border: 1px solid rgba(180, 180, 180, 200); border-radius: 16px; } '
            'QLineEdit { background: rgba(255, 255, 255, 255); color: #111111; border: 1px solid rgba(180, 180, 180, 200); '
            'border-radius: 10px; padding: 10px; font-size: 11px; }'
            'QPushButton { background: rgba(245, 245, 245, 255); color: #111111; border: 1px solid rgba(180, 180, 180, 200); '
            'border-radius: 10px; padding: 10px 14px; font-weight: 700; font-size: 12px; }'
            'QPushButton:hover { background: rgba(235, 235, 235, 255); }'
        )

    def set_prompt(self, text):
        self.prompt_label.setText(text or '')
        self.prompt_label.adjustSize()
        self.adjustSize()

    def set_transient_mode(self, enabled=True):
        try:
            if enabled:
                self.setStyleSheet(
                    'QFrame#chatPromptBubble { background: rgba(240, 240, 240, 255); '
                    'border: 1px solid rgba(170, 170, 170, 200); border-radius: 16px; } '
                    'QLineEdit { background: rgba(255, 255, 255, 255); color: #111111; border: 1px solid rgba(180, 180, 180, 200); '
                    'border-radius: 10px; padding: 10px; }'
                    'QPushButton { background: rgba(245, 245, 245, 255); color: #111111; border: 1px solid rgba(180, 180, 180, 200); '
                    'border-radius: 10px; padding: 10px 14px; font-weight: 700; }'
                    'QPushButton:hover { background: rgba(235, 235, 235, 255); }'
                )
            else:
                self.setStyleSheet(
                    'QFrame#chatPromptBubble { background: rgba(255, 255, 255, 255); '
                    'border: 1px solid rgba(180, 180, 180, 200); border-radius: 16px; } '
                    'QLineEdit { background: rgba(255, 255, 255, 255); color: #111111; border: 1px solid rgba(180, 180, 180, 200); '
                    'border-radius: 10px; padding: 10px; }'
                    'QPushButton { background: rgba(245, 245, 245, 255); color: #111111; border: 1px solid rgba(180, 180, 180, 200); '
                    'border-radius: 10px; padding: 10px 14px; font-weight: 700; }'
                    'QPushButton:hover { background: rgba(235, 235, 235, 255); }'
                )
        except Exception:
            pass

    def append_message(self, speaker, text, outgoing=False):
        bubble = ChatMessageBubble(speaker, text, outgoing=outgoing)
        self.chat_log_layout.insertWidget(self.chat_log_layout.count() - 1, bubble)
        scrollbar = self.chat_log.verticalScrollBar()
        QtCore.QTimer.singleShot(0, lambda: scrollbar.setValue(scrollbar.maximum()))

    def expand_chat(self):
        if self._expanded:
            self._move_focus_to_input()
            return
        self._expanded = True
        self.expand_hint.hide()
        self.details_widget.show()
        self.adjustSize()
        self._move_focus_to_input()

    def collapse_chat(self):
        self._expanded = False
        self.details_widget.hide()
        self.expand_hint.show()
        self.adjustSize()
        self.closed.emit()

    def is_expanded(self):
        return self._expanded

    def set_waiting(self, waiting):
        self.input_edit.setDisabled(waiting)
        self.send_button.setDisabled(waiting)

    def clear_input(self):
        self.input_edit.clear()

    def _move_focus_to_input(self):
        QtCore.QTimer.singleShot(0, self.input_edit.setFocus)

    def _submit(self):
        text = self.input_edit.text().strip()
        if not text:
            return
        self.input_edit.clear()
        self.submitted.emit(text)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class ChatMessageBubble(QtWidgets.QFrame):
    def __init__(self, speaker, text, outgoing=False, parent=None):
        super().__init__(parent)
        self.setObjectName('chatMessageBubble')
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Maximum)

        outer_layout = QtWidgets.QHBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        if outgoing:
            outer_layout.addStretch(1)

        bubble = QtWidgets.QFrame()
        bubble.setObjectName('bubbleBody')
        bubble_layout = QtWidgets.QVBoxLayout(bubble)
        bubble_layout.setContentsMargins(12, 8, 12, 8)
        bubble_layout.setSpacing(4)

        speaker_label = QtWidgets.QLabel(speaker)
        speaker_label.setObjectName('speakerLabel')
        speaker_label.setStyleSheet('QLabel { color: #444444; font-size: 12px; font-weight: 700; }')
        speaker_label.setMinimumHeight(20)

        message_label = QtWidgets.QLabel(text or '')
        message_label.setWordWrap(True)
        message_label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        message_label.setStyleSheet('QLabel { color: #111111; font-size: 19px; }')
        message_label.setMinimumHeight(28)

        bubble_layout.addWidget(speaker_label)
        bubble_layout.addWidget(message_label)

        if outgoing:
            bubble.setStyleSheet(
                'QFrame#bubbleBody { background: rgba(245, 245, 245, 255); border: 1px solid rgba(180, 180, 180, 200); border-radius: 16px; }'
            )
        else:
            bubble.setStyleSheet(
                'QFrame#bubbleBody { background: rgba(255, 255, 255, 255); border: 1px solid rgba(132, 166, 220, 140); border-radius: 16px; }'
            )

        outer_layout.addWidget(bubble, 0)

        if not outgoing:
            outer_layout.addStretch(1)


class PetChatFeature(QtCore.QObject):
    def __init__(self, pet_window, controller=None, api_key=None, settings_path=None, parent=None):
        super().__init__(parent or pet_window)
        self.pet_window = pet_window
        self.controller = controller
        self.settings_path = Path(settings_path) if settings_path else _default_settings_path()
        self.client = GeminiChatClient(api_key or '')
        self.chat_enabled = True
        self.chat_history = []
        self.chat_session_active = False
        self.chat_generating = False
        self._latest_timer_text = '沒有計時器'
        self._last_prompt_text = ''
        self._last_prompt_at = 0.0
        self._async_jobs = []
        self._pet_hovered = False
        self._active_prompt_source = None

        self.chat_prompt_bubble = ChatPromptBubble()
        self.chat_prompt_bubble.hide()
        self.chat_prompt_bubble.clicked.connect(self.open_chat_dialog)
        # handle submitted text and closed events
        try:
            self.chat_prompt_bubble.submitted.connect(self._on_bubble_submitted)
        except Exception:
            pass
        try:
            self.chat_prompt_bubble.closed.connect(self.end_chat_session)
        except Exception:
            pass

        self.chat_prompt_timer = QtCore.QTimer(self)
        self.chat_prompt_timer.setSingleShot(True)
        self.chat_prompt_timer.timeout.connect(self._dismiss_prompt)

        self.chat_timer = QtCore.QTimer(self)
        self.chat_timer.setSingleShot(True)
        self.chat_timer.timeout.connect(self._begin_chat_prompt)

        self.hover_monitor_timer = QtCore.QTimer(self)
        self.hover_monitor_timer.timeout.connect(self._sync_hover_pause)
        self.hover_monitor_timer.start(HOVER_POLL_MS)

        try:
            self.pet_window.hoverStateChanged.connect(self._on_pet_hover_changed)
        except Exception:
            pass
        try:
            self.pet_window.moved.connect(self._on_pet_moved)
        except Exception:
            pass

        self.startup_timer = QtCore.QTimer(self)
        self.startup_timer.setSingleShot(True)
        self.startup_timer.timeout.connect(self._startup_chat)

        if self.controller is not None:
            try:
                self.controller.updated.connect(self._on_timer_updated)
            except Exception:
                pass

        if self.chat_enabled:
            self.startup_timer.start(STARTUP_CHAT_DELAY_MS)
            self._schedule_next_chat()

    def _pause_pet(self, paused):
        try:
            if paused:
                self.pet_window.move_timer.stop()
                self.pet_window.frame_timer.stop()
            else:
                if not self.pet_window.move_timer.isActive():
                    self.pet_window.move_timer.start(40)
                if not self.pet_window.frame_timer.isActive():
                    self.pet_window.frame_timer.start(150)
        except Exception:
            pass

    def _on_pet_hover_changed(self, hovering):
        self._pet_hovered = bool(hovering)
        self._sync_hover_pause()

    def _on_pet_moved(self):
        if self.chat_prompt_bubble.isVisible():
            self._move_prompt_bubble()

    def _sync_hover_pause(self):
        try:
            hovering = bool(self.pet_window.isVisible() and (self._pet_hovered or self.pet_window._cursor_near_pet()))
        except Exception:
            hovering = False

        prompt_visible = self.chat_prompt_bubble.isVisible()
        active_prompt = self._active_prompt_source in {'chat', 'timer', 'thinking'}

        if hovering:
            self._pause_pet(True)
            if not self.chat_session_active and not self.chat_generating and not prompt_visible:
                if self._should_restore_recent_prompt():
                    self._show_prompt(self._last_prompt_text, remember=False, append_history=False)
                elif self._latest_timer_text and self._latest_timer_text != '沒有計時器':
                    self._show_timer_prompt()
                else:
                    # no recent content and no timer -> show default clickable hint
                    self.chat_prompt_bubble.set_prompt('點我開始聊天')
                    self.chat_prompt_bubble.set_waiting(False)
                    try:
                        self.chat_prompt_bubble.set_transient_mode(True)
                    except Exception:
                        pass
                    self._move_prompt_bubble()
                    self.chat_prompt_bubble.show()
                    self.chat_prompt_bubble.raise_()
            if prompt_visible:
                self._move_prompt_bubble()
        elif active_prompt or self.chat_session_active or self.chat_generating:
            self._pause_pet(True)
            if prompt_visible:
                self._move_prompt_bubble()
        elif not self.chat_session_active and not self.chat_generating:
            if prompt_visible:
                self.chat_prompt_bubble.hide()
            self.chat_prompt_timer.stop()
            self._pause_pet(False)

    def _format_context_hint(self, text):
        text = (text or '').strip()
        if not text:
            return ''
        try:
            return text if len(text) <= 120 else text[:117] + '...'
        except Exception:
            return text

    def _build_context_prompt(self):
        base_dir = Path(__file__).resolve().parent
        books = load_book_topics(base_dir)
        events = load_calendar_events(base_dir)
        lines = []

        if books:
            sample_books = '、'.join(random.sample(books, min(3, len(books))))
            lines.append(f'書單分類有：{sample_books}')

        if events:
            today = datetime.now().date().isoformat()
            today_events = [item for item in events if item.get('date') == today]
            chosen_events = today_events or events
            chosen = random.choice(chosen_events)
            lines.append(f"行事曆提醒：{chosen.get('time') or '未指定時間'} {chosen.get('task') or '待辦事項'}")

        if not lines:
            lines.append('今天請用溫柔可愛的方式主動關心主人，提醒他注意待辦和行程。')

        return '\n'.join(lines)

    def _schedule_next_chat(self):
        if not self.chat_enabled or self.chat_generating or self.chat_session_active:
            return
        interval = random.randint(CHAT_PROMPT_MIN_MS, CHAT_PROMPT_MAX_MS)
        self.chat_timer.start(interval)

    def _should_restore_recent_prompt(self):
        if not self._last_prompt_text or not self._last_prompt_at:
            return False
        return (time.monotonic() - self._last_prompt_at) * 1000 <= CHAT_RECENT_RESTORE_MS

    def _startup_chat(self):
        if not self.chat_enabled or self.chat_session_active:
            return
        self.chat_generating = True
        self._active_prompt_source = 'thinking'
        self._pause_pet(True)
        self.chat_prompt_bubble.set_prompt('小寵物正在準備第一句話...')
        self._move_prompt_bubble()
        self.chat_prompt_bubble.show()
        self.chat_prompt_bubble.raise_()

        def _request():
            context_hint = self._build_context_prompt()
            local_seed = build_local_prompt(base_dir=Path(__file__).resolve().parent)
            if not self.client.enabled:
                return local_seed
            prompt = (
                '請依照以下資訊，生成一句繁體中文、自然可愛、像小寵物在主動聊天的開場白，30字到60字。\n'
                f'{context_hint}\n'
                f'開場感覺要像：{local_seed}'
            )
            return self.client.generate(prompt, history=self.chat_history[-4:])

        def _done(result, error):
            self.chat_generating = False
            opener = (result or '').strip() if error is None else ''
            if not opener:
                opener = build_local_prompt(base_dir=Path(__file__).resolve().parent)
            self.chat_history.append(('model', opener))
            self._show_prompt(opener)

        self._launch_async(_request, _done)

    def _launch_async(self, func, callback):
        thread = QtCore.QThread(self)
        worker = _AsyncWorker(func)
        worker.moveToThread(thread)
        worker._chat_callback = callback
        worker._chat_thread = thread

        worker.finished.connect(self._on_async_finished)
        thread.started.connect(worker.run)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._cleanup_async_thread)
        self._async_jobs.append((thread, worker))
        thread.start()

    @QtCore.pyqtSlot(object, object)
    def _on_async_finished(self, result, error):
        worker = self.sender()
        callback = getattr(worker, '_chat_callback', None)
        thread = getattr(worker, '_chat_thread', None)
        try:
            if callable(callback):
                callback(result, error)
        finally:
            if thread is not None:
                thread.quit()

    @QtCore.pyqtSlot()
    def _cleanup_async_thread(self):
        thread = self.sender()
        self._async_jobs = [job for job in self._async_jobs if job[0] is not thread]

    def _move_prompt_bubble(self):
        self.chat_prompt_bubble.adjustSize()
        pet_geo = self.pet_window.frameGeometry()
        screen = QtWidgets.QApplication.screenAt(pet_geo.center()) or QtWidgets.QApplication.primaryScreen()
        if screen is None:
            self.chat_prompt_bubble.move(self.pet_window.mapToGlobal(QtCore.QPoint(self.pet_window.width() + 16, -4)))
            return

        screen_geo = screen.availableGeometry()
        margin = 12
        gap = 16

        max_width = max(180, screen_geo.width() - margin * 2)
        if self.chat_prompt_bubble.width() > max_width:
            self.chat_prompt_bubble.setFixedWidth(max_width)
            self.chat_prompt_bubble.adjustSize()

        bubble_w = self.chat_prompt_bubble.width()
        bubble_h = self.chat_prompt_bubble.height()

        right_x = pet_geo.right() + gap
        left_x = pet_geo.left() - bubble_w - gap
        prefer_right = (screen_geo.right() - right_x) >= (left_x - screen_geo.left())
        if prefer_right and right_x + bubble_w <= screen_geo.right() - margin:
            bx = right_x
        elif left_x >= screen_geo.left() + margin:
            bx = left_x
        else:
            bx = min(max(screen_geo.left() + margin, right_x), screen_geo.right() - bubble_w - margin)

        by = pet_geo.top() - 4
        max_by = screen_geo.bottom() - bubble_h - margin
        by = min(max(screen_geo.top() + margin, by), max_by)
        self.chat_prompt_bubble.move(bx, by)

    def _show_prompt(self, text, remember=True, append_history=True):
        self.chat_prompt_timer.stop()
        self._active_prompt_source = 'chat'
        self.chat_prompt_bubble.set_prompt(text)
        # transient (hover) prompts use gray background
        if not self.chat_prompt_bubble.is_expanded():
            try:
                self.chat_prompt_bubble.set_transient_mode(True)
            except Exception:
                pass
        else:
            try:
                self.chat_prompt_bubble.set_transient_mode(False)
            except Exception:
                pass
        if append_history and not self.chat_prompt_bubble.is_expanded():
            self.chat_prompt_bubble.append_message('小寵物', text, outgoing=False)
        if remember:
            self._last_prompt_text = text
            self._last_prompt_at = time.monotonic()
        self._move_prompt_bubble()
        self.chat_prompt_bubble.show()
        self.chat_prompt_bubble.raise_()
        self._pause_pet(True)
        self.chat_prompt_timer.start(CHAT_PROMPT_TIMEOUT_MS)

    def _show_timer_prompt(self):
        if self._active_prompt_source == 'chat' and self.chat_prompt_bubble.isVisible():
            return
        timer_text = self._latest_timer_text if self._latest_timer_text else '沒有計時器'
        self._active_prompt_source = 'timer'
        self.chat_prompt_bubble.set_prompt(f'番茄鐘提醒：{timer_text}')
        self.chat_prompt_bubble.set_waiting(False)
        try:
            self.chat_prompt_bubble.set_transient_mode(True)
        except Exception:
            pass
        self._move_prompt_bubble()
        self.chat_prompt_bubble.show()
        self.chat_prompt_bubble.raise_()
        self.chat_prompt_timer.start(CHAT_PROMPT_TIMEOUT_MS)

    def _on_bubble_submitted(self, text):
        try:
            if not text:
                return
            # ensure session state
            if not self.chat_session_active:
                self.chat_session_active = True
                self._pause_pet(True)
            # forward to send_message safely
            self.send_message(text)
        except Exception:
            # don't crash the UI thread on unexpected errors
            pass

    def _dismiss_prompt(self):
        self.chat_prompt_bubble.hide()
        self.chat_generating = False
        self.chat_session_active = False
        self._active_prompt_source = None
        self._pause_pet(False)
        self._schedule_next_chat()

    def _begin_chat_prompt(self):
        if not self.chat_enabled or self.chat_generating or self.chat_session_active:
            return
        if not self.pet_window.isVisible():
            self._schedule_next_chat()
            return

        self.chat_generating = True
        self._active_prompt_source = 'thinking'
        self._pause_pet(True)
        self.chat_prompt_bubble.set_prompt('小寵物正在想一句話...')
        self._move_prompt_bubble()
        self.chat_prompt_bubble.show()
        self.chat_prompt_bubble.raise_()

        def _request():
            context_hint = self._build_context_prompt()
            local_seed = build_local_prompt(base_dir=Path(__file__).resolve().parent)
            if not self.client.enabled:
                return local_seed
            return self.client.generate(
                '請用繁體中文、可愛又自然的口吻，根據下列資訊主動跟主人聊天並問一個簡單問題，40字到60字。\n'
                f'{context_hint}\n'
                f'語氣參考：{local_seed}',
                history=self.chat_history[-6:],
            )

        def _done(result, error):
            self.chat_generating = False
            opener = '主人，我想跟你聊天，可以點我一下。'
            if error is None:
                opener = (result or '').strip() or opener
            self.chat_history.append(('model', opener))
            self._show_prompt(opener)

        self._launch_async(_request, _done)

    def open_chat_dialog(self):
        if not self.chat_enabled:
            return

        self.chat_prompt_timer.stop()
        self.chat_session_active = True
        self._pause_pet(True)

        try:
            self.chat_prompt_bubble.clear_input()
        except Exception:
            pass

        self.chat_prompt_bubble.set_prompt('輸入你想跟小寵物說的話')
        self.chat_prompt_bubble.show()
        self.chat_prompt_bubble.expand_chat()
        self._move_prompt_bubble()
        self._refresh_bubble_history()
        self.chat_prompt_bubble.set_waiting(False)
        self.chat_prompt_bubble.show()
        self.chat_prompt_bubble.raise_()
        self.chat_prompt_bubble.activateWindow()

        try:
            self.chat_prompt_bubble.input_edit.setFocus()
            self.chat_prompt_bubble.input_edit.setEnabled(True)
        except Exception:
            pass

    def _refresh_bubble_history(self):
        while self.chat_prompt_bubble.chat_log_layout.count() > 1:
            item = self.chat_prompt_bubble.chat_log_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        for role, text in self.chat_history[-12:]:
            outgoing = role == 'user'
            speaker = '你' if outgoing else '小寵物'
            self.chat_prompt_bubble.append_message(speaker, text, outgoing=outgoing)

    def send_message(self, text):
        if not self.chat_enabled or not self.chat_session_active:
            return
        self.chat_history.append(('user', text))
        self.chat_prompt_bubble.append_message('你', text, outgoing=True)
        self.chat_prompt_bubble.set_waiting(True)

        def _request():
            try:
                # 檢查 API 是否啟用
                if not self.client.enabled:
                    return None
                # 調用 Gemini API
                result = self.client.generate(
                    f'請以可愛小寵物的口吻回覆主人：{text}',
                    history=self.chat_history[-8:],
                )
                return result
            except Exception as e:
                return None

        def _done(result, error):
            if not self.chat_session_active:
                return
            reply = (result or '').strip() if error is None else ''
            if not reply:
                # API 沒有返回結果，給出動態備用回應
                if not self.client.enabled:
                    reply = '主人還沒有設定 AI API key 呢，我現在無法聊天喔'
                else:
                    # API key 存在但 API 調用失敗 - 可能是配額限制或其他問題
                    if len(text) > 20:
                        short_text = text[:17] + '...'
                    else:
                        short_text = text
                    reply = f'我聽到你說「{short_text}」了，想想該怎麼回答呢～'
            self.chat_history.append(('model', reply))
            self.chat_prompt_bubble.append_message('小寵物', reply, outgoing=False)
            self.chat_prompt_bubble.set_waiting(False)

        self._launch_async(_request, _done)

    def end_chat_session(self):
        self.chat_session_active = False
        self.chat_generating = False
        self._active_prompt_source = None
        self.chat_prompt_bubble.hide()
        self._pause_pet(False)
        self._schedule_next_chat()

    def _on_timer_updated(self, remaining_seconds, progress, running, activity_text):
        self._latest_timer_text = f'{remaining_seconds // 60:02d}:{remaining_seconds % 60:02d}' if running else '沒有計時器'
        if self.chat_prompt_bubble is not None and self.chat_prompt_bubble.isVisible():
            if self._active_prompt_source == 'chat' or self.chat_session_active:
                return
            if self._active_prompt_source == 'timer':
                if running:
                    self.chat_prompt_bubble.set_prompt(f'番茄鐘提醒：{self._latest_timer_text}')
                else:
                    self._dismiss_prompt()
                return
            if running and not self._should_restore_recent_prompt():
                self._show_timer_prompt()


def create_pet_chat_feature(pet_window, controller=None, api_key=None, settings_path=None, parent=None):
    return PetChatFeature(
        pet_window=pet_window,
        controller=controller,
        api_key=api_key,
        settings_path=settings_path,
        parent=parent,
    )
