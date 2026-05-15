import os
import sys
import random
import json
from pathlib import Path
from datetime import datetime

from PyQt5 import QtWidgets, QtCore, QtGui, QtMultimedia

from pomodoro_feature import PomodoroController, PomodoroPanel
from calendar_feature import CalendarPanel


def _configure_qt_plugin_paths():
    venv_root = Path(sys.executable).resolve().parent.parent
    qt_plugins_path = venv_root / 'Lib' / 'site-packages' / 'PyQt5' / 'Qt5' / 'plugins'
    qt_platforms_path = qt_plugins_path / 'platforms'
    if qt_platforms_path.exists():
        os.environ.setdefault('QT_QPA_PLATFORM_PLUGIN_PATH', str(qt_platforms_path))
        os.environ.setdefault('QT_PLUGIN_PATH', str(qt_plugins_path))


_configure_qt_plugin_paths()


# 活動霓虹色定義（大賢者主題 - 霓虹青藍色系）
ACTIVITY_NEON_COLORS = {
    '讀書中': QtGui.QColor(0, 255, 200),        # 亮青綠
    '修習中': QtGui.QColor(0, 255, 200),        # 亮青綠
    '健身中': QtGui.QColor(0, 200, 255),        # 霓虹藍
    '休息中': QtGui.QColor(100, 200, 255),      # 淡霓虹藍
    '工作中': QtGui.QColor(0, 230, 200),        # 亮青
    '冥想中': QtGui.QColor(0, 180, 255),        # 深藍
}

# 預設活動顏色
def get_neon_color(activity_text):
    """獲取活動對應的霓虹色（大賢者主題）"""
    return ACTIVITY_NEON_COLORS.get(activity_text, QtGui.QColor(0, 255, 150))


def _ui_size(normal_size, compact_size, compact_mode):
    return compact_size if compact_mode else normal_size


SAGE_STYLE = """
QMainWindow, QWidget {
    color: #e6fbff;
    font-family: 'Microsoft JhengHei';
}
QFrame#menuPanel, QFrame#pomodoroCore {
    background: rgba(7, 16, 29, 205);
    border: 1px solid rgba(117, 220, 255, 80);
    border-radius: 18px;
}
QLabel {
    color: #e6fbff;
}
QPushButton {
    background: rgba(14, 28, 50, 220);
    color: #effcff;
    border: 1px solid rgba(110, 214, 255, 90);
    border-radius: 12px;
    padding: 10px 14px;
    font-size: 15px;
}
QPushButton:hover {
    background: rgba(33, 62, 95, 235);
    border: 1px solid rgba(168, 241, 255, 160);
}
QPushButton:checked {
    background: rgba(0, 242, 255, 65);
    border: 1px solid rgba(0, 242, 255, 200);
}
QSpinBox {
    background: rgba(9, 18, 31, 230);
    color: #effcff;
    padding: 6px;
    border: 1px solid rgba(110, 214, 255, 90);
    border-radius: 8px;
}
QComboBox {
    background: rgba(9, 18, 31, 230);
    color: #effcff;
    padding: 8px;
    border: 1px solid rgba(110, 214, 255, 90);
    border-radius: 8px;
    font-size: 16px;
}
QComboBox QAbstractItemView {
    background: rgba(9, 18, 31, 240);
    color: #effcff;
    selection-background-color: rgba(0, 242, 255, 80);
}
"""


