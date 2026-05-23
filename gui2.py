import os
import sys
import random
import json
from pathlib import Path
from datetime import datetime
import uuid
import requests
from io import BytesIO

from PyQt5 import QtWidgets, QtCore, QtGui, QtMultimedia

from pomodoro_feature import PomodoroController, PomodoroPanel
from calendar_feature import CalendarPanel
from todo_feature import TodoListPanel


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


def _screen_geometry():
    app = QtWidgets.QApplication.instance()
    if app is not None:
        screen = app.primaryScreen()
        if screen is not None:
            return screen.availableGeometry()
    return QtCore.QRect(0, 0, 1600, 900)


def _screen_scale(compact_mode=False):
    geometry = _screen_geometry()
    scale = min(geometry.width() / 1600.0, geometry.height() / 900.0, 1.0)
    return max(0.62, scale)


def _scaled(value, scale):
    return max(1, int(round(value * scale)))


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


# ---- Book Card Widget ----
class BookCard(QtWidgets.QWidget):
    """書籍卡片：顯示封面、進度條和百分比"""
    clicked = QtCore.pyqtSignal(str)  # 發出記錄ID信號
    
    def __init__(self, record_data, parent=None):
        super().__init__(parent)
        self.record_data = record_data
        self.cover_pixmap = None
        # Allow flexible sizing so grid can distribute space evenly
        self.setMinimumSize(200, 360)
        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        # enable mouse tracking to detect hover without pressing buttons
        self.setMouseTracking(True)
        self._cover_rect = QtCore.QRect()
        
        # 從本地文件夾加載封面
        self._load_cover_from_local()
    
    def _load_cover_from_local(self):
        """從本地文件夾加載書籍封面"""
        title = self.record_data.get('title', '').strip()
        
        if not title:
            self._create_placeholder()
            return
        
        # 構建本地文件路徑
        covers_dir = os.path.join(os.path.dirname(__file__), 'assets', 'book_covers')
        cover_path = os.path.join(covers_dir, f'{title}.jpg')
        
        # 嘗試加載圖片
        if os.path.isfile(cover_path):
            self.cover_pixmap = QtGui.QPixmap(cover_path)
            if not self.cover_pixmap.isNull():
                self.update()
                return
        
        # 如果文件不存在或加載失敗，使用佔位圖片
        self._create_placeholder()
    
    def _create_placeholder(self):
        """創建佔位圖片"""
        pixmap = QtGui.QPixmap(240, 360)
        pixmap.fill(QtGui.QColor(180, 180, 200))
        painter = QtGui.QPainter(pixmap)
        painter.setPen(QtGui.QColor(80, 80, 100))
        painter.setFont(QtGui.QFont('Microsoft JhengHei', 32, QtGui.QFont.Bold))
        painter.drawText(pixmap.rect(), QtCore.Qt.AlignCenter, '?')
        painter.end()
        self.cover_pixmap = pixmap
    
    def mousePressEvent(self, event):
        self.clicked.emit(self.record_data.get('id', ''))
        super().mousePressEvent(event)
    
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        # 繪製卡片背景（不顯示外框線）
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtGui.QColor(10, 30, 50))
        painter.drawRect(0, 0, self.width(), self.height())
        
        # 繪製封面
        cover_width = self.width() - 10
        cover_height = int(cover_width * 1.5)  # 保持 2:3 比例
        
        if self.cover_pixmap:
            scaled = self.cover_pixmap.scaledToWidth(cover_width, QtCore.Qt.SmoothTransformation)
            # 居中繪製
            x = (self.width() - scaled.width()) // 2
            y = 5
            painter.drawPixmap(x, y, scaled)
            cover_bottom = y + scaled.height()
            # 保存封面區域以供 hover 顯示資訊
            try:
                self._cover_rect = QtCore.QRect(x, y, scaled.width(), scaled.height())
            except Exception:
                self._cover_rect = QtCore.QRect()
        else:
            cover_bottom = cover_height + 5
            self._cover_rect = QtCore.QRect(5, 5, cover_width, cover_height)
        
        # 繪製進度條背景
        progress_y = cover_bottom + 8
        progress_rect = QtCore.QRect(5, progress_y, self.width() - 10, 6)
        painter.fillRect(progress_rect, QtGui.QColor(40, 40, 60))
        painter.setPen(QtGui.QPen(QtGui.QColor(100, 150, 180), 2))
        painter.drawRect(progress_rect)
        
        # 計算進度
        total = self.record_data.get('total_pages', 1)
        current = self.record_data.get('current_page', 0)
        progress = min(100, int(current / max(1, total) * 100))
        
        # 繪製進度條填充
        filled_width = int((self.width() - 10) * progress / 100)
        filled_rect = QtCore.QRect(5, progress_y, filled_width, 6)
        painter.fillRect(filled_rect, QtGui.QColor(100, 255, 150))
        
        # 不顯示百分比文字，只顯示進度條
        # 繪製書名（固定最多 3 行，超出在第三行末尾顯示 ...）
        title = self.record_data.get('title', '')

        title_font = QtGui.QFont('Microsoft JhengHei', 6)
        painter.setFont(title_font)
        painter.setPen(QtGui.QColor(200, 220, 240))

        fm = QtGui.QFontMetrics(title_font)
        text_x = 6
        text_width = max(10, self.width() - 12)
        line_height = fm.height()
        max_lines = 3

        # 優先在單詞邊界換行（若單詞過長則退回到字元分割），並限制為最多三行
        lines = []
        cur = ''
        overflowed = False
        words = title.split()
        for word in words:
            # 構建嘗試放入當前行的候選字串
            candidate = word if not cur else (cur + ' ' + word)
            if fm.horizontalAdvance(candidate) <= text_width:
                cur = candidate
                continue

            # 候選不合，若單詞本身可以放進一行，則換行把 cur 推入 lines
            if fm.horizontalAdvance(word) <= text_width:
                if cur:
                    lines.append(cur)
                    cur = word
                else:
                    # cur 為空但 candidate 仍不合（理論上不會發生），直接放 word
                    cur = word
                if len(lines) >= max_lines:
                    overflowed = True
                    break
                continue

            # 單詞本身也太長，需用字元分割（先將 cur 推入 lines）
            if cur:
                lines.append(cur)
                cur = ''
                if len(lines) >= max_lines:
                    overflowed = True
                    break

            part = ''
            for ch in word:
                if fm.horizontalAdvance(part + ch) <= text_width:
                    part += ch
                else:
                    lines.append(part)
                    part = ch
                    if len(lines) >= max_lines:
                        overflowed = True
                        break
            if overflowed:
                break
            if part:
                cur = part

        if cur and len(lines) < max_lines:
            lines.append(cur)

        # 只有在實際溢位（需要超過三行）時，才在最後顯示行加上省略號
        if overflowed:
            last = lines[max_lines - 1] if len(lines) >= max_lines else (lines[-1] if lines else '')
            while fm.horizontalAdvance(last + '...') > text_width and last:
                last = last[:-1]
            if len(lines) >= max_lines:
                lines = lines[:max_lines]
                lines[-1] = last + '...'
            else:
                # 少於三行但標記為 overflow（保險處理）
                if lines:
                    lines[-1] = last + '...'

        # 繪製書名字行（向上微調以配合較短的進度條）
        text_y = progress_y + 12
        for i, ln in enumerate(lines[:max_lines]):
            painter.drawText(text_x, text_y + i * line_height, text_width, line_height,
                             QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, ln)

        # 不顯示作者資訊（根據使用者要求）
    def mouseMoveEvent(self, event):
        # 顯示當前是否停留於封面上，若是則顯示已讀/總頁數與百分比
        pos = event.pos()
        if hasattr(self, '_cover_rect') and self._cover_rect.contains(pos):
            total = self.record_data.get('total_pages', 1)
            current = self.record_data.get('current_page', 0)
            pct = 0 if total <= 0 else int(current / max(1, total) * 100)
            title = self.record_data.get('title', '').strip()
            author = self.record_data.get('author', '').strip()
            parts = []
            if title:
                parts.append(title)
            if author:
                parts.append(f'作者: {author}')
            parts.append(f'已讀: {current} / {total} ({pct}%)')
            tip = '\n'.join(parts)
            QtWidgets.QToolTip.showText(self.mapToGlobal(pos), tip, self)
        else:
            QtWidgets.QToolTip.hideText()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        QtWidgets.QToolTip.hideText()
        super().leaveEvent(event)


