import sys
import os
import json
import psutil
import datetime
import math
import time

from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import Qt, QTimer, QRectF
from PySide6.QtGui import QPainter, QPen, QFont


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATUS_FILE = os.path.join(BASE_DIR, "status.json")


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

        self.angle = 0
        self.scan_y = 0
        self.last_tick = time.time()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(40)

    def read_status(self):
        try:
            with open(STATUS_FILE, "r", encoding="utf-8") as file:
                return json.load(file)
        except Exception:
            return {"status": "OFFLINE", "voice": "UNKNOWN", "last_command": "None"}

    def animate(self):
        self.angle = (self.angle + 2) % 360
        self.scan_y = (self.scan_y + 5) % max(1, self.height())
        self.update()

    def text(self, painter, x, y, value, size=11, bold=False):
        font = QFont("Consolas", size)
        font.setBold(bold)
        painter.setFont(font)
        painter.drawText(x, y, value)

    def bar(self, painter, x, y, width, height, value):
        painter.drawRect(x, y, width, height)
        fill = max(0, min(width - 4, int((width - 4) * value / 100)))
        painter.drawRect(x + 2, y + 2, fill, height - 4)

    def panel(self, painter, x, y, w, h, title):
        painter.drawRect(x, y, w, h)
        self.text(painter, x + 12, y + 20, title, 10, True)
        painter.drawLine(x + 10, y + 28, x + w - 10, y + 28)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        cx = w // 2
        cy = h // 2

        pen = QPen()
        pen.setColor(Qt.GlobalColor.cyan)
        pen.setWidth(2)
        pen.setCosmetic(True)
        painter.setPen(pen)

        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        disk = psutil.disk_usage(os.path.abspath(os.sep)).percent
        net = psutil.net_io_counters()
        status = self.read_status()
        now = datetime.datetime.now()
        uptime = int(time.time() - psutil.boot_time())
        up_h = uptime // 3600
        up_m = (uptime % 3600) // 60

        # Outer visor framing
        margin = 28
        corner = 135
        for x, y, dx, dy in [
            (margin, margin, 1, 1),
            (w - margin, margin, -1, 1),
            (margin, h - margin, 1, -1),
            (w - margin, h - margin, -1, -1),
        ]:
            painter.drawLine(x, y, x + dx * corner, y)
            painter.drawLine(x, y, x, y + dy * corner)
            painter.drawLine(x + dx * 18, y, x + dx * 18, y + dy * 42)

        # Top center title
        self.text(painter, cx - 125, 42, "J A R V I S  //  VISOR", 14, True)
        self.text(painter, cx - 92, 62, "NEURAL INTERFACE ONLINE", 9)

        # Left system panel
        self.panel(painter, 45, 90, 300, 220, "SYSTEM TELEMETRY")
        self.text(painter, 60, 55 + 80, f"CPU     {cpu:5.1f}%", 11)
        self.bar(painter, 155, 128, 160, 13, cpu)
        self.text(painter, 60, 170, f"MEMORY  {ram:5.1f}%", 11)
        self.bar(painter, 155, 158, 160, 13, ram)
        self.text(painter, 60, 200, f"DISK    {disk:5.1f}%", 11)
        self.bar(painter, 155, 188, 160, 13, disk)
        self.text(painter, 60, 235, f"UPTIME  {up_h:02d}h {up_m:02d}m", 11)
        self.text(painter, 60, 265, f"TIME    {now.strftime('%I:%M:%S %p')}", 11)
        self.text(painter, 60, 292, f"DATE    {now.strftime('%m/%d/%Y')}", 11)

        # Right network / voice panel
        self.panel(painter, w - 345, 90, 300, 220, "LINK STATUS")
        self.text(painter, w - 330, 128, f"VOICE   {status.get('voice', 'UNKNOWN')}", 11)
        self.text(painter, w - 330, 158, f"STATE   {status.get('status', 'UNKNOWN')}", 11)
        self.text(painter, w - 330, 188, "NETWORK  ONLINE", 11)
        self.text(painter, w - 330, 218, f"RX      {net.bytes_recv / 1024 / 1024:,.1f} MB", 10)
        self.text(painter, w - 330, 246, f"TX      {net.bytes_sent / 1024 / 1024:,.1f} MB", 10)
        self.text(painter, w - 330, 278, "MIC      LISTENING READY", 10)

        # Center targeting array
        r1, r2, r3 = 62, 105, 155
        painter.drawEllipse(QRectF(cx - r1, cy - r1, r1 * 2, r1 * 2))
        painter.drawEllipse(QRectF(cx - r2, cy - r2, r2 * 2, r2 * 2))
        painter.drawEllipse(QRectF(cx - r3, cy - r3, r3 * 2, r3 * 2))
        painter.drawLine(cx - 250, cy, cx - 175, cy)
        painter.drawLine(cx + 175, cy, cx + 250, cy)
        painter.drawLine(cx, cy - 250, cx, cy - 175)
        painter.drawLine(cx, cy + 175, cx, cy + 250)

        # Rotating scanner marks
        for i in range(0, 360, 15):
            a = math.radians(i + self.angle)
            inner = 165 if i % 30 else 155
            outer = 178 if i % 30 else 190
            x1 = cx + math.cos(a) * inner
            y1 = cy + math.sin(a) * inner
            x2 = cx + math.cos(a) * outer
            y2 = cy + math.sin(a) * outer
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

        # Horizontal scan line
        painter.drawLine(40, self.scan_y, w - 40, self.scan_y)

        # Center labels
        self.text(painter, cx - 100, cy - 185, "TARGETING ARRAY", 9, True)
        self.text(painter, cx - 55, cy + 185, "VISOR LOCK", 9, True)
        self.text(painter, cx - 44, cy + 202, "ACTIVE", 9)

        # Bottom left command panel
        self.panel(painter, 45, h - 205, 450, 145, "LAST COMMAND")
        command = str(status.get("last_command", "None"))[:48]
        self.text(painter, 62, h - 145, command, 12, True)
        self.text(painter, 62, h - 112, "VOICE CHANNEL: ACTIVE", 9)
        self.text(painter, 62, h - 88, "WAKE WORD: JARVIS", 9)

        # Bottom right diagnostics
        self.panel(painter, w - 495, h - 205, 450, 145, "DIAGNOSTICS")
        self.text(painter, w - 478, h - 145, "CORE LINK        STABLE", 9)
        self.text(painter, w - 478, h - 118, "HUD ENGINE        ONLINE", 9)
        self.text(painter, w - 478, h - 91, "VOICE ENGINE      READY", 9)
        self.text(painter, w - 478, h - 64, "ALL SYSTEMS       NOMINAL", 9, True)

        # Small visor data ticks around the edges
        for x in range(80, w - 80, 80):
            painter.drawLine(x, 75, x + 35, 75)
            painter.drawLine(x, h - 70, x + 35, h - 70)

        self.text(painter, 45, h - 35, "JARVIS // VISOR LINK ACTIVE", 9, True)
        self.text(painter, w - 210, h - 35, "SYSTEM MONITORING", 9)


app = QApplication(sys.argv)
hud = JarvisHUD()
hud.show()
sys.exit(app.exec())