class DailyPieChart(QtWidgets.QWidget):
    """顯示當日活動時間分配的圓餅圖（左邊圓餅圖，右邊圖例）"""
    def __init__(self, parent=None, compact_mode=False):
        super().__init__(parent)
        self.compact_mode = compact_mode
        self.data = {}  # {活動名稱: 分鐘數}
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.setMinimumSize(540 if compact_mode else 720, 580 if compact_mode else 760)
        self.setMinimumHeight(100)  # 最小高度
        self.current_date = datetime.now().date()
        self.view_mode = 'day'

    def set_data(self, activities_data, date=None, view_mode='day'):
        """設置圓餅圖數據 {活動: 分鐘數}"""
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
        
        # 沒有數據時顯示無資料訊息
        if not self.data or sum(self.data.values()) == 0:
            painter.setPen(QtGui.QColor(255, 255, 255))
            painter.setFont(QtGui.QFont('Microsoft JhengHei', _ui_size(18, 12, self.compact_mode), QtGui.QFont.Bold))
            
            view_text = {'day': '今日', 'week': '本週', 'month': '本月', 'year': '本年'}.get(self.view_mode, '本期')
            painter.drawText(self.rect(), QtCore.Qt.AlignCenter, f'{view_text}\n暫無統計數據')
            return

        # 繪製日期標題（西元年月日）
        painter.setFont(QtGui.QFont('Microsoft JhengHei', _ui_size(14, 11, self.compact_mode), QtGui.QFont.Bold))
        painter.setPen(QtGui.QColor(255, 255, 255))
        date_str = self.current_date.strftime('%Y年%m月%d日')
        painter.drawText(inner_rect.left(), inner_rect.top(), inner_rect.width(), title_height, QtCore.Qt.AlignCenter, date_str)

        # 繪製圓餅圖
        total = sum(self.data.values())
        start_angle = 0

        for activity, minutes in self.data.items():
            if minutes <= 0:
                continue
            angle = (minutes / total) * 360 * 16  # Qt 使用 1/16 度為單位
            color = get_neon_color(activity)

            painter.setBrush(color)
            painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255, 120), 2))
            painter.drawPie(pie_rect, int(start_angle), int(angle))

            start_angle += angle

        # 繪製圖例（下方集中排列）
        painter.setFont(QtGui.QFont('Microsoft JhengHei', _ui_size(10, 8, self.compact_mode), QtGui.QFont.Bold))

        sorted_items = sorted(self.data.items(), key=lambda x: x[1], reverse=True)
        legend_y = legend_start_y
        for idx, (activity, minutes) in enumerate(sorted_items):
            if minutes <= 0:
                continue
            color = get_neon_color(activity)

            # 顏色方塊（集中在下方）
            painter.setBrush(color)
            painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255, 200), 1))
            painter.drawRect(QtCore.QRectF(legend_x, legend_y + 4, legend_swatch, legend_swatch))

            # 標籤文字
            painter.setPen(QtGui.QColor(255, 255, 255))
            label_text = f'{activity} {minutes}m'
            painter.drawText(int(legend_x + legend_swatch + 6), legend_y, legend_width - legend_swatch - 6, legend_item_height,
                            QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, label_text)
            legend_y += legend_item_height




class SageBackground(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        self.particles = []
        self.lines = []
        self._init_elements()

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self._animate)
        self.timer.start(50)

    def _init_elements(self):
        width = max(1, self.width() or 1920)
        height = max(1, self.height() or 1080)
        for _ in range(40):
            self.particles.append({
                'pos': QtCore.QPointF(random.random() * width, random.random() * height),
                'size': random.randint(2, 6),
                'speed': random.random() * 1.8 + 0.8,
                'alpha': random.randint(40, 160),
            })
        for _ in range(10):
            self.lines.append(self._create_curve())

    def _create_curve(self):
        path = QtGui.QPainterPath()
        start_y = random.randint(0, max(1, self.height() or 1080))
        path.moveTo(-80, start_y)
        path.cubicTo(
            500, start_y + random.randint(-240, 240),
            1200, start_y + random.randint(-240, 240),
            max(2100, self.width() or 2100), random.randint(0, max(1, self.height() or 1080))
        )
        return {
            'path': path,
            'color': QtGui.QColor(0, 255, 255, random.randint(20, 60)),
            'width': random.random() * 2 + 1,
        }

    def _animate(self):
        for particle in self.particles:
            particle['pos'].setY(particle['pos'].y() - particle['speed'])
            if particle['pos'].y() < -10:
                particle['pos'].setY(self.height() + 10)
                particle['pos'].setX(random.random() * max(1, self.width()))
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        bg_grad = QtGui.QRadialGradient(self.width() / 2, self.height() / 2, max(self.width(), self.height()))
        bg_grad.setColorAt(0, QtGui.QColor(12, 42, 52))
        bg_grad.setColorAt(0.55, QtGui.QColor(4, 16, 26))
        bg_grad.setColorAt(1, QtGui.QColor(1, 4, 8))
        painter.fillRect(self.rect(), bg_grad)

        for line in self.lines:
            pen = QtGui.QPen(line['color'], line['width'])
            painter.setPen(pen)
            painter.drawPath(line['path'])

        for particle in self.particles:
            painter.setBrush(QtGui.QColor(180, 255, 255, particle['alpha']))
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawRect(QtCore.QRectF(particle['pos'].x(), particle['pos'].y(), particle['size'], particle['size']))


