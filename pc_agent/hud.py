import sys
import json
import psutil
import datetime
import math

from PySide6.QtWidgets import QApplication, QWidget, QLabel
from PySide6.QtCore import Qt, QTimer, QRectF
from PySide6.QtGui import QPainter, QPen, QFont


class JarvisHUD(QWidget):
    def __init__(self):
        super().__init__()

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowTitle("Jarvis HUD")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setWindowState(Qt.WindowState.WindowFullScreen)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        self.info = QLabel(self)
        self.info.setGeometry(45, 35, 430, 245)
        self.info.setStyleSheet(
            "color: rgba(80, 235, 255, 235); background: transparent;"
        )
        self.info.setFont(QFont("Consolas", 13))

        self.center = QLabel(self)
        self.center.setStyleSheet(
            "color: rgba(80, 235, 255, 230); background: transparent;"
        )
        self.center.setFont(QFont("Consolas", 11))
        self.center.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.center.setGeometry(
            self.screen().geometry().center().x() - 170,
            self.screen().geometry().center().y() - 25,
            340,
            55,
        )

        self.angle = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_hud)
        self.timer.timeout.connect(self.update)
        self.timer.start(80)
        self.update_hud()

    def read_status(self):
        try:
            with open("status.json", "r", encoding="utf-8") as file:
                return json.load(file)
        except Exception:
            return {
                "status": "OFFLINE",
                "voice": "UNKNOWN",
                "last_command": "None",
            }

    def update_hud(self):
        status = self.read_status()
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        disk = psutil.disk_usage(os_path()).percent
        current_time = datetime.datetime.now().strftime("%I:%M:%S %p")
        self.angle = (self.angle + 3) % 360

        self.info.setText(
            f"JARVIS // SYSTEM INTERFACE\n"
            f"────────────────────────\n"
            f"VOICE     {status['voice']}\n"
            f"STATUS    {status['status']}\n"
            f"CPU       {cpu:5.1f}%\n"
            f"RAM       {ram:5.1f}%\n"
            f"STORAGE   {disk:5.1f}%\n"
            f"TIME      {current_time}\n"
            f"COMMAND   {status['last_command']}"
        )
        self.center.setText("◉  J A R V I S   O N L I N E  ◉")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        pen = QPen()
        pen.setColor(Qt.GlobalColor.cyan)
        pen.setWidth(2)
        pen.setCosmetic(True)
        painter.setPen(pen)

        w = self.width()
        h = self.height()
        cx = w // 2
        cy = h // 2

        # Mask-style corner brackets
        length = 95
        margin = 35
        corners = [
            (margin, margin, 1, 1),
            (w - margin, margin, -1, 1),
            (margin, h - margin, 1, -1),
            (w - margin, h - margin, -1, -1),
        ]
        for x, y, dx, dy in corners:
            painter.drawLine(x, y, x + dx * length, y)
            painter.drawLine(x, y, x, y + dy * length)

        # Center targeting reticle
        r1 = 62
        r2 = 105
        painter.drawEllipse(QRectF(cx - r1, cy - r1, r1 * 2, r1 * 2))
        painter.drawEllipse(QRectF(cx - r2, cy - r2, r2 * 2, r2 * 2))
        painter.drawLine(cx - 145, cy, cx - 75, cy)
        painter.drawLine(cx + 75, cy, cx + 145, cy)
        painter.drawLine(cx, cy - 145, cx, cy - 75)
        painter.drawLine(cx, cy + 75, cx, cy + 145)

        # Rotating scanner ticks
        for i in range(0, 360, 30):
            a = math.radians(i + self.angle)
            inner = 115
            outer = 128
            x1 = cx + math.cos(a) * inner
            y1 = cy + math.sin(a) * inner
            x2 = cx + math.cos(a) * outer
            y2 = cy + math.sin(a) * outer
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

        # Bottom status line
        painter.setFont(QFont("Consolas", 10))
        painter.drawText(45, h - 45, "JARVIS // VISOR LINK ACTIVE")
        painter.drawText(w - 260, h - 45, "SYSTEM MONITORING")


def os_path():
    import os
    return os.path.abspath(".")


app = QApplication(sys.argv)
hud = JarvisHUD()
hud.show()
sys.exit(app.exec())
