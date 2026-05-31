import os
import random
import sys

from PyQt5 import QtWidgets, QtGui, QtCore
from pet_chat_feature import create_pet_chat_feature, resolve_gemini_api_key


class ClickableBubbleLabel(QtWidgets.QLabel):
    clicked = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.clicked.emit()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            event.accept()
        else:
            super().mouseReleaseEvent(event)


class PetWindow(QtWidgets.QLabel):
    hoverStateChanged = QtCore.pyqtSignal(bool)
    moved = QtCore.pyqtSignal()

    def __init__(self, assets_dir, on_click=None, size=(120, 120), controller=None):
        super().__init__()
        self.assets_dir = assets_dir
        self.on_click = on_click
        self.controller = controller
        self.width_fixed, self.height_fixed = size
        self.timer_text = '點我跟我聊天'

        # load frames from assets_dir (expecting 1.jpg,2.jpg...)
        self.frames = []
        if os.path.isdir(self.assets_dir):
            files = os.listdir(self.assets_dir)
            # filter numeric filenames
            imgs = []
            for fn in files:
                lower = fn.lower()
                if lower.endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    # try to extract leading number
                    name = os.path.splitext(fn)[0]
                    try:
                        idx = int(name)
                    except Exception:
                        idx = None
                    imgs.append((idx if idx is not None else 9999, fn))
            imgs.sort()
            for _, fn in imgs:
                path = os.path.join(self.assets_dir, fn)
                pm = QtGui.QPixmap(path)
                if not pm.isNull():
                    scaled = pm.scaled(self.width_fixed, self.height_fixed, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
                    # ensure exact fixed size canvas
                    canvas = QtGui.QPixmap(self.width_fixed, self.height_fixed)
                    canvas.fill(QtCore.Qt.transparent)
                    painter = QtGui.QPainter(canvas)
                    x = (self.width_fixed - scaled.width()) // 2
                    y = (self.height_fixed - scaled.height()) // 2
                    painter.drawPixmap(x, y, scaled)
                    painter.end()
                    self.frames.append(canvas)

        # fallback placeholder if no frames
        if not self.frames:
            canvas = QtGui.QPixmap(self.width_fixed, self.height_fixed)
            canvas.fill(QtCore.Qt.transparent)
            painter = QtGui.QPainter(canvas)
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            brush = QtGui.QBrush(QtGui.QColor('#8b6d5c'))
            painter.setBrush(brush)
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawEllipse(4, 4, self.width_fixed - 8, self.height_fixed - 8)
            painter.setPen(QtGui.QColor('#fff'))
            painter.setFont(QtGui.QFont('Arial', 10))
            painter.drawText(canvas.rect(), QtCore.Qt.AlignCenter, 'Pet')
            painter.end()
            self.frames = [canvas]

        # prepare mirrored frames for left-facing movement
        self.frames_mirrored = [pm.transformed(QtGui.QTransform().scale(-1, 1)) for pm in self.frames]

        self.setPixmap(self.frames[0])
        self.setFixedSize(self.width_fixed, self.height_fixed)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.Tool)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)

        screen = QtWidgets.QApplication.primaryScreen().availableGeometry()
        x = random.randint(0, max(0, screen.width() - self.width()))
        y = random.randint(0, max(0, screen.height() - self.height()))
        self.move(x, y)
        try:
            self.moved.emit()
        except Exception:
            pass

        # movement
        self.vx = random.choice([-4, -3, 3, 4])
        self.vy = random.choice([-2, -1, 0, 1, 2])

        # timers
        self.move_timer = QtCore.QTimer(self)
        self.move_timer.timeout.connect(self.move_step)
        self.move_timer.start(40)

        self.frame_timer = QtCore.QTimer(self)
        self.frame_timer.timeout.connect(self.next_frame)
        self.frame_timer.start(150)

        self.frame_index = 0
        self.facing_left = False

        # hover bubble that follows the pet
        self.bubble = ClickableBubbleLabel(None)
        self.bubble.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.ToolTip)
        self.bubble.setStyleSheet(
            'QLabel { background: rgba(18, 18, 24, 230); color: #f6fbff; border: 1px solid rgba(170, 230, 255, 160); '
            'border-radius: 12px; padding: 8px 12px; font-size: 14px; font-weight: 700; }'
        )
        self.bubble.setText(self.timer_text)
        self.bubble.adjustSize()
        self.bubble.clicked.connect(self._open_chat_from_bubble)
        self.bubble.hide()
        self.hover_padding = 90
        self._hovered = False
        self._hover_pause_active = False

        self.hover_timer = QtCore.QTimer(self)
        self.hover_timer.timeout.connect(self._sync_hover_bubble)
        self.hover_timer.start(40)

        if self.controller is not None:
            try:
                self.controller.updated.connect(self._on_timer_updated)
            except Exception:
                pass

    def enterEvent(self, event):
        try:
            self.hoverStateChanged.emit(True)
        except Exception:
            pass
        super().enterEvent(event)

    def leaveEvent(self, event):
        try:
            self.hoverStateChanged.emit(False)
        except Exception:
            pass
        super().leaveEvent(event)

    def _on_timer_updated(self, remaining_seconds, progress, running, activity_text):
        if self.bubble.isVisible():
            self._update_bubble()

    def _update_bubble(self):
        self.bubble.setText(self.timer_text if self.timer_text else '點我跟我聊天')
        self.bubble.adjustSize()
        pet_geo = self.frameGeometry()
        screen = QtWidgets.QApplication.screenAt(pet_geo.center()) or QtWidgets.QApplication.primaryScreen()
        if screen is None:
            self.bubble.move(self.mapToGlobal(QtCore.QPoint(self.width() + 14, -8)))
            return

        screen_geo = screen.availableGeometry()
        margin = 10
        gap = 14
        max_width = max(160, screen_geo.width() - margin * 2)
        if self.bubble.width() > max_width:
            self.bubble.setFixedWidth(max_width)
            self.bubble.adjustSize()

        bubble_w = self.bubble.width()
        bubble_h = self.bubble.height()
        right_x = pet_geo.right() + gap
        left_x = pet_geo.left() - bubble_w - gap

        if right_x + bubble_w <= screen_geo.right() - margin:
            bx = right_x
        elif left_x >= screen_geo.left() + margin:
            bx = left_x
        else:
            bx = min(max(screen_geo.left() + margin, right_x), screen_geo.right() - bubble_w - margin)

        by = pet_geo.top() - 8
        by = min(max(screen_geo.top() + margin, by), screen_geo.bottom() - bubble_h - margin)
        self.bubble.move(bx, by)

    def _cursor_near_pet(self):
        cursor_pos = QtGui.QCursor.pos()
        near_rect = self.frameGeometry().adjusted(-self.hover_padding, -self.hover_padding, self.hover_padding, self.hover_padding)
        return near_rect.contains(cursor_pos)

    def _sync_hover_bubble(self):
        if not self.isVisible():
            if self._hover_pause_active:
                self._hover_pause_active = False
                try:
                    if not self.move_timer.isActive():
                        self.move_timer.start(40)
                    if not self.frame_timer.isActive():
                        self.frame_timer.start(150)
                except Exception:
                    pass
            if self._hovered:
                self._hovered = False
                try:
                    self.hoverStateChanged.emit(False)
                except Exception:
                    pass
            self.bubble.hide()
            return
        hovered = self._cursor_near_pet()
        if hovered != self._hovered:
            self._hovered = hovered
            try:
                self.hoverStateChanged.emit(hovered)
            except Exception:
                pass

        if hovered:
            if not self._hover_pause_active:
                self._hover_pause_active = True
                try:
                    self.move_timer.stop()
                    self.frame_timer.stop()
                except Exception:
                    pass
            self._update_bubble()
            self.bubble.show()
            self.bubble.raise_()
        else:
            if self._hover_pause_active:
                self._hover_pause_active = False
                try:
                    if not self.move_timer.isActive():
                        self.move_timer.start(40)
                    if not self.frame_timer.isActive():
                        self.frame_timer.start(150)
                except Exception:
                    pass
            self.bubble.hide()

    def mousePressEvent(self, event):
        # right-click quits the application immediately
        try:
            if event.button() == QtCore.Qt.RightButton:
                QtWidgets.QApplication.quit()
                return
        except Exception:
            pass

        if callable(self.on_click):
            # hide pet when opening GUI
            try:
                self.hide()
            except Exception:
                pass
            self.on_click()

    def next_frame(self):
        self.frame_index = (self.frame_index + 1) % len(self.frames)
        if self.facing_left:
            self.setPixmap(self.frames_mirrored[self.frame_index])
        else:
            self.setPixmap(self.frames[self.frame_index])

    def move_step(self):
        geom = QtWidgets.QApplication.primaryScreen().availableGeometry()
        nx = self.x() + self.vx
        ny = self.y() + self.vy
        bounced = False
        if nx < geom.left() or nx + self.width() > geom.right():
            self.vx = -self.vx
            bounced = True
        if ny < geom.top() or ny + self.height() > geom.bottom():
            self.vy = -self.vy
            bounced = True
        self.move(self.x() + self.vx, self.y() + self.vy)

        # update facing direction
        new_facing_left = self.vx < 0
        if new_facing_left != self.facing_left or bounced:
            self.facing_left = new_facing_left
            # update current pixmap to mirrored/original
            if self.facing_left:
                self.setPixmap(self.frames_mirrored[self.frame_index])
            else:
                self.setPixmap(self.frames[self.frame_index])
        if self.bubble.isVisible():
            self._update_bubble()

    def _open_chat_from_bubble(self):
        try:
            self.bubble.hide()
        except Exception:
            pass
        
        chat_feature = getattr(self, 'chat_feature', None)
        if chat_feature is not None:
            try:
                if hasattr(chat_feature, 'open_chat_dialog'):
                    chat_feature.open_chat_dialog()
            except Exception as e:
                pass
        
        try:
            self.moved.emit()
        except Exception:
            pass


