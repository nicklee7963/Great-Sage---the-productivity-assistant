from PyQt5 import QtWidgets, QtCore, QtGui
import random
import math

# --- 進化版背景：能量流與魔素粒子 ---
class MagicBackground(QtWidgets.QWidget):
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
        
        # 背景漸層 (模擬圖中的紅/紫/黑交錯感)
        grad = QtGui.QLinearGradient(0, 0, self.width(), self.height())
        grad.setColorAt(0, QtGui.QColor(20, 5, 5))
        grad.setColorAt(0.5, QtGui.QColor(10, 10, 20))
        grad.setColorAt(1, QtGui.QColor(5, 15, 10))
        painter.fillRect(self.rect(), grad)

        # 繪製能量連線
        painter.setOpacity(0.3)
        for i in range(15):
            pen = QtGui.QPen(QtGui.QColor(255, 200, 50), random.random() * 1.5)
            painter.setPen(pen)
            painter.drawLine(0, random.randint(0, 600), 1000, random.randint(0, 600))

# --- 大賢者菱形說話視窗 ---
class SageSpeakingDiamond(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(400, 400)
        self.display_text = ""
        self.full_text = "解析完成。獲得獨特技能「專注者」成功。"
        self.char_index = 0
        
        # 打字機效果定時器
        self.type_timer = QtCore.QTimer(self)
        self.type_timer.timeout.connect(self._type_text)
        self.type_timer.start(100)

    def _type_text(self):
        if self.char_index < len(self.full_text):
            self.display_text += self.full_text[self.char_index]
            self.char_index += 1
            self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        # 1. 定義菱形頂點
        w, h = self.width(), self.height()
        center = QtCore.QPoint(w // 2, h // 2)
        points = [
            QtCore.QPoint(w // 2, 20),      # 上
            QtCore.QPoint(w - 20, h // 2),  # 右
            QtCore.QPoint(w // 2, h - 20),  # 下
            QtCore.QPoint(20, h // 2)       # 左
        ]
        polygon = QtGui.QPolygon(points)

        # 2. 繪製發光邊框
        path = QtGui.QPainterPath()
        path.addPolygon(QtGui.QPolygonF(polygon))
        painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255, 200), 4))
        painter.setBrush(QtGui.QColor(0, 0, 0, 220)) # 黑色中心
        painter.drawPath(path)

        # 3. 繪製文字 "ユニークスキル" (直書)
        painter.setPen(QtGui.QColor(255, 255, 255))
        painter.setFont(QtGui.QFont('Microsoft JhengHei', 8))
        painter.drawText(QtCore.QRect(w//2 + 50, h//2 - 100, 20, 100), QtCore.Qt.AlignTop, "ユ\nニ\nー\nク\nス\nキ\nル")

        # 4. 繪製大標題 "大賢者" (直書)
        font_main = QtGui.QFont('SimSun-ExtB', 48, QtGui.QFont.Bold)
        painter.setFont(font_main)
        painter.drawText(QtCore.QRect(0, 0, w, h), QtCore.Qt.AlignCenter, "大\n賢\n者")

        # 5. 繪製側邊文字 "成" "功"
        font_side = QtGui.QFont('SimSun-ExtB', 24, QtGui.QFont.Bold)
        painter.setFont(font_side)
        painter.drawText(w // 2 - 120, h // 2 + 10, "成")
        painter.drawText(w // 2 + 80, h // 2 + 10, "功")

        # 6. 底部說話內容 (打字機效果)
        painter.setFont(QtGui.QFont('Microsoft JhengHei', 12))
        painter.drawText(QtCore.QRect(0, h - 60, w, 40), QtCore.Qt.AlignCenter, self.display_text)

class SageSpeakingGUI(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('個體名：大賢者 - 語音告解中')
        self.resize(1000, 600)

        # 疊層顯示
        layout = QtWidgets.QGridLayout(self.centralWidget())
        self.bg = MagicBackground()
        self.diamond = SageSpeakingDiamond()
        
        layout.addWidget(self.bg, 0, 0)
        layout.addWidget(self.diamond, 0, 0, QtCore.Qt.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)

if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    window = SageSpeakingGUI()
    window.show()
    app.exec_()