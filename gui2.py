import os
import sys
from pathlib import Path

_venv_root = Path(sys.executable).resolve().parent.parent
_qt_plugins_path = _venv_root / 'Lib' / 'site-packages' / 'PyQt5' / 'Qt5' / 'plugins'
_qt_platforms_path = _qt_plugins_path / 'platforms'
if _qt_platforms_path.exists():
    os.environ.setdefault('QT_QPA_PLATFORM_PLUGIN_PATH', str(_qt_platforms_path))
    os.environ.setdefault('QT_PLUGIN_PATH', str(_qt_plugins_path))

from PyQt5 import QtWidgets, QtCore, QtGui, QtMultimedia
import random
import math
import json
from datetime import datetime


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
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = {}  # {活動名稱: 分鐘數}
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
        
        # 沒有數據時顯示無資料訊息
        if not self.data or sum(self.data.values()) == 0:
            painter.setPen(QtGui.QColor(100, 200, 255))
            painter.setFont(QtGui.QFont('Microsoft JhengHei', 18, QtGui.QFont.Bold))
            
            view_text = {'day': '今日', 'week': '本週', 'month': '本月', 'year': '本年'}.get(self.view_mode, '本期')
            painter.drawText(self.rect(), QtCore.Qt.AlignCenter, f'{view_text}\n暫無統計數據')
            return

        # 繪製日期標題（西元年月日）
        painter.setFont(QtGui.QFont('Microsoft JhengHei', 14, QtGui.QFont.Bold))
        painter.setPen(QtGui.QColor(255, 255, 255))  # 白色
        date_str = self.current_date.strftime('%Y年%m月%d日')
        painter.drawText(0, 5, self.width(), 25, QtCore.Qt.AlignCenter, date_str)

        # 計算佈局：左邊圓餅圖，右邊圖例
        title_height = 30
        available_height = self.height() - title_height
        
        # 右邊圖例預留寬度
        legend_width = 150
        pie_area_width = self.width() - legend_width
        
        # 圓餅圖直徑 = pie_area_width * 3/4，並限制不超過高度
        pie_size = min(pie_area_width * 0.75, available_height)
        pie_x = (pie_area_width - pie_size) / 2
        pie_y = title_height + (available_height - pie_size) / 2
        rect = QtCore.QRectF(pie_x, pie_y, pie_size, pie_size)

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
            painter.drawPie(rect, int(start_angle), int(angle))

            start_angle += angle

        # 繪製圖例（右邊，小字體）
        legend_x = pie_area_width + 10
        legend_start_y = title_height + 15
        painter.setFont(QtGui.QFont('Microsoft JhengHei', 9, QtGui.QFont.Bold))

        sorted_items = sorted(self.data.items(), key=lambda x: x[1], reverse=True)
        for idx, (activity, minutes) in enumerate(sorted_items):
            if minutes <= 0:
                continue
            color = get_neon_color(activity)

            legend_y = int(legend_start_y + idx * 24)

            # 顏色方塊（較小）
            painter.setBrush(color)
            painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255, 200), 1))
            painter.drawRect(QtCore.QRectF(legend_x, legend_y, 12, 12))

            # 標籤文字（小字體）
            painter.setPen(QtGui.QColor(255, 255, 255))
            percentage = (minutes / total) * 100
            label_text = f'{activity} {minutes}m'
            painter.drawText(int(legend_x + 16), legend_y, 120, 14,
                            QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, label_text)




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
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(400, 400)
        # no subtitle / typing text per user request
        self.display_text = ""
        self.full_text = ""

    def _type_text(self):
        return

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        w, h = self.width(), self.height()
        center = QtCore.QPoint(w // 2, h // 2)
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
        painter.setFont(QtGui.QFont('Microsoft JhengHei', 22, QtGui.QFont.Bold))
        painter.drawText(QtCore.QRect(w//2 + 35, h//2 - 110, 60, 120), QtCore.Qt.AlignCenter, "專\n注\n模\n式")
        font_main = QtGui.QFont('SimSun-ExtB', 68, QtGui.QFont.Bold)
        painter.setFont(font_main)
        painter.drawText(QtCore.QRect(0, 0, w, h), QtCore.Qt.AlignCenter, "專\n注\n者")
        font_side = QtGui.QFont('SimSun-ExtB', 30, QtGui.QFont.Bold)
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
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(700, 700)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.remaining_text = '25:00'
        self.progress = 0.0
        self.running = False
        self.activity_text = '讀書中'

    def set_timer_state(self, remaining_seconds, progress, running, activity_text):
        self.remaining_text = f'{remaining_seconds // 60:02d}:{remaining_seconds % 60:02d}'
        self.progress = max(0.0, min(1.0, progress))
        self.running = running
        self.activity_text = activity_text
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
        painter.setFont(QtGui.QFont('Microsoft JhengHei', max(10, int(self.height() * 0.03))))
        painter.drawText(QtCore.QRect(0, int(self.height() * 0.22), self.width(), 40), QtCore.Qt.AlignCenter, 'ユニークスキル')

        main_font = QtGui.QFont('SimSun-ExtB', max(48, int(self.height() * 0.16)), QtGui.QFont.Bold)
        painter.setFont(main_font)
        painter.drawText(QtCore.QRect(0, int(self.height() * 0.30), self.width(), int(self.height() * 0.22)), QtCore.Qt.AlignCenter, '大賢者')

        rect_w = int(self.width() * 0.36)
        rect_h = max(40, int(self.height() * 0.08))
        rect_x = int((self.width() - rect_w) / 2)
        rect_y = int(self.height() * 0.60)
        rect = QtCore.QRect(rect_x, rect_y, rect_w, rect_h)

        painter.setPen(QtGui.QPen(QtGui.QColor(50, 90, 80), 3))
        painter.drawRect(rect)
        painter.setFont(QtGui.QFont('Microsoft JhengHei', max(10, int(self.height() * 0.035)), QtGui.QFont.Bold))
        painter.drawText(rect, QtCore.Qt.AlignCenter, self.remaining_text)

        status_font = QtGui.QFont('Microsoft JhengHei', max(10, int(self.height() * 0.03)), QtGui.QFont.Bold)
        painter.setFont(status_font)
        painter.setPen(QtGui.QColor(45, 85, 78))
        status_text = self.activity_text
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
                        if not k in ('讀書中', '修習中') and not k.endswith('.mp3'):
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
    def __init__(self, controller=None):
        super().__init__()
        self.setWindowTitle('個體名：大賢者')
        self.setMinimumSize(900, 700)
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

        self.disc = GreatSageDisc()
        self.disc.setFixedSize(760, 760)
        overlay_layout.addWidget(self.disc, alignment=QtCore.Qt.AlignCenter)
        overlay_layout.addStretch(1)

        self.main_layout.addWidget(self.bg, 0, 0)
        self.main_layout.addWidget(self.overlay, 0, 0)

        self.controller.updated.connect(self.disc.set_timer_state)
        self.controller.reset()

        # integrated notice widget (hidden until alarm)
        self.notice_widget = QtWidgets.QWidget(root)
        notice_layout = QtWidgets.QGridLayout(self.notice_widget)
        self.notice_bg = MagicBackgroundNotice(self.notice_widget)
        self.notice_diamond = SageSpeakingDiamond(self.notice_widget)
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
        disc_size = min(max(720, int(min(rect.width(), rect.height()) * 0.82)), min(rect.width(), rect.height()) - 40)
        disc_size = max(520, disc_size)
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
    def __init__(self, controller=None):
        super().__init__()
        self.setWindowTitle('個體名：大賢者 - 功能選單')
        self.setMinimumSize(520, 520)  # 正方形視窗
        self.setStyleSheet(SAGE_STYLE)
        self.controller = controller or PomodoroController(self)
        self._add_status_label = '新增...'
        self._status_defaults = ['讀書中', '休息中']
        self._status_file = os.path.join(os.path.dirname(__file__), 'status_options.json')
        self._status_options = self._load_status_options()

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
        overlay_layout.setContentsMargins(28, 28, 28, 28)
        overlay_layout.setSpacing(18)

        title = QtWidgets.QLabel('功能選單')
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet('color: #dffcff; font-size: 22pt; font-weight: 700; letter-spacing: 4px;')
        overlay_layout.addWidget(title)

        subtitle = QtWidgets.QLabel('系統存取')
        subtitle.setAlignment(QtCore.Qt.AlignCenter)
        subtitle.setStyleSheet('color: #7fdcff; font-size: 10pt; letter-spacing: 3px;')
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
            button.setMinimumHeight(100)
            button.setStyleSheet('font-size: 22px; font-weight: 800;')
            button.setCheckable(True)
            button.clicked.connect(lambda checked=False, i=index: self.set_active(i))
            menu_layout.addWidget(button)
            self.buttons.append(button)

        self.menu_hint = QtWidgets.QLabel('')
        self.menu_hint.setWordWrap(True)
        self.menu_hint.setAlignment(QtCore.Qt.AlignCenter)
        self.menu_hint.setStyleSheet('color: #d9f7ff; font-size: 12pt;')
        menu_layout.addWidget(self.menu_hint)

        self.editor_stack = QtWidgets.QStackedWidget()
        self.pomodoro_editor = self._build_pomodoro_editor()
        self.editor_stack.addWidget(self.pomodoro_editor)
        self.editor_stack.addWidget(self._build_placeholder('待辦清單 尚未接上'))
        self.editor_stack.addWidget(self._build_placeholder('進度追蹤 尚未接上'))
        self.editor_stack.addWidget(self._build_placeholder('行事曆 尚未接上'))
        menu_layout.addWidget(self.editor_stack)
        menu_layout.addStretch(1)

        overlay_layout.addWidget(self.menu_panel, stretch=1)
        overlay_layout.addStretch(1)
        self.main_layout.addWidget(self.bg, 0, 0)
        self.main_layout.addWidget(overlay, 0, 0)

        self.set_active(0)
        self.controller.updated.connect(self._sync_controls)
        self.controller.sessionRecorded.connect(self._on_session_recorded)
        self.controller.pieChartUpdateRequested.connect(self._refresh_pie_chart)
        self.controller.reset()

        # alarm mode controls
        self._prev_editor_index = 0
        self.alarm_panel = QtWidgets.QFrame()
        alarm_layout = QtWidgets.QVBoxLayout(self.alarm_panel)
        alarm_layout.setContentsMargins(16, 16, 16, 16)
        alarm_layout.addStretch(1)
        self.alarm_button = QtWidgets.QPushButton('關閉鬧鐘')
        self.alarm_button.setMinimumHeight(120)
        self.alarm_button.setStyleSheet("font-size:28px; font-weight:800; background: rgba(7,16,29,205); color:#e6fbff; border-radius:12px;")
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
        label.setStyleSheet('font-size: 13pt; color: #bdefff; padding: 16px;')
        return label

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
                # restore to current controller state if user canceled
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
        # keep input readable: black text on white field
        dialog.setStyleSheet(
            'QLabel { color: #111111; }'
            'QLineEdit { color: #000000; background: #ffffff; border: 1px solid #888888; padding: 4px; }'
            'QPushButton { color: #111111; background: #f0f0f0; border: 1px solid #999999; padding: 6px 10px; }'
        )
        ok = dialog.exec_() == QtWidgets.QDialog.Accepted
        return dialog.textValue(), ok

    def _build_pomodoro_editor(self):
        panel = QtWidgets.QFrame()
        panel.setObjectName('pomodoroCore')
        layout = QtWidgets.QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        form = QtWidgets.QGridLayout()
        time_label = QtWidgets.QLabel('工作時間(分鐘)')
        time_label.setStyleSheet('font-size: 14pt; font-weight: 700;')
        form.addWidget(time_label, 0, 0)
        self.work_input = QtWidgets.QSpinBox()
        self.work_input.setRange(0, 180)
        self.work_input.setValue(25)
        self.work_input.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.work_input.setMinimumHeight(96)
        self.work_input.setStyleSheet('font-size: 42px; font-weight: 700;')
        form.addWidget(self.work_input, 0, 1)
        minute_text = QtWidgets.QLabel('MIN')
        minute_text.setStyleSheet('font-size: 20px; font-weight: 700;')
        form.addWidget(minute_text, 0, 2)
        form.setColumnStretch(0, 1)
        form.setColumnStretch(1, 2)
        form.setColumnStretch(2, 1)
        layout.addLayout(form)

        btn_row = QtWidgets.QHBoxLayout()
        btn_row.setSpacing(10)
        self.toggle_btn = QtWidgets.QPushButton('開始')
        self.reset_btn = QtWidgets.QPushButton('重開')
        
        # 按鈕樣式：有 hover 和 pressed 效果
        btn_style = (
            "font-size: 24px; font-weight: 800; background: rgba(7,16,29,205); "
            "border:1px solid rgba(117,220,255,80); color: #e6fbff; border-radius:12px; "
            "padding: 10px;"
        )
        btn_hover_pressed = (
            "QPushButton:hover { background: rgba(33, 62, 95, 235); border: 1px solid rgba(168, 241, 255, 160); }"
            "QPushButton:pressed { background: rgba(0, 200, 255, 150); border: 2px solid rgba(0, 255, 200, 255); }"
        )
        
        for button in (self.toggle_btn, self.reset_btn):
            button.setMinimumHeight(112)
            button.setStyleSheet(btn_style + btn_hover_pressed)
        btn_row.addWidget(self.toggle_btn)
        btn_row.addWidget(self.reset_btn)
        layout.addLayout(btn_row)

        mode_row = QtWidgets.QHBoxLayout()
        mode_row.setSpacing(8)
        self.mode_combo = QtWidgets.QComboBox()
        self.mode_combo.addItems(self._status_options)
        self.mode_combo.addItem(self._add_status_label)
        self.mode_combo.setMinimumHeight(62)
        self.mode_combo.setStyleSheet('background: rgba(7,16,29,205); color: #effcff; padding: 8px; border-radius: 8px; font-size:16px;')
        mode_row.addWidget(self.mode_combo, 1)
        self.mode_delete_btn = QtWidgets.QPushButton('-')
        self.mode_delete_btn.setFixedSize(62, 62)
        self.mode_delete_btn.setStyleSheet('font-size: 28px; font-weight: 900; background: rgba(7,16,29,205); border:1px solid rgba(117,220,255,80); color: #e6fbff; border-radius:12px;')
        mode_row.addWidget(self.mode_delete_btn)
        layout.addLayout(mode_row)

        stats_row = QtWidgets.QHBoxLayout()
        stats_row.setSpacing(8)
        self.stats_buttons = []
        button_styles_unchecked = (
            'font-size: 18px; font-weight: 800; background: rgba(7,16,29,205); '
            'border:1px solid rgba(117,220,255,80); color: #e6fbff; border-radius:12px;'
        )
        button_styles_checked = (
            'font-size: 18px; font-weight: 800; background: rgba(0,255,150,100); '
            'border:2px solid rgba(0,255,150,255); color: #000000; border-radius:12px;'
        )
        # 只保留「當天」按鈕
        button = QtWidgets.QPushButton('當天')
        button.setMinimumHeight(54)
        button.setStyleSheet(
            button_styles_unchecked + 
            f'\nQPushButton:checked {{ {button_styles_checked} }}'
        )
        button.setCheckable(True)
        button.setChecked(True)
        stats_row.addWidget(button)
        self.stats_buttons.append(button)
        stats_row.addStretch(1)
        layout.addLayout(stats_row)

        # === 圓餅圖面板（含日期導航） - 初始隱藏 ===
        self.pie_container = QtWidgets.QFrame()
        self.pie_container.setStyleSheet('background: rgba(7,16,29,180); border: 1px solid rgba(0,255,200,60); border-radius: 12px;')
        self.pie_container.hide()  # 初始隱藏
        pie_layout = QtWidgets.QVBoxLayout(self.pie_container)
        pie_layout.setContentsMargins(8, 8, 8, 8)  # 減少邊距
        pie_layout.setSpacing(8)  # 減少間距

        # 日期導航行
        nav_row = QtWidgets.QHBoxLayout()
        nav_row.setSpacing(6)

        self.date_prev_btn = QtWidgets.QPushButton('◀ 前一天')
        self.date_prev_btn.setMaximumWidth(100)
        self.date_prev_btn.setMinimumHeight(28)
        self.date_prev_btn.setStyleSheet('font-size: 10px; font-weight: 700; background: rgba(0,150,255,80); border: 1px solid rgba(0,150,255,150); color: #fff; border-radius: 6px;')
        nav_row.addWidget(self.date_prev_btn)

        self.date_display = QtWidgets.QLabel('今日')
        self.date_display.setAlignment(QtCore.Qt.AlignCenter)
        self.date_display.setStyleSheet('font-size: 12px; font-weight: 700; color: #ffffff;')
        nav_row.addWidget(self.date_display, 1)

        self.date_next_btn = QtWidgets.QPushButton('後一天 ▶')
        self.date_next_btn.setMaximumWidth(100)
        self.date_next_btn.setMinimumHeight(28)
        self.date_next_btn.setStyleSheet('font-size: 10px; font-weight: 700; background: rgba(0,150,255,80); border: 1px solid rgba(0,150,255,150); color: #fff; border-radius: 6px;')
        nav_row.addWidget(self.date_next_btn)

        pie_layout.addLayout(nav_row)

        self.daily_pie_chart = DailyPieChart()
        pie_layout.addWidget(self.daily_pie_chart, 1)

        layout.addWidget(self.pie_container, 2)

        self.record_panel = QtWidgets.QFrame()
        self.record_panel.setStyleSheet('background: rgba(7,16,29,180); border: 1px solid rgba(117,220,255,80); border-radius: 16px;')
        record_layout = QtWidgets.QVBoxLayout(self.record_panel)
        record_layout.setContentsMargins(12, 12, 12, 12)
        record_layout.setSpacing(6)
        self.record_title = QtWidgets.QLabel('本次紀錄')
        self.record_title.setAlignment(QtCore.Qt.AlignCenter)
        self.record_title.setStyleSheet('font-size: 16px; color: #ffffff; font-weight: 700;')
        self.record_text = QtWidgets.QLabel('尚未產生紀錄')
        self.record_text.setAlignment(QtCore.Qt.AlignCenter)
        self.record_text.setWordWrap(True)
        self.record_text.setStyleSheet('font-size: 36px; font-weight: 900; color: #ffffff;')
        record_layout.addWidget(self.record_title)
        record_layout.addWidget(self.record_text)
        layout.addWidget(self.record_panel, 1)

        # 初始化活動分配字典、查看日期和視圖模式
        self.daily_allocations = {}  # {活動: 分鐘數}
        self.viewing_date = datetime.now().date()  # 當前查看的日期
        self._view_mode = 'day'  # 'day', 'week', 'month', 'year' - 必須先初始化
        self._session_records_file = os.path.join(os.path.dirname(__file__), 'session_records.json')
        # 追蹤上一次設置的分鐘數，只有改變時才重新設置
        self._last_work_minutes = self.work_input.value()

        # 連接信號槽
        self.toggle_btn.clicked.connect(self._toggle_pomodoro)
        self.reset_btn.clicked.connect(self._reset_pomodoro)
        self.mode_combo.currentTextChanged.connect(self._on_mode_combo_changed)
        self.mode_delete_btn.clicked.connect(self._delete_current_status)
        self.date_prev_btn.clicked.connect(self._on_date_prev)
        self.date_next_btn.clicked.connect(self._on_date_next)
        self.stats_buttons[0].clicked.connect(self._on_show_today)      # 當天

        # 初始化加載當日統計（但不顯示圓餅圖，除非點「當天」）
        self._view_mode = 'day'

        return panel

    def _on_show_today(self):
        """點擊當天按鈕 - 顯示圓餅圖並刷新"""
        self._view_mode = 'day'
        self.viewing_date = datetime.now().date()
        self.date_prev_btn.show()
        self.date_next_btn.show()
        self.pie_container.show()  # 顯示圓餅圖容器
        self._refresh_pie_chart()

    def _on_date_prev(self):
        """前一天"""
        from datetime import timedelta
        self.viewing_date -= timedelta(days=1)
        self.pie_container.show()  # 確保容器顯示
        self._refresh_pie_chart()

    def _on_date_next(self):
        """後一天"""
        from datetime import timedelta
        self.viewing_date += timedelta(days=1)
        self.pie_container.show()  # 確保容器顯示
        self._refresh_pie_chart()

    def _refresh_pie_chart(self):
        """刷新圓餅圖顯示"""
        self._load_daily_statistics()
        self._update_date_display()
        self.daily_pie_chart.set_data(self.daily_allocations, self.viewing_date, self._view_mode)

    def _update_date_display(self):
        """更新日期顯示"""
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
        """根據 view_mode 從 session_records.json 讀取統計"""
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

                                # 根據 view_mode 判斷是否包含此記錄
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
        elif status_text == '休息中':
            status_text = '休息'
        minutes = max(1, int(round(float(seconds) / 60.0))) if seconds > 0 else 0
        self.record_text.setText(f'{status_text}\n{minutes} 分鐘')

        # 無論什麼視圖模式都自動刷新圓餅圖
        self._refresh_pie_chart()

    def _toggle_pomodoro(self):
        # 只有當用戶改變時間值時才重新設置
        # 暫停後按開始會直接繼續，不重新設定
        current_value = self.work_input.value()
        if current_value != self._last_work_minutes:
            # 時間值改變，重新設置
            self.controller.set_work_minutes(current_value)
            self._last_work_minutes = current_value
            self.record_text.setText('尚未產生紀錄')
        # 無論時間是否改變，都直接切換開始/暫停（繼續從暫停時間開始）
        self.controller.toggle()

    def _reset_pomodoro(self):
        # 重開會重新設置時間
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


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    app.setFont(QtGui.QFont('Microsoft JhengHei', 10))
    w = FinalSageWindow()
    w.showFullScreen()
    app.exec_()


SageEvolutionWindow = FinalSageWindow
SageWindow = FinalSageWindow
MainWindow = FinalSageWindow