# ---- Notice UI integrated from notice.py ----
class MagicBackgroundNotice(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.particles = []
        for _ in range(50):
            self.particles.append({
                'pos': QtCore.QPointF(random.random() * 1000, random.random() * 600),
                'size': random.randint(1, 4),
                'color': QtGui.QColor(random.randint(100, 255), random.randint(50, 150), 50, 150)
            })
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(30)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        grad = QtGui.QLinearGradient(0, 0, self.width(), self.height())
        grad.setColorAt(0, QtGui.QColor(20, 5, 5))
        grad.setColorAt(0.5, QtGui.QColor(10, 10, 20))
        grad.setColorAt(1, QtGui.QColor(5, 15, 10))
        painter.fillRect(self.rect(), grad)
        painter.setOpacity(0.3)
        for i in range(15):
            pen = QtGui.QPen(QtGui.QColor(255, 200, 50), random.random() * 1.5)
            painter.setPen(pen)
            painter.drawLine(0, random.randint(0, max(1, self.height())), max(1000, self.width()), random.randint(0, max(1, self.height())))


class SageSpeakingDiamond(QtWidgets.QWidget):
    def __init__(self, parent=None, compact_mode=False):
        super().__init__(parent)
        self.compact_mode = compact_mode
        self.setFixedSize(340 if compact_mode else 360, 340 if compact_mode else 400)
        # no subtitle / typing text per user request
        self.display_text = ""
        self.full_text = ""

    def _type_text(self):
        return

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        w, h = self.width(), self.height()
        points = [
            QtCore.QPoint(w // 2, 20),
            QtCore.QPoint(w - 20, h // 2),
            QtCore.QPoint(w // 2, h - 20),
            QtCore.QPoint(20, h // 2)
        ]
        polygon = QtGui.QPolygon(points)
        path = QtGui.QPainterPath()
        path.addPolygon(QtGui.QPolygonF(polygon))
        painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255, 200), 4))
        painter.setBrush(QtGui.QColor(0, 0, 0, 220))
        painter.drawPath(path)
        painter.setPen(QtGui.QColor(255, 255, 255))
        painter.setFont(QtGui.QFont('Microsoft JhengHei', _ui_size(22, 16, self.compact_mode), QtGui.QFont.Bold))
        painter.drawText(QtCore.QRect(w//2 + 35, h//2 - 110, 60, 120), QtCore.Qt.AlignCenter, "專\n注\n模\n式")
        font_main = QtGui.QFont('SimSun-ExtB', _ui_size(68, 48, self.compact_mode), QtGui.QFont.Bold)
        painter.setFont(font_main)
        painter.drawText(QtCore.QRect(0, 0, w, h), QtCore.Qt.AlignCenter, "專\n注\n者")
        font_side = QtGui.QFont('SimSun-ExtB', _ui_size(30, 20, self.compact_mode), QtGui.QFont.Bold)
        painter.setFont(font_side)
        painter.drawText(w // 2 - 120, h // 2 + 10, "成")
        painter.drawText(w // 2 + 80, h // 2 + 10, "功")
        # user requested no subtitle text, skip drawing bottom text


class SageNoticeWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('個體名：大賢者 - 專注通知')
        self.resize(1000, 600)
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QGridLayout(central)
        self.bg = MagicBackgroundNotice()
        self.diamond = SageSpeakingDiamond()
        layout.addWidget(self.bg, 0, 0)
        layout.addWidget(self.diamond, 0, 0, QtCore.Qt.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)

# ---- end notice UI ----


class GreatSageDisc(QtWidgets.QWidget):
    def __init__(self, parent=None, compact_mode=False):
        super().__init__(parent)
        self.compact_mode = compact_mode
        self.setMinimumSize(640 if compact_mode else 700, 640 if compact_mode else 700)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.remaining_text = '25:00'
        self.progress = 0.0
        self.running = False
        self.activity_text = '讀書中'
        self.status_override_text = ''

    def set_status_override(self, text=''):
        self.status_override_text = text or ''
        self.update()

    def set_timer_state(self, remaining_seconds, progress, running, activity_text):
        self.remaining_text = f'{remaining_seconds // 60:02d}:{remaining_seconds % 60:02d}'
        self.progress = max(0.0, min(1.0, progress))
        self.running = running
        self.activity_text = self.status_override_text or activity_text
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        cx = self.width() / 2
        cy = self.height() / 2
        radius = min(self.width(), self.height()) / 2

        glow = QtGui.QRadialGradient(cx, cy, radius)
        glow.setColorAt(0.70, QtGui.QColor(255, 255, 255, 255))
        glow.setColorAt(1.0, QtGui.QColor(255, 255, 255, 0))
        painter.setBrush(glow)
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawEllipse(0, 0, self.width(), self.height())

        # outer progress ring around the disc
        ring_margin = int(self.width() * 0.03)
        ring_rect = QtCore.QRect(ring_margin, ring_margin, self.width() - 2 * ring_margin, self.height() - 2 * ring_margin)
        track_pen = QtGui.QPen(QtGui.QColor(120, 220, 255, 70), max(8, int(self.width() * 0.018)))
        track_pen.setCapStyle(QtCore.Qt.RoundCap)
        painter.setPen(track_pen)
        painter.setBrush(QtCore.Qt.NoBrush)
        painter.drawArc(ring_rect, 90 * 16, -360 * 16)

        progress_pen = QtGui.QPen(QtGui.QColor(145, 245, 255, 235), max(10, int(self.width() * 0.022)))
        progress_pen.setCapStyle(QtCore.Qt.RoundCap)
        painter.setPen(progress_pen)
        painter.drawArc(ring_rect, 90 * 16, int(-360 * 16 * self.progress))

        painter.setPen(QtGui.QColor(40, 40, 40))
        painter.setFont(QtGui.QFont('Microsoft JhengHei', max(7 if self.compact_mode else 10, int(self.height() * (0.018 if self.compact_mode else 0.03)))))
        painter.drawText(QtCore.QRect(0, int(self.height() * 0.22), self.width(), 40), QtCore.Qt.AlignCenter, 'ユニークスキル')

        main_font = QtGui.QFont('SimSun-ExtB', max(24 if self.compact_mode else 48, int(self.height() * (0.08 if self.compact_mode else 0.16))), QtGui.QFont.Bold)
        painter.setFont(main_font)
        painter.drawText(QtCore.QRect(0, int(self.height() * 0.30), self.width(), int(self.height() * 0.22)), QtCore.Qt.AlignCenter, '大賢者')

        rect_w = int(self.width() * 0.36)
        rect_h = max(40, int(self.height() * 0.08))
        rect_x = int((self.width() - rect_w) / 2)
        rect_y = int(self.height() * 0.60)
        rect = QtCore.QRect(rect_x, rect_y, rect_w, rect_h)

        painter.setPen(QtGui.QPen(QtGui.QColor(50, 90, 80), 3))
        painter.drawRect(rect)
        painter.setFont(QtGui.QFont('Microsoft JhengHei', max(7 if self.compact_mode else 10, int(self.height() * (0.02 if self.compact_mode else 0.035))), QtGui.QFont.Bold))
        painter.drawText(rect, QtCore.Qt.AlignCenter, self.remaining_text)

        status_font = QtGui.QFont('Microsoft JhengHei', max(7 if self.compact_mode else 10, int(self.height() * (0.018 if self.compact_mode else 0.03))), QtGui.QFont.Bold)
        painter.setFont(status_font)
        painter.setPen(QtGui.QColor(45, 85, 78))
        status_text = self.status_override_text or self.activity_text
        painter.drawText(QtCore.QRect(0, int(self.height() * 0.69), self.width(), 40), QtCore.Qt.AlignCenter, status_text)


class PomodoroController(QtCore.QObject):
    updated = QtCore.pyqtSignal(int, float, bool, str)
    alarmStarted = QtCore.pyqtSignal()
    alarmStopped = QtCore.pyqtSignal()
    sessionRecorded = QtCore.pyqtSignal(str, int, str)
    pieChartUpdateRequested = QtCore.pyqtSignal()  # 圓餅圖更新信號

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
        # setup audio player (optional)
        try:
            self.player = QtMultimedia.QMediaPlayer()
            self.player.setVolume(50)
        except Exception:
            self.player = None
        # discover music files in assets/music and map by activity
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
                # time reached zero: emit final state and show notice
                self._emit()
                try:
                    self._on_finish()
                except Exception:
                    pass
                # stop timer and music
                self.stop(record_session=False)
        else:
            self.stop(record_session=False)

    def _on_finish(self):
        # emit alarm started signal and stop music
        try:
            self._record_session(self.total_seconds, '計時器')
            try:
                self._stop_music()
            except Exception:
                pass
            self.alarmStarted.emit()
            # 計時完成時更新圓餅圖
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
            # if remiru_movie.mp3 exists, map it to the study activity (讀書中 / 修習中)
            if 'remiru_movie.mp3' in res:
                res['讀書中'] = res['remiru_movie.mp3']
                res['修習中'] = res['remiru_movie.mp3']
        except Exception:
            return res
        return res

    def _play_music(self):
        if not self.player:
            return
        # choose music by activity_text if available, else use any found file
        music_path = None
        try:
            if isinstance(self._music_map, dict):
                # prefer exact activity mapping
                music_path = self._music_map.get(self.activity_text)
                if not music_path:
                    # fallback to any mp3 (first value that's not an activity key)
                    for k, v in self._music_map.items():
                        if k not in ('讀書中', '修習中') and not k.endswith('.mp3'):
                            continue
                        # if key looks like filename or activity, pick filename entries
                        if k.lower().endswith('.mp3'):
                            music_path = v
                            break
                    if not music_path:
                        # take any value
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
            # when switching from countdown to stopwatch while running, restart elapsed from zero
            self.remaining_seconds = 0
        elif (not self.stopwatch_mode) and prev_stopwatch_mode:
            # when switching from stopwatch to countdown while running, apply new countdown target
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
            # play music when starting if available
            try:
                self._play_music()
            except Exception:
                pass

    def stop(self, record_session=False):
        # 自動記錄秒錶暫停或計時完成的時間
        if self.running:
            if self.stopwatch_mode and self.remaining_seconds > 0:
                # 秒錶暫停時記錄
                self._record_session(self.remaining_seconds, '秒錶')
                # 暫停時更新圓餅圖
                self.pieChartUpdateRequested.emit()
            # 倒計時已在 _on_finish 中記錄
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


class FinalSageWindow(QtWidgets.QMainWindow):
    toggleRequested = QtCore.pyqtSignal()
    def __init__(self, controller=None, compact_mode=False):
        super().__init__()
        self.compact_mode = compact_mode
        self.setWindowTitle('個體名：大賢者')
        self.setMinimumSize(560, 560)
        self.setStyleSheet(SAGE_STYLE)
        self.controller = controller or PomodoroController(self)

        root = QtWidgets.QWidget()
        root.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        self.setCentralWidget(root)

        self.main_layout = QtWidgets.QGridLayout(root)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.bg = SageBackground(root)
        self.bg.lower()

        self.overlay = QtWidgets.QWidget(root)
        self.overlay.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.overlay.setStyleSheet('background: transparent;')
        overlay_layout = QtWidgets.QVBoxLayout(self.overlay)
        overlay_layout.setContentsMargins(0, 0, 0, 0)
        overlay_layout.addStretch(1)

        self.disc = GreatSageDisc(compact_mode=compact_mode)
        self.disc.setFixedSize(700 if compact_mode else 760, 700 if compact_mode else 760)
        overlay_layout.addWidget(self.disc, alignment=QtCore.Qt.AlignCenter)
        overlay_layout.addStretch(1)

        self.calendar_summary_widget = QtWidgets.QFrame(root)
        self.calendar_summary_widget.setStyleSheet(
            "background: transparent;"
            " border: none;"
        )
        self.calendar_summary_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        summary_layout = QtWidgets.QVBoxLayout(self.calendar_summary_widget)
        summary_layout.setContentsMargins(0, 0, 0, 0)
        summary_layout.setSpacing(0)
        summary_layout.addStretch(1)

        self.calendar_summary_title = QtWidgets.QLabel('')
        self.calendar_summary_title.setAlignment(QtCore.Qt.AlignCenter)
        self.calendar_summary_title.setStyleSheet(f'color: #dffcff; font-size: {_ui_size(24, 18, compact_mode)}pt; font-weight: 800; letter-spacing: 4px;')
        self.calendar_summary_title.hide()

        self.calendar_summary_date = QtWidgets.QLabel('')
        self.calendar_summary_date.setAlignment(QtCore.Qt.AlignCenter)
        self.calendar_summary_date.setStyleSheet(f'color: #7fdcff; font-size: {_ui_size(14, 11, compact_mode)}pt; font-weight: 700;')
        self.calendar_summary_date.hide()

        # Create custom container for calendar items
        self.calendar_items_container = QtWidgets.QWidget()
        self.calendar_items_container.setStyleSheet('background: transparent;')
        self.calendar_items_layout = QtWidgets.QVBoxLayout(self.calendar_items_container)
        self.calendar_items_layout.setContentsMargins(0, 0, 0, 0)
        self.calendar_items_layout.setSpacing(12)
        self.calendar_items_layout.addStretch(1)
        
        summary_layout.addWidget(self.calendar_items_container, 0, QtCore.Qt.AlignCenter)
        summary_layout.addStretch(1)

        self.calendar_summary_widget.hide()
        self.main_layout.addWidget(self.calendar_summary_widget, 0, 0)

        self.main_layout.addWidget(self.bg, 0, 0)
        self.main_layout.addWidget(self.overlay, 0, 0)

        self.controller.updated.connect(self.disc.set_timer_state)
        self.controller.reset()

        # integrated notice widget (hidden until alarm)
        self.notice_widget = QtWidgets.QWidget(root)
        notice_layout = QtWidgets.QGridLayout(self.notice_widget)
        self.notice_bg = MagicBackgroundNotice(self.notice_widget)
        self.notice_diamond = SageSpeakingDiamond(self.notice_widget, compact_mode=compact_mode)
        notice_layout.addWidget(self.notice_bg, 0, 0)
        notice_layout.addWidget(self.notice_diamond, 0, 0, QtCore.Qt.AlignCenter)
        notice_layout.setContentsMargins(0, 0, 0, 0)
        self.notice_widget.hide()
        self.main_layout.addWidget(self.notice_widget, 0, 0)

        # connect alarm signals to switch UI
        try:
            self.controller.alarmStarted.connect(self._enter_notice_mode)
            self.controller.alarmStopped.connect(self._exit_notice_mode)
        except Exception:
            pass

    def set_mode_status(self, text='', visible=False):
        try:
            self.disc.set_status_override(text if visible else '')
        except Exception:
            pass

    def show_calendar_detail(self):
        try:
            self.disc.hide()
            self.calendar_summary_widget.show()
        except Exception:
            pass

    def show_calendar_home(self):
        try:
            self.calendar_summary_widget.hide()
            self.disc.show()
        except Exception:
            pass

    def show_calendar_summary(self, selected_date, events):
        try:
            self.disc.hide()
            self.calendar_summary_widget.show()
            if selected_date is not None:
                self.calendar_summary_date.setText(selected_date.strftime('%Y年%m月%d日'))
            else:
                self.calendar_summary_date.setText('')
            
            # Clear previous items
            while self.calendar_items_layout.count() > 0:
                item = self.calendar_items_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            # Add top stretch
            self.calendar_items_layout.addStretch(1)
            
            if events:
                for event in events:
                    if isinstance(event, dict):
                        time_text = event.get('time', '')
                        task_text = event.get('task', event.get('text', ''))
                    else:
                        time_text = ''
                        task_text = str(event)
                    # Add large spacing between time and task
                    item_text = f'{time_text}          {task_text}'.strip()
                    
                    # Create label for each event
                    event_label = QtWidgets.QLabel(item_text)
                    event_label.setAlignment(QtCore.Qt.AlignCenter)
                    event_label.setFont(QtGui.QFont('SimSun-ExtB', 20, QtGui.QFont.Bold))
                    event_label.setStyleSheet('color: #ffffff; letter-spacing: 2px;')
                    self.calendar_items_layout.addWidget(event_label)
            else:
                empty_label = QtWidgets.QLabel('這一天還沒有安排')
                empty_label.setAlignment(QtCore.Qt.AlignCenter)
                empty_label.setFont(QtGui.QFont('SimSun-ExtB', 20, QtGui.QFont.Bold))
                empty_label.setStyleSheet('color: #ffffff; letter-spacing: 2px;')
                self.calendar_items_layout.addWidget(empty_label)
            
            # Add bottom stretch
            self.calendar_items_layout.addStretch(1)
        except Exception:
            pass

    def _enter_notice_mode(self):
        try:
            # size the diamond to match the main disc
            try:
                ds = self.disc.size()
                self.notice_diamond.setFixedSize(ds)
            except Exception:
                pass
            self.overlay.hide()
            self.bg.hide()
            self.notice_widget.show()
            self.notice_widget.raise_()
        except Exception:
            pass

    def _exit_notice_mode(self):
        try:
            self.notice_widget.hide()
            self.bg.show()
            self.overlay.show()
            self.bg.raise_()
            self.overlay.raise_()
        except Exception:
            pass

    def resizeEvent(self, event):
        super().resizeEvent(event)
        rect = self.centralWidget().rect()
        self.bg.setGeometry(rect)
        self.overlay.setGeometry(rect)
        target_ratio = 0.74 if self.compact_mode else 0.82
        disc_min = 480 if self.compact_mode else 520
        disc_size = min(max(720, int(min(rect.width(), rect.height()) * target_ratio)), min(rect.width(), rect.height()) - 40)
        disc_size = max(disc_min, disc_size)
        self.disc.setFixedSize(disc_size, disc_size)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Q:
            self.toggleRequested.emit()
            return
        if event.key() == QtCore.Qt.Key_Escape:
            QtWidgets.QApplication.closeAllWindows()
            return
        super().keyPressEvent(event)

    def mousePressEvent(self, event):
        # if in notice mode, clicking anywhere on main should stop the alarm and restore UI
        try:
            if getattr(self, 'notice_widget', None) and self.notice_widget.isVisible():
                try:
                    # stop alarm via controller
                    if self.controller:
                        self.controller.stop_alarm()
                except Exception:
                    pass
                return
        except Exception:
            pass
        super().mousePressEvent(event)

    def _enter_alarm_mode(self):
        try:
            self._prev_editor_index = self.editor_stack.currentIndex()
            self.editor_stack.setCurrentWidget(self.alarm_panel)
            self.alarm_panel.show()
        except Exception:
            pass

    def _exit_alarm_mode(self):
        try:
            self.alarm_panel.hide()
            self.editor_stack.setCurrentIndex(self._prev_editor_index)
        except Exception:
            pass


class MenuSageWindow(QtWidgets.QMainWindow):
    toggleRequested = QtCore.pyqtSignal()
    def __init__(self, controller=None, compact_mode=False, main_window=None):
        super().__init__()
        self.compact_mode = compact_mode
        self.main_window = main_window
        self.setWindowTitle('個體名：大賢者 - 功能選單')
        self.setMinimumSize(400, 520)  # 盡量保留左右雙窗排版的可用寬度
        self.setStyleSheet(SAGE_STYLE)
        self.controller = controller or PomodoroController(self)

        root = QtWidgets.QWidget()
        root.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        self.setCentralWidget(root)

        self.main_layout = QtWidgets.QGridLayout(root)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.bg = SageBackground(root)
        self.bg.lower()

        overlay = QtWidgets.QWidget(root)
        overlay.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        overlay.setStyleSheet('background: transparent;')
        overlay_layout = QtWidgets.QVBoxLayout(overlay)
        overlay_layout.setContentsMargins(24 if compact_mode else 28, 24 if compact_mode else 28, 24 if compact_mode else 28, 24 if compact_mode else 28)
        overlay_layout.setSpacing(14 if compact_mode else 18)

        title = QtWidgets.QLabel('功能選單')
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet(f'color: #dffcff; font-size: {_ui_size(22, 18, compact_mode)}pt; font-weight: 700; letter-spacing: 4px;')
        overlay_layout.addWidget(title)

        subtitle = QtWidgets.QLabel('系統存取')
        subtitle.setAlignment(QtCore.Qt.AlignCenter)
        subtitle.setStyleSheet(f'color: #7fdcff; font-size: {_ui_size(10, 9, compact_mode)}pt; letter-spacing: 3px;')
        overlay_layout.addWidget(subtitle)

        self.menu_panel = QtWidgets.QFrame()
        self.menu_panel.setObjectName('menuPanel')
        menu_layout = QtWidgets.QVBoxLayout(self.menu_panel)
        menu_layout.setContentsMargins(24, 24, 24, 24)
        menu_layout.setSpacing(18)

        self.buttons = []
        names = ['番茄鐘', '待辦清單', '進度追蹤', '行事曆']
        for index, name in enumerate(names):
            button = QtWidgets.QPushButton(name)
            button.setMinimumHeight(90 if compact_mode else 100)
            button.setStyleSheet(f'font-size: {_ui_size(22, 18, compact_mode)}px; font-weight: 800;')
            button.setCheckable(True)
            button.clicked.connect(lambda checked=False, i=index: self.set_active(i))
            menu_layout.addWidget(button)
            self.buttons.append(button)

        self.menu_hint = QtWidgets.QLabel('')
        self.menu_hint.setWordWrap(True)
        self.menu_hint.setAlignment(QtCore.Qt.AlignCenter)
        self.menu_hint.setStyleSheet(f'color: #d9f7ff; font-size: {_ui_size(12, 10, compact_mode)}pt;')
        menu_layout.addWidget(self.menu_hint)

        self.editor_stack = QtWidgets.QStackedWidget()
        self.pomodoro_editor = PomodoroPanel(self.controller, compact_mode=self.compact_mode)
        self.editor_stack.addWidget(self.pomodoro_editor)
        self.editor_stack.addWidget(self._build_placeholder('待辦清單 尚未接上'))
        self.editor_stack.addWidget(self._build_placeholder('進度追蹤 尚未接上'))
        self.calendar_panel = CalendarPanel(compact_mode=self.compact_mode)
        self.editor_stack.addWidget(self.calendar_panel)
        menu_layout.addWidget(self.editor_stack)
        menu_layout.addStretch(1)

        try:
            self.calendar_panel.dateOpened.connect(self._enter_calendar_detail)
            self.calendar_panel.backRequested.connect(self._exit_calendar_detail)
            self.calendar_panel.eventsChanged.connect(self._sync_calendar_summary)
        except Exception:
            pass

        overlay_layout.addWidget(self.menu_panel, stretch=1)
        overlay_layout.addStretch(1)
        self.main_layout.addWidget(self.bg, 0, 0)
        self.main_layout.addWidget(overlay, 0, 0)

        self.set_active(0)
        self.controller.reset()

        # alarm mode controls
        self._prev_editor_index = 0
        self.alarm_panel = QtWidgets.QFrame()
        alarm_layout = QtWidgets.QVBoxLayout(self.alarm_panel)
        alarm_layout.setContentsMargins(16, 16, 16, 16)
        alarm_layout.addStretch(1)
        self.alarm_button = QtWidgets.QPushButton('關閉鬧鐘')
        self.alarm_button.setMinimumHeight(108 if compact_mode else 120)
        self.alarm_button.setStyleSheet(f"font-size:{_ui_size(28, 22, compact_mode)}px; font-weight:800; background: rgba(7,16,29,205); color:#e6fbff; border-radius:12px;")
        alarm_layout.addWidget(self.alarm_button, alignment=QtCore.Qt.AlignCenter)
        alarm_layout.addStretch(1)
        self.alarm_panel.hide()
        self.editor_stack.addWidget(self.alarm_panel)
        # connect alarm signals
        try:
            self.controller.alarmStarted.connect(self._enter_alarm_mode)
            self.controller.alarmStopped.connect(self._exit_alarm_mode)
        except Exception:
            pass
        self.alarm_button.clicked.connect(lambda: self.controller.stop_alarm())

    def _build_placeholder(self, text):
        label = QtWidgets.QLabel(text)
        label.setAlignment(QtCore.Qt.AlignCenter)
        label.setWordWrap(True)
        label.setStyleSheet(f'font-size: {_ui_size(13, 11, self.compact_mode)}pt; color: #bdefff; padding: {12 if self.compact_mode else 16}px;')
        return label


    def set_active(self, index):
        for i, button in enumerate(self.buttons):
            button.setChecked(i == index)
        self.editor_stack.setCurrentIndex(index)
        hints = [
            '',
            '待辦清單 尚未接上',
            '進度追蹤 尚未接上',
            '行事曆',
        ]
        self.menu_hint.setText(hints[index])
        if index == 3:
            try:
                self.calendar_panel.show_month_view(emit_signal=False)
            except Exception:
                pass
            if self.main_window is not None:
                try:
                    self.main_window.show_calendar_home()
                except Exception:
                    pass
        else:
            if self.main_window is not None:
                try:
                    self.main_window.set_mode_status('', False)
                except Exception:
                    pass
                try:
                    self.main_window.show_calendar_home()
                except Exception:
                    pass

    def _enter_calendar_detail(self, selected_date=None):
        if self.main_window is not None:
            try:
                date_value = selected_date or self.calendar_panel.selected_date()
                events = self.calendar_panel.get_events_for_selected_date()
                self.main_window.show_calendar_summary(date_value, events)
                self.main_window.set_mode_status('', False)
            except Exception:
                pass

    def _exit_calendar_detail(self):
        if self.main_window is not None:
            try:
                self.main_window.show_calendar_home()
            except Exception:
                pass
        try:
            self.calendar_panel.show_month_view(emit_signal=False)
        except Exception:
            pass

    def _sync_calendar_summary(self, date_value=None):
        if self.main_window is None:
            return
        try:
            if not self.calendar_panel.is_detail_view():
                return
            selected_date = date_value or self.calendar_panel.selected_date()
            events = self.calendar_panel.get_events_for_selected_date()
            self.main_window.show_calendar_summary(selected_date, events)
        except Exception:
            pass

    def resizeEvent(self, event):
        super().resizeEvent(event)
        rect = self.centralWidget().rect()
        self.bg.setGeometry(rect)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Q:
            self.toggleRequested.emit()
            return
        if event.key() == QtCore.Qt.Key_Escape:
            QtWidgets.QApplication.closeAllWindows()
            return
        super().keyPressEvent(event)


SageEvolutionWindow = FinalSageWindow
SageWindow = FinalSageWindow
MainWindow = FinalSageWindow


def create_sage_windows(controller=None, compact_mode=False):
    controller = controller or PomodoroController()
    main_window = FinalSageWindow(controller=controller, compact_mode=compact_mode)
    menu_window = MenuSageWindow(controller=controller, compact_mode=compact_mode, main_window=main_window)
    return controller, main_window, menu_window


def arrange_sage_windows(app, main_window, menu_window, compact_mode=False):
    screens = list(app.screens()) if app is not None else []
    if len(screens) >= 2:
        for window, screen in ((main_window, screens[0]), (menu_window, screens[1])):
            geometry = screen.availableGeometry()
            window.setGeometry(geometry)
            if window.windowHandle():
                window.windowHandle().setScreen(screen)
            window.showFullScreen()
        main_window.raise_()
        main_window.activateWindow()
        return

    screen = app.primaryScreen() if app is not None else None
    geometry = screen.availableGeometry() if screen is not None else QtCore.QRect(0, 0, 1600, 900)
    gap = max(12, geometry.width() // 120)
    usable_width = max(1, geometry.width() - gap)

    main_min = max(1, main_window.minimumWidth())
    menu_min = max(1, menu_window.minimumWidth())

    main_width = max(main_min, int(usable_width * 0.58))
    menu_width = max(menu_min, usable_width - main_width)

    if main_width + menu_width > usable_width:
        menu_width = max(menu_min, usable_width - main_width)
    if main_width + menu_width > usable_width:
        main_width = max(main_min, usable_width - menu_width)

    if main_width + menu_width > usable_width:
        total_min = main_min + menu_min
        if total_min > usable_width and total_min > 0:
            ratio = main_min / total_min
            main_width = max(1, int(usable_width * ratio))
            menu_width = max(1, usable_width - main_width)
        else:
            main_width = max(1, usable_width // 2)
            menu_width = max(1, usable_width - main_width)

    main_geometry = QtCore.QRect(geometry.left(), geometry.top(), main_width, geometry.height())
    menu_geometry = QtCore.QRect(geometry.left() + main_width + gap, geometry.top(), max(1, menu_width), geometry.height())

    for window, win_geometry in ((main_window, main_geometry), (menu_window, menu_geometry)):
        window.setGeometry(win_geometry)
        window.showNormal()
        if window.windowHandle() and screen is not None:
            window.windowHandle().setScreen(screen)

    main_window.raise_()
    main_window.activateWindow()


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    compact_mode = len(app.screens()) < 2
    app.setFont(QtGui.QFont('Microsoft JhengHei', 9 if compact_mode else 10))
    controller, w, menu_w = create_sage_windows(compact_mode=compact_mode)
    arrange_sage_windows(app, w, menu_w, compact_mode=compact_mode)
    app.exec_()