# ---- Bookshelf Panel (左邊視窗，按類別分組顯示書籍卡片) ----
class BookshelfPanel(QtWidgets.QWidget):
    """書架面板：按類別分組顯示書籍，每行4本"""
    def __init__(self, parent=None, compact_mode=False):
        super().__init__(parent)
        self.compact_mode = compact_mode
        self.ui_scale = _screen_scale(compact_mode)
        self._data_file = os.path.join(os.path.dirname(__file__), 'progress_records.json')
        self._categories_file = os.path.join(os.path.dirname(__file__), 'book_categories.json')
        self.records = []
        self.categories = []
        self._last_column_count = None
        
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)
        
        # 標題
        title = QtWidgets.QLabel('我的書櫃')
        title.setAlignment(QtCore.Qt.AlignLeft)
        title.setStyleSheet('color: #dffcff; font-size: 16pt; font-weight: bold;')
        main_layout.addWidget(title)
        
        # 可滾動的書架區域
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.shelf_widget = QtWidgets.QWidget()
        self.shelf_layout = QtWidgets.QVBoxLayout(self.shelf_widget)
        self.shelf_layout.setContentsMargins(0, 0, 0, 0)
        self.shelf_layout.setSpacing(12)
        
        scroll_area.setWidget(self.shelf_widget)
        main_layout.addWidget(scroll_area, stretch=1)
        
        self.load_data()
        self.refresh_bookshelf()
    
    def load_data(self):
        """加載書籍和分類數據"""
        try:
            if os.path.isfile(self._data_file):
                with open(self._data_file, 'r', encoding='utf-8') as f:
                    self.records = json.load(f)
            else:
                self.records = []
        except Exception:
            self.records = []
        
        try:
            if os.path.isfile(self._categories_file):
                with open(self._categories_file, 'r', encoding='utf-8') as f:
                    self.categories = json.load(f)
            else:
                self.categories = []
        except Exception:
            self.categories = []
    
    def refresh_bookshelf(self):
        """刷新書架顯示，按類別分組（每行4本）"""
        # 清空現有布局
        while self.shelf_layout.count() > 0:
            item = self.shelf_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
        
        # 分組書籍
        books_by_category = {}
        for rec in self.records:
            cat = rec.get('category', '（未分類）')
            if cat not in books_by_category:
                books_by_category[cat] = []
            books_by_category[cat].append(rec)
        
        # 按字典順序顯示分類
        sorted_categories = sorted(books_by_category.keys())
        column_count = self._get_column_count()
        
        for category in sorted_categories:
            # 添加分類標題
            cat_label = QtWidgets.QLabel(category)
            cat_label.setStyleSheet('color: #7fdcff; font-size: 12pt; font-weight: bold; margin-top: 8px;')
            self.shelf_layout.addWidget(cat_label)
            
            # 按字母順序排列書籍
            books_in_cat = books_by_category[category]
            sorted_books = sorted(books_in_cat, key=lambda r: r.get('title', '').lower())
            
            # 使用 QGridLayout 實現自適應列布局
            grid_widget = QtWidgets.QWidget()
            grid_layout = QtWidgets.QGridLayout(grid_widget)
            grid_layout.setContentsMargins(0, 0, 0, 0)
            grid_layout.setSpacing(_scaled(20, self.ui_scale))
            # 為了讓書籍平均分配在整個視窗，為每一列設定相等的伸縮係數
            for c in range(column_count):
                grid_layout.setColumnStretch(c, 1)
            
            for idx, rec in enumerate(sorted_books):
                row = idx // column_count
                col = idx % column_count
                card = BookCard(rec, self)
                # 將卡片置中於欄位並靠上排列
                grid_layout.addWidget(card, row, col, alignment=QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop)
            
            self.shelf_layout.addWidget(grid_widget)
        
        # 添加底部伸縮
        self.shelf_layout.addStretch()

    def _get_column_count(self):
        available_width = max(1, self.width())
        card_width = _scaled(200, self.ui_scale)
        spacing = _scaled(20, self.ui_scale)
        estimated = max(1, available_width // max(1, card_width + spacing))
        return max(1, min(4, estimated))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        column_count = self._get_column_count()
        if column_count != self._last_column_count:
            self._last_column_count = column_count
            self.refresh_bookshelf()


# ---- Progress Tracker Panel ----
class ProgressTrackerPanel(QtWidgets.QWidget):
    """進度追蹤面板：上方編輯表單 + 下方記錄清單，儲存在 progress_records.json（書籍追蹤）"""
    show_bookshelf_requested = QtCore.pyqtSignal()  # 請求顯示書架的信號
    
    def __init__(self, parent=None, compact_mode=False):
        super().__init__(parent)
        self.compact_mode = compact_mode
        self._data_file = os.path.join(os.path.dirname(__file__), 'progress_records.json')
        self._categories_file = os.path.join(os.path.dirname(__file__), 'book_categories.json')
        self.records = []  # list of dicts
        self.categories = []  # list of category strings
        self._selected_record_id = None  # 追蹤當前選中的記錄ID
        self._current_page = 0  # 當前頁碼（0-indexed）
        self._items_per_page = 10  # 每頁顯示數量
        self.main_window = None  # 對左窗口的引用，用於更新封面

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # Top: form (編輯區)
        form = QtWidgets.QWidget()
        form_layout = QtWidgets.QFormLayout(form)
        form_layout.setLabelAlignment(QtCore.Qt.AlignRight)

        self.title_edit = QtWidgets.QLineEdit()
        self.author_edit = QtWidgets.QLineEdit()
        self.total_spin = QtWidgets.QSpinBox()
        self.total_spin.setRange(1, 100000)
        self.current_spin = QtWidgets.QSpinBox()
        self.current_spin.setRange(0, 100000)

        # 為書名添加自動完成功能
        self.title_completer = QtWidgets.QCompleter([])
        self.title_completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.title_completer.setCompletionMode(QtWidgets.QCompleter.PopupCompletion)
        self.title_edit.setCompleter(self.title_completer)

        form_layout.addRow('書名：', self.title_edit)
        form_layout.addRow('作者：', self.author_edit)
        form_layout.addRow('總頁數：', self.total_spin)
        form_layout.addRow('已讀頁數：', self.current_spin)
        
        # 分類選擇區
        category_layout = QtWidgets.QHBoxLayout()
        self.category_combo = QtWidgets.QComboBox()
        self.category_combo.addItem('（未分類）')  # 預設選項
        self.add_category_btn = QtWidgets.QPushButton('+')
        self.add_category_btn.setMaximumWidth(40)
        self.add_category_btn.clicked.connect(self._on_add_category)
        category_layout.addWidget(self.category_combo)
        category_layout.addWidget(self.add_category_btn)
        form_layout.addRow('分類：', category_layout)

        btn_row = QtWidgets.QHBoxLayout()
        self.add_btn = QtWidgets.QPushButton('新增')
        self.update_btn = QtWidgets.QPushButton('更新')
        self.remove_btn = QtWidgets.QPushButton('移除')
        self.update_btn.hide()  # 初始時隱藏「更新」按鈕
        btn_row.addWidget(self.add_btn)
        btn_row.addWidget(self.update_btn)
        btn_row.addWidget(self.remove_btn)
        form_layout.addRow(btn_row)

        # 在表單上安裝事件過濾器以處理背景點擊
        form.installEventFilter(self)
        main_layout.addWidget(form, stretch=0)

        # Bottom: list (已紀錄書目)
        list_container = QtWidgets.QWidget()
        list_layout = QtWidgets.QVBoxLayout(list_container)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(6)
        header = QtWidgets.QLabel('閱讀紀錄（選擇以編輯）')
        header.setAlignment(QtCore.Qt.AlignLeft)
        list_layout.addWidget(header)
        self.list_widget = QtWidgets.QListWidget()
        list_layout.addWidget(self.list_widget)
        
        # 分頁控件
        pagination_widget = QtWidgets.QWidget()
        pagination_layout = QtWidgets.QHBoxLayout(pagination_widget)
        pagination_layout.setContentsMargins(0, 0, 0, 0)
        pagination_layout.setSpacing(6)
        
        self.prev_btn = QtWidgets.QPushButton('← 上一頁')
        self.prev_btn.setMaximumWidth(80)
        self.page_label = QtWidgets.QLabel('第 1 頁')
        self.page_label.setAlignment(QtCore.Qt.AlignCenter)
        self.next_btn = QtWidgets.QPushButton('下一頁 →')
        self.next_btn.setMaximumWidth(80)
        
        pagination_layout.addWidget(self.prev_btn)
        pagination_layout.addStretch()
        pagination_layout.addWidget(self.page_label)
        pagination_layout.addStretch()
        pagination_layout.addWidget(self.next_btn)
        
        list_layout.addWidget(pagination_widget)
        main_layout.addWidget(list_container, stretch=1)

        # signal connections
        self.add_btn.clicked.connect(self._on_add)
        self.update_btn.clicked.connect(self._on_update)
        self.remove_btn.clicked.connect(self._on_remove)
        self.list_widget.currentItemChanged.connect(self._on_select_item)
        self.prev_btn.clicked.connect(self._on_prev_page)
        self.next_btn.clicked.connect(self._on_next_page)
        
        # 在表單上安裝事件過濾器以處理背景點擊
        form.installEventFilter(self)
        # 在列表上安裝事件過濾器以處理背景點擊
        self.list_widget.installEventFilter(self)

        self.load_categories()
        self.load_records()
        self._update_title_completer()  # 初始化自動完成列表
        self.refresh_list()
        self._update_button_state()  # 初始化按鈕狀態

    def load_records(self):
        try:
            if os.path.isfile(self._data_file):
                with open(self._data_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                if isinstance(loaded, list):
                    self.records = loaded
                else:
                    self.records = []
            else:
                self.records = []
        except Exception:
            self.records = []

    def save_records(self):
        try:
            with open(self._data_file, 'w', encoding='utf-8') as f:
                json.dump(self.records, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def load_categories(self):
        """加載書籍分類"""
        try:
            if os.path.isfile(self._categories_file):
                with open(self._categories_file, 'r', encoding='utf-8') as f:
                    self.categories = json.load(f)
            else:
                self.categories = []
        except Exception:
            self.categories = []
        self._refresh_category_combo()

    def save_categories(self):
        """保存書籍分類"""
        try:
            with open(self._categories_file, 'w', encoding='utf-8') as f:
                json.dump(self.categories, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _update_title_completer(self):
        """更新書名自動完成列表（根據 book_covers 文件夾中的文件）"""
        title_list = []
        
        # 從 book_covers 文件夾讀取所有 .jpg 文件
        covers_dir = os.path.join(os.path.dirname(__file__), 'assets', 'book_covers')
        if os.path.isdir(covers_dir):
            try:
                for filename in os.listdir(covers_dir):
                    if filename.endswith('.jpg') or filename.endswith('.jpeg'):
                        # 移除副檔名，獲得書名
                        title = filename.rsplit('.', 1)[0]
                        if title.strip():
                            title_list.append(title)
            except Exception:
                pass
        
        # 排序：中文先，英文後
        title_list = sorted(set(title_list), key=lambda t: self._sort_key(t))
        # 創建模型並設置給 completer
        model = QtCore.QStringListModel(title_list, self.title_completer)
        self.title_completer.setModel(model)

    def _refresh_category_combo(self):
        """刷新分類下拉選單"""
        current_text = self.category_combo.currentText()
        self.category_combo.blockSignals(True)
        self.category_combo.clear()
        self.category_combo.addItem('（未分類）')
        for cat in sorted(self.categories):
            self.category_combo.addItem(cat)
        # 恢復之前的選擇
        idx = self.category_combo.findText(current_text)
        if idx >= 0:
            self.category_combo.setCurrentIndex(idx)
        else:
            self.category_combo.setCurrentIndex(0)
        self.category_combo.blockSignals(False)

    def _on_add_category(self):
        """新增分類"""
        text, ok = QtWidgets.QInputDialog.getText(self, '新增分類', '請輸入新分類名稱：')
        if ok and text.strip():
            cat = text.strip()
            if cat not in self.categories:
                self.categories.append(cat)
                self.save_categories()
                self._refresh_category_combo()
                # 自動選擇新增的分類
                idx = self.category_combo.findText(cat)
                if idx >= 0:
                    self.category_combo.setCurrentIndex(idx)

    def _is_chinese(self, text):
        """檢查文本是否以中文字符開頭"""
        if not text:
            return False
        first_char = text[0]
        return '\u4e00' <= first_char <= '\u9fff'
    
    def _sort_key(self, title):
        """排序鍵：中文先（0），英文後（1）；然後按字母序排列"""
        is_chinese = self._is_chinese(title)
        return (0 if is_chinese else 1, title.lower())

    def refresh_list(self):
        # 暫停信號以避免在清除列表時觸發 currentItemChanged
        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        self.list_widget.blockSignals(False)
        
        # 按排序規則排序（中文先，然後按字母序）
        sorted_records = sorted(self.records, key=lambda r: self._sort_key(r.get('title', '')))
        
        # 計算總頁數
        total_records = len(sorted_records)
        total_pages = (total_records + self._items_per_page - 1) // self._items_per_page
        if total_pages == 0:
            total_pages = 1
        
        # 確保當前頁碼有效
        if self._current_page >= total_pages:
            self._current_page = total_pages - 1
        if self._current_page < 0:
            self._current_page = 0
        
        # 計算本頁顯示的記錄範圍
        start_idx = self._current_page * self._items_per_page
        end_idx = start_idx + self._items_per_page
        page_records = sorted_records[start_idx:end_idx]
        
        # 顯示本頁的記錄
        for rec in page_records:
            title = (rec.get('title', '') or '').strip()
            # 只顯示書名（若無書名則顯示未命名）
            display = title if title else '（未命名）'
            item = QtWidgets.QListWidgetItem(display)
            item.setData(QtCore.Qt.UserRole, rec.get('id'))
            self.list_widget.addItem(item)
        
        # 更新分頁標籤和按鈕狀態
        self.page_label.setText(f'第 {self._current_page + 1} 頁 / 共 {total_pages} 頁')
        self.prev_btn.setEnabled(self._current_page > 0)
        self.next_btn.setEnabled(self._current_page < total_pages - 1)

    def _find_record_by_id(self, idv):
        for r in self.records:
            if r.get('id') == idv:
                return r
        return None

    def _clear_form(self):
        """清空編輯表單"""
        self.title_edit.clear()
        self.author_edit.clear()
        self.total_spin.setValue(1)
        self.current_spin.setValue(0)
        self.category_combo.setCurrentIndex(0)  # 重置為「未分類」
        self._selected_record_id = None
        # 確保清除列表選擇狀態，避免 currentItemChanged 信號不被觸發
        self.list_widget.blockSignals(True)
        self.list_widget.clearSelection()
        self.list_widget.setCurrentItem(None)
        self.list_widget.blockSignals(False)
        self._update_button_state()

    def _update_button_state(self):
        """根據選擇狀態更新按鈕顯示"""
        if self._selected_record_id is None:
            # 未選中：顯示「新增」，隱藏「更新」和「移除」
            self.add_btn.show()
            self.update_btn.hide()
            self.remove_btn.hide()
        else:
            # 已選中：隱藏「新增」，顯示「更新」和「移除」
            self.add_btn.hide()
            self.update_btn.show()
            self.remove_btn.show()

    def eventFilter(self, obj, event):
        """處理背景點擊事件（整個面板的空白區域）"""
        if event.type() == QtCore.QEvent.MouseButtonPress:
            # 如果點擊在列表上
            if obj == self.list_widget:
                item = self.list_widget.itemAt(event.pos())
                if item is None:
                    # 點擊在列表背景上，清空選擇和表單
                    self._clear_form()
                    return True
                return False
            
            # 定義表單中的互動元素
            form_widgets = [self.title_edit, self.author_edit, self.total_spin, 
                          self.current_spin, self.category_combo, self.add_category_btn,
                          self.add_btn, self.update_btn, self.remove_btn]
            
            # 檢查點擊位置是否在表單控件上
            def is_in_form_area(pos, widget_list):
                """檢查位置是否在任何表單控件的幾何範圍內"""
                for w in widget_list:
                    if w and w.isVisible() and w.geometry().contains(w.mapFromGlobal(widget_list[0].mapToGlobal(pos))):
                        return True
                return False
            
            # 簡化：檢查全局位置
            global_pos = self.mapToGlobal(event.pos())
            is_on_control = False
            for w in form_widgets:
                if w and w.isVisible():
                    local_pos = w.mapFromGlobal(global_pos)
                    if w.rect().contains(local_pos):
                        is_on_control = True
                        break
            
            # 如果點擊不在任何表單控件上，清空表單
            if not is_on_control:
                self._clear_form()
                return True
        
        return super().eventFilter(obj, event)

    def _on_select_item(self, current, previous=None):
        try:
            if current is None:
                self._clear_form()
                return
            idv = current.data(QtCore.Qt.UserRole)
            rec = self._find_record_by_id(idv)
            if not rec:
                self._clear_form()
                return
            self._selected_record_id = idv  # 保存選中的記錄ID
            self.title_edit.setText(rec.get('title', ''))
            self.author_edit.setText(rec.get('author', ''))
            total = int(rec.get('total_pages', 0) or 0)
            cur = int(rec.get('current_page', 0) or 0)
            self.total_spin.setValue(max(1, total))
            self.current_spin.setValue(max(0, cur))
            # 加載分類
            category = rec.get('category', '（未分類）')
            idx = self.category_combo.findText(category)
            if idx >= 0:
                self.category_combo.setCurrentIndex(idx)
            else:
                self.category_combo.setCurrentIndex(0)
            self._update_button_state()  # 更新按鈕狀態為「更新」模式
            # 發出信號要求顯示書架
            self.show_bookshelf_requested.emit()
        except Exception:
            pass

    def _on_add(self):
        title = self.title_edit.text().strip()
        author = self.author_edit.text().strip()
        total = int(self.total_spin.value())
        cur = int(self.current_spin.value())
        category = self.category_combo.currentText()
        if category == '（未分類）':
            category = '（未分類）'
        if not title:
            return
        
        # 檢查是否已存在同書名的紀錄，如果存在則更新而非新增
        existing_rec = None
        for r in self.records:
            if r.get('title') == title:
                existing_rec = r
                break
        
        if existing_rec:
            # 更新現有紀錄
            existing_rec.update({
                'author': author,
                'total_pages': total,
                'current_page': cur,
                'category': category,
            })
        else:
            # 新增紀錄
            rec = {
                'id': str(uuid.uuid4()),
                'title': title,
                'author': author,
                'total_pages': total,
                'current_page': cur,
                'category': category,
            }
            self.records.append(rec)
        
        self.save_records()
        self._current_page = 0  # 新增時重置到第一頁
        self._update_title_completer()  # 更新自動完成列表
        self.refresh_list()
        self._clear_form()  # 新增完成後清空表單
        # 刷新書架封面
        try:
            if self.main_window:
                self.show_bookshelf_requested.emit()
        except Exception:
            pass

    def _on_update(self):
        if self._selected_record_id is None:
            return
        rec = self._find_record_by_id(self._selected_record_id)
        if not rec:
            return
        title = self.title_edit.text().strip()
        author = self.author_edit.text().strip()
        total = int(self.total_spin.value())
        cur = int(self.current_spin.value())
        category = self.category_combo.currentText()
        if category == '（未分類）':
            category = '（未分類）'
        rec.update({
            'title': title,
            'author': author,
            'total_pages': total,
            'current_page': cur,
            'category': category,
        })
        self.save_records()
        self._update_title_completer()  # 更新自動完成列表
        self.refresh_list()
        self._clear_form()  # 更新完成後清空表單
        # 刷新書架封面
        try:
            if self.main_window:
                self.show_bookshelf_requested.emit()
        except Exception:
            pass

    def _on_remove(self):
        if self._selected_record_id is None:
            return
        self.records = [r for r in self.records if r.get('id') != self._selected_record_id]
        self.save_records()
        self._current_page = 0  # 刪除時重置到第一頁
        self._update_title_completer()  # 更新自動完成列表
        self.refresh_list()
        self._clear_form()  # 移除完成後清空表單
        # 刷新書架封面
        try:
            if self.main_window:
                self.show_bookshelf_requested.emit()
        except Exception:
            pass

    def _on_prev_page(self):
        """上一頁"""
        if self._current_page > 0:
            self._current_page -= 1
            self._clear_form()  # 切換頁面時清空表單
            self.refresh_list()

    def _on_next_page(self):
        """下一頁"""
        total_records = len(self.records)
        total_pages = (total_records + self._items_per_page - 1) // self._items_per_page
        if total_pages == 0:
            total_pages = 1
        if self._current_page < total_pages - 1:
            self._current_page += 1
            self._clear_form()  # 切換頁面時清空表單
            self.refresh_list()


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
        self.ui_scale = _screen_scale(compact_mode)
        self.setFixedSize(
            _scaled(340 if compact_mode else 360, self.ui_scale),
            _scaled(340 if compact_mode else 400, self.ui_scale),
        )
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
        scale = _screen_scale()
        self.resize(_scaled(1000, scale), _scaled(600, scale))
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
        self.ui_scale = _screen_scale(compact_mode)
        self.setMinimumSize(
            _scaled(640 if compact_mode else 700, self.ui_scale),
            _scaled(640 if compact_mode else 700, self.ui_scale),
        )
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


class TodoItemCard(QtWidgets.QWidget):
    """任務卡片 widget - 支持點擊循環狀態切換、hover 顯示常規任務信息"""
    def __init__(self, task, status_colors, todo_panel, main_window, parent=None):
        super().__init__(parent)
        self.task = task
        self.status_colors = status_colors
        self.todo_panel = todo_panel
        self.main_window = main_window
        self.status_dot_label = None
        self.activity_timer = None  # 3秒定時器
        
        # 狀態循環順序：completed -> in_progress -> pending -> completed
        self.status_cycle = ['completed', 'in_progress', 'pending']
        
        # 主容器
        main_item_layout = QtWidgets.QHBoxLayout(self)
        main_item_layout.setContentsMargins(12, 12, 12, 12)
        main_item_layout.setSpacing(8)

        status = task.get('status', 'pending')
        status_color = status_colors.get(status, QtGui.QColor(255, 255, 255))

        self.status_dot_label = QtWidgets.QLabel('●')
        self.status_dot_label.setStyleSheet(f'color: rgb({status_color.red()}, {status_color.green()}, {status_color.blue()}); font-size: 36px;')
        self.status_dot_label.setFixedWidth(32)
        self.status_dot_label.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        main_item_layout.addWidget(self.status_dot_label)

        name_label = QtWidgets.QLabel(task.get('name', 'Untitled'))
        name_label.setStyleSheet('color: #e6fbff; font-size: 28px; font-weight: 600;')
        name_label.setFont(QtGui.QFont('Microsoft JhengHei', 28, QtGui.QFont.Bold))
        name_label.setWordWrap(True)
        name_label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        main_item_layout.addWidget(name_label, 1)
        main_item_layout.addStretch(1)

        self.setStyleSheet('''
            QWidget {
                background: rgba(14, 28, 50, 180);
                border: none;
                border-radius: 4px;
            }
            QWidget:hover {
                background: rgba(33, 62, 95, 200);
                border: none;
            }
        ''')
        
        # 為常規任務設置 tooltip 顯示星期信息
        if task.get('type') == 'routine':
            routine_days = task.get('routine_days', [])
            weekday_names = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日']
            routine_text = '、'.join([weekday_names[day] for day in sorted(routine_days) if day < 7])
            self.setToolTip(routine_text)
    
    def mousePressEvent(self, event):
        """點擊任務卡片 - 循環切換狀態"""
        # 獲取當前狀態在循環列表中的位置
        current_status = self.task.get('status', 'pending')
        current_index = self.status_cycle.index(current_status) if current_status in self.status_cycle else 2
        # 循環到下一個狀態
        next_index = (current_index + 1) % len(self.status_cycle)
        next_status = self.status_cycle[next_index]
        
        # 更新任務狀態
        self.task['status'] = next_status
        self.todo_panel._save_tasks()
        
        # 更新卡片顯示
        status_color = self.status_colors.get(next_status, QtGui.QColor(255, 255, 255))
        self.status_dot_label.setStyleSheet(f'color: rgb({status_color.red()}, {status_color.green()}, {status_color.blue()}); font-size: 36px;')
        
        # 取消舊的定時器
        if self.activity_timer:
            self.activity_timer.stop()
        
        # 設置3秒定時器，3秒後重新排列
        self.activity_timer = QtCore.QTimer()
        self.activity_timer.setSingleShot(True)
        self.activity_timer.timeout.connect(self._on_timer_timeout)
        self.activity_timer.start(3000)  # 3000 毫秒 = 3 秒
        
        super().mousePressEvent(event)
    
    def _on_timer_timeout(self):
        """3秒定時器超時 - 重新排列任務"""
        if self.main_window:
            self.todo_panel.refresh_display()


class FinalSageWindow(QtWidgets.QMainWindow):
    toggleRequested = QtCore.pyqtSignal()
    def __init__(self, controller=None, compact_mode=False):
        super().__init__()
        self.compact_mode = compact_mode
        self.ui_scale = _screen_scale(compact_mode)
        self.setWindowTitle('個體名：大賢者')
        self.setMinimumSize(_scaled(560, self.ui_scale), _scaled(560, self.ui_scale))
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

        # 內容堆疊窗口（圓盤 vs 書架）
        self.display_stack = QtWidgets.QStackedWidget()
        
        # 圓盤視圖
        disc_container = QtWidgets.QWidget()
        disc_layout = QtWidgets.QVBoxLayout(disc_container)
        disc_layout.setContentsMargins(0, 0, 0, 0)
        disc_layout.addStretch(1)
        
        self.disc = GreatSageDisc(compact_mode=compact_mode)
        self.disc.setFixedSize(
            _scaled(700 if compact_mode else 760, self.ui_scale),
            _scaled(700 if compact_mode else 760, self.ui_scale),
        )
        disc_layout.addWidget(self.disc, alignment=QtCore.Qt.AlignCenter)
        disc_layout.addStretch(1)
        
        self.display_stack.addWidget(disc_container)
        
        # 書架視圖
        self.bookshelf_panel = BookshelfPanel(compact_mode=compact_mode)
        self.display_stack.addWidget(self.bookshelf_panel)
        
        # 待辦清單視圖
        self.todo_list_display = QtWidgets.QWidget()
        todo_list_layout = QtWidgets.QVBoxLayout(self.todo_list_display)
        todo_list_layout.setContentsMargins(12, 12, 12, 12)
        todo_list_layout.setSpacing(8)
        
        # 待辦清單標題（隱藏）
        todo_title = QtWidgets.QLabel('待辦清單')
        todo_title.setStyleSheet('color: #e6fbff; font-weight: bold; font-size: 18px;')
        todo_title.hide()
        todo_list_layout.addWidget(todo_title)
        
        # 待辦清單內容（可滾動）
        self.todo_list_scroll = QtWidgets.QScrollArea()
        self.todo_list_scroll.setWidgetResizable(True)
        self.todo_list_scroll.setStyleSheet('''
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
        
        self.todo_list_container = QtWidgets.QWidget()
        self.todo_list_layout_inner = QtWidgets.QVBoxLayout(self.todo_list_container)
        self.todo_list_layout_inner.setContentsMargins(0, 0, 0, 0)
        self.todo_list_layout_inner.setSpacing(4)
        
        self.todo_list_scroll.setWidget(self.todo_list_container)
        todo_list_layout.addWidget(self.todo_list_scroll)
        
        self.display_stack.addWidget(self.todo_list_display)
        
        # 默認顯示圓盤（索引 0）
        self.display_stack.setCurrentIndex(0)
        
        overlay_layout.addWidget(self.display_stack, stretch=1)
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
                    event_label.setFont(QtGui.QFont('SimSun-ExtB', 14, QtGui.QFont.Bold))
                    event_label.setStyleSheet('color: #ffffff; letter-spacing: 2px;')
                    self.calendar_items_layout.addWidget(event_label)
            else:
                empty_label = QtWidgets.QLabel('這一天還沒有安排')
                empty_label.setAlignment(QtCore.Qt.AlignCenter)
                empty_label.setFont(QtGui.QFont('SimSun-ExtB', 14, QtGui.QFont.Bold))
                empty_label.setStyleSheet('color: #ffffff; letter-spacing: 2px;')
                self.calendar_items_layout.addWidget(empty_label)
            
            # Add bottom stretch
            self.calendar_items_layout.addStretch(1)
        except Exception:
            pass

    def show_bookshelf(self):
        """顯示書架視圖"""
        self.display_stack.setCurrentIndex(1)  # 顯示書架
        self.bookshelf_panel.load_data()
        self.bookshelf_panel.refresh_bookshelf()

    def show_disc(self):
        """顯示圓盤視圖"""
        self.display_stack.setCurrentIndex(0)  # 顯示圓盤

    def show_todo_list(self, todo_panel):
        """顯示待辦清單視圖"""
        # 清空舊的任務列表
        while self.todo_list_layout_inner.count():
            widget = self.todo_list_layout_inner.takeAt(0).widget()
            if widget:
                widget.deleteLater()
        
        # 獲取篩選後的任務
        filtered_tasks, filtered_date = todo_panel.get_filtered_tasks_for_display()
        
        # 如果有篩選日期，顯示日期標題
        if filtered_date:
            date_display_text = todo_panel.get_filtered_date_display_text()
            date_title = QtWidgets.QLabel(date_display_text if date_display_text else filtered_date)
            date_title.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
            date_title.setStyleSheet('color: #ffcc00; font-size: 32px; font-weight: bold; margin-bottom: 8px;')
            date_title.setFont(QtGui.QFont('Microsoft JhengHei', 32, QtGui.QFont.Bold))
            self.todo_list_layout_inner.addWidget(date_title)
        
        # 獲取任務列表並依類型分區顯示：緊急任務在上、常規任務在下
        status_order = {
            'in_progress': 0,
            'pending': 1,
            'completed': 2,
        }
        all_tasks = filtered_tasks
        urgent_tasks = sorted(
            [task for task in all_tasks if task.get('type') == todo_panel.TYPE_URGENT],
            key=lambda task: (
                status_order.get(task.get('status', 'pending'), 99),
                task.get('name', '').lower(),
            )
        )
        routine_tasks = sorted(
            [task for task in all_tasks if task.get('type') == todo_panel.TYPE_ROUTINE],
            key=lambda task: (
                status_order.get(task.get('status', 'pending'), 99),
                task.get('name', '').lower(),
            )
        )

        if not all_tasks:
            # 無任務時的提示
            if filtered_date:
                empty_label = QtWidgets.QLabel(f'該日期無任務')
            else:
                empty_label = QtWidgets.QLabel('暫無任務\n點擊右側「新增」按鈕建立任務')
            empty_label.setAlignment(QtCore.Qt.AlignCenter)
            empty_label.setStyleSheet('color: #8fb5d4; font-size: 24px; padding: 60px;')
            empty_label.setFont(QtGui.QFont('Microsoft JhengHei', 24))
            self.todo_list_layout_inner.addWidget(empty_label)
        else:
            def add_section(title_text, section_tasks, title_color):
                if not section_tasks:
                    return

                section_label = QtWidgets.QLabel(title_text)
                section_label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
                section_label.setStyleSheet(f'color: {title_color}; font-size: 28px; font-weight: bold; margin-top: 8px; margin-bottom: 4px;')
                section_label.setFont(QtGui.QFont('Microsoft JhengHei', 28, QtGui.QFont.Bold))
                self.todo_list_layout_inner.addWidget(section_label)

                for task in section_tasks:
                    # 使用新的 TodoItemCard 替代普通 QWidget
                    item_widget = TodoItemCard(task, todo_panel.STATUS_COLORS, todo_panel, self)
                    self.todo_list_layout_inner.addWidget(item_widget)

            add_section(todo_panel.TYPE_NAMES[todo_panel.TYPE_URGENT], urgent_tasks, '#ff6464')
            add_section(todo_panel.TYPE_NAMES[todo_panel.TYPE_ROUTINE], routine_tasks, '#64b4ff')
        
        self.todo_list_layout_inner.addStretch()
        self.display_stack.setCurrentIndex(2)  # 顯示待辦清單
    
    def _on_todo_item_clicked(self, task_id, todo_panel):
        """待辦清單項目被點擊"""
        todo_panel.select_task_by_id(task_id)
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
        target_ratio = 0.68 if self.compact_mode else 0.82
        disc_min = _scaled(420 if self.compact_mode else 520, self.ui_scale)
        available = max(1, min(rect.width(), rect.height()) - _scaled(40, self.ui_scale))
        preferred = int(min(rect.width(), rect.height()) * target_ratio)
        disc_size = max(disc_min, min(preferred, available))
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
        self.ui_scale = _screen_scale(compact_mode)
        self.main_window = main_window
        self.setWindowTitle('個體名：大賢者 - 功能選單')
        self.setMinimumSize(_scaled(400, self.ui_scale), _scaled(520, self.ui_scale))  # 盡量保留左右雙窗排版的可用寬度
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
            button.setMinimumHeight(_scaled(90 if compact_mode else 100, self.ui_scale))
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
        self.todo_panel = TodoListPanel(compact_mode=self.compact_mode, main_window=self.main_window)
        self.editor_stack.addWidget(self.todo_panel)
        self.progress_panel = ProgressTrackerPanel(compact_mode=self.compact_mode)
        self.progress_panel.main_window = self.main_window  # 設置左窗口引用
        self.editor_stack.addWidget(self.progress_panel)
        self.calendar_panel = CalendarPanel(compact_mode=self.compact_mode)
        self.editor_stack.addWidget(self.calendar_panel)
        menu_layout.addWidget(self.editor_stack)
        menu_layout.addStretch(1)

        # 連接進度追蹤面板的信號到左窗口的書架顯示
        if self.main_window:
            try:
                self.progress_panel.show_bookshelf_requested.connect(self.main_window.show_bookshelf)
            except Exception:
                pass

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
        self.alarm_button.setMinimumHeight(_scaled(108 if compact_mode else 120, self.ui_scale))
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
            '',
            '',
            '行事曆',
        ]
        self.menu_hint.setText(hints[index])
        
        # 根據選擇的功能切換左窗口的顯示（進度追蹤顯示書架，待辦清單顯示任務，其他顯示圓盤）
        if self.main_window is not None:
            if index == 1:
                # 待辦清單：顯示任務列表
                try:
                    self.main_window.show_todo_list(self.todo_panel)
                except Exception:
                    pass
            elif index == 2:
                # 進度追蹤：顯示書架
                try:
                    self.main_window.show_bookshelf()
                except Exception:
                    pass
            else:
                # 其他功能：顯示圓盤
                try:
                    self.main_window.show_disc()
                except Exception:
                    pass
        
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