if __name__ == '__main__':
    import gui2
    app = QtWidgets.QApplication(sys.argv)
    compact_mode = len(app.screens()) < 2
    # use assets/walk for walking animation
    assets_dir = os.path.join(os.path.dirname(__file__), 'assets', 'walk')
    # create the shared GUI windows but keep them hidden until the pet is clicked
    controller, main_win, menu_win = gui2.create_sage_windows(compact_mode=compact_mode)

    def _do_open_gui():
        gui2.arrange_sage_windows(app, main_win, menu_win, compact_mode=compact_mode)

    # simple shared state for toggle/Q handling
    state = {'gui_visible': False, 'alarm_active': False}

    def _on_open_gui():
        _do_open_gui()
        state['gui_visible'] = True

    def _toggle_q():
        gui_is_visible = main_win.isVisible() or menu_win.isVisible() or state.get('gui_visible')
        # if alarm is active, Q should stop alarm and return to pet mode
        if state.get('alarm_active'):
            try:
                controller.stop_alarm()
            except Exception:
                pass
            try:
                main_win.hide()
            except Exception:
                pass
            try:
                menu_win.hide()
            except Exception:
                pass
            try:
                w.show()
            except Exception:
                pass
            state['alarm_active'] = False
            state['gui_visible'] = False
            return
        # if GUI visible (but not alarm), hide GUI and show pet again
        if gui_is_visible:
            try:
                main_win.hide()
            except Exception:
                pass
            try:
                menu_win.hide()
            except Exception:
                pass
            try:
                w.show()
            except Exception:
                pass
            state['gui_visible'] = False
            return
        # otherwise, quit application (second Q)
        QtWidgets.QApplication.quit()
    # wrap open_gui so we can track state
    def open_gui():
        _on_open_gui()

    w = PetWindow(assets_dir, on_click=open_gui, size=(120, 120), controller=controller)
    try:
        api_key = resolve_gemini_api_key(prompt_if_missing=False)
        w.chat_feature = create_pet_chat_feature(w, controller, api_key=api_key)
    except Exception:
        w.chat_feature = None
    # ensure pet can receive shortcuts/focus
    try:
        w.setFocusPolicy(QtCore.Qt.StrongFocus)
        w.setFocus()
    except Exception:
        pass
    # make Q work even when pet is visible by adding a shortcut on the pet
    try:
        from PyQt5 import QtGui as _QtGui
        pet_shortcut = QtWidgets.QShortcut(_QtGui.QKeySequence('Q'), w)
        pet_shortcut.activated.connect(_toggle_q)
    except Exception:
        pass
    # connect Q toggle signals from windows to handler
    try:
        if hasattr(main_win, 'toggleRequested'):
            main_win.toggleRequested.connect(_toggle_q)
    except Exception:
        pass
    try:
        if hasattr(menu_win, 'toggleRequested'):
            menu_win.toggleRequested.connect(_toggle_q)
    except Exception:
        pass

    # if alarm starts (time up) while pet is visible, open the GUI and hide the pet
    try:
        def _on_alarm_started():
            state['alarm_active'] = True
            _do_open_gui()
            w.hide()
        controller.alarmStarted.connect(_on_alarm_started)
    except Exception:
        pass
    try:
        controller.alarmStopped.connect(lambda: state.update({'alarm_active': False, 'gui_visible': True}))
    except Exception:
        pass
    w.show()
    sys.exit(app.exec_())
