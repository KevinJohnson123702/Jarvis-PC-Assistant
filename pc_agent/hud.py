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
        self.boot_start = time.time()
        self.boot_duration = 2.8
        self.pulse = 0.0

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(35)

    def read_status(self):
        try:
            with open(STATUS_FILE, "r", encoding="utf-8") as file:
                return json.load(file)
        except Exception:
            return {"status": "OFFLINE", "voice": "UNKNOWN", "last_command": "None"}

    def animate(self):
        self.angle = (self.angle + 2.5) % 360
        self.scan_y = (self.scan_y + 7) % max(1, self.height())
        self.pulse = (self.pulse + 0.08) % (math.pi * 2)
        self.update()

    def text(self, painter, x, y, value, size=11, bold=False):
        font = QFont("Consolas", size)
        font.setBold(bold)
        painter.setFont(font)
        painter.drawText(int(x), int(y), str(value))

    def panel(self, painter, x, y, w, h, title, alpha=175):
        painter.save()
        pen = QPen(Qt.GlobalColor.cyan)
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawRect(x, y, w, h)
        self.text(painter, x + 12, y + 20, title, 10, True)
        painter.drawLine(x + 10, y + 28, x + w - 10, y + 28)
        painter.restore()

    def bar(self, painter, x, y, width, height, value):
        painter.drawRect(x, y, width, height)
        fill = max(0, min(width - 4, int((width - 4) * value / 100)))
        if fill > 0:
            painter.drawRect(x + 2, y + 2, fill, height - 4)

    def draw_boot(self, painter, w, h, progress):
        cx, cy = w // 2, h // 2
        painter.save()
        painter.setPen(QPen(Qt.GlobalColor.cyan, 2))

        # Expanding boot rings
        max_r = int(80 + progress * 260)
        for i in range(4):
            r = max(20, max_r - i * 55)
            painter.drawEllipse(QRectF(cx - r, cy - r, r * 2, r * 2))

        # Horizontal / vertical lock lines
        line_len = int(150 + progress * 500)
        painter.drawLine(cx - line_len, cy, cx + line_len, cy)
        painter.drawLine(cx, cy - line_len, cx, cy + line_len)

        self.text(painter, cx - 155, cy - 35, "J A R V I S", 25, True)
        self.text(painter, cx - 135, cy - 8, "VISOR INITIALIZING", 11)

        blocks = int(progress * 18)
        self.text(painter, cx - 135, cy + 42, "SYSTEM LINK [" + "█" * blocks + "·" * (18 - blocks) + "]", 10)

        if progress >= 0.92:
            self.text(painter, cx - 75, cy + 78, "ONLINE", 15, True)
        painter.restore()

    def draw_state_banner(self, painter, w, h, status):
        state = str(status.get("status", "STANDBY")).upper()
        voice = str(status.get("voice", "READY")).upper()
        labels = {
            "LISTENING": "LISTENING",
            "SPEAKING": "SPEAKING",
            "WAKE WORD DETECTED": "WAKE SIGNAL",
            "COMMAND RECEIVED": "COMMAND RECEIVED",
            "STANDBY": "STANDBY",
            "OFFLINE": "OFFLINE",
        }
        label = labels.get(state, state)
        pulse = int(90 + 80 * (0.5 + 0.5 * math.sin(self.pulse)))
        pen = QPen(Qt.GlobalColor.cyan)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawRect(w // 2 - 125, 82, 250, 34)
        self.text(painter, w // 2 - 108, 104, f"● {label}  //  {voice}", 10, True)
        # small animated signal marks
        for i in range(5):
            bar_h = 5 + int((i + 1) * (3 + 4 * (0.5 + 0.5 * math.sin(self.pulse + i))))
            painter.drawRect(w // 2 + 140 + i * 9, 99 - bar_h // 2, 5, bar_h)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2
        status = self.read_status()

        # Boot animation is shown for the first few seconds after the HUD launches.
        elapsed = time.time() - self.boot_start
        if elapsed < self.boot_duration:
            progress = min(1.0, elapsed / self.boot_duration)
            self.draw_boot(painter, w, h, progress)
            return

        pen = QPen(Qt.GlobalColor.cyan)
        pen.setWidth(2)
        pen.setCosmetic(True)
        painter.setPen(pen)

        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        disk = psutil.disk_usage(os.path.abspath(os.sep)).percent
        net = psutil.net_io_counters()
        now = datetime.datetime.now()
        uptime = max(0, int(time.time() - psutil.boot_time()))
        up_h = uptime // 3600
        up_m = (uptime % 3600) // 60

        # Full visor frame
        margin = 24
        corner = 145
        for x, y, dx, dy in [
            (margin, margin, 1, 1),
            (w - margin, margin, -1, 1),
            (margin, h - margin, 1, -1),
            (w - margin, h - margin, -1, -1),
        ]:
            painter.drawLine(x, y, x + dx * corner, y)
            painter.drawLine(x, y, x, y + dy * corner)
            painter.drawLine(x + dx * 20, y, x + dx * 20, y + dy * 52)

        self.text(painter, cx - 125, 42, "J A R V I S  //  VISOR", 14, True)
        self.text(painter, cx - 96, 61, "NEURAL INTERFACE ONLINE", 9)
        self.draw_state_banner(painter, w, h, status)

        # Left telemetry
        self.panel(painter, 45, 90, 315, 245, "SYSTEM TELEMETRY")
        self.text(painter, 60, 122, f"CPU       {cpu:5.1f}%", 11)
        self.bar(painter, 170, 113, 170, 13, cpu)
        self.text(painter, 60, 157, f"MEMORY    {ram:5.1f}%", 11)
        self.bar(painter, 170, 148, 170, 13, ram)
        self.text(painter, 60, 192, f"STORAGE   {disk:5.1f}%", 11)
        self.bar(painter, 170, 183, 170, 13, disk)
        self.text(painter, 60, 228, f"UPTIME    {up_h:02d}h {up_m:02d}m", 11)
        self.text(painter, 60, 259, f"TIME      {now.strftime('%I:%M:%S %p')}", 11)
        self.text(painter, 60, 290, f"DATE      {now.strftime('%m/%d/%Y')}", 11)
        self.text(painter, 60, 320, "PROCESSOR LINK    STABLE", 9)

        # Right link panel
        self.panel(painter, w - 360, 90, 315, 245, "LINK STATUS")
        self.text(painter, w - 345, 122, f"VOICE     {status.get('voice', 'UNKNOWN')}", 11)
        self.text(painter, w - 345, 153, f"STATE     {status.get('status', 'UNKNOWN')}", 11)
        self.text(painter, w - 345, 184, "NETWORK   ONLINE", 11)
        self.text(painter, w - 345, 215, f"RX        {net.bytes_recv / 1024 / 1024:,.1f} MB", 10)
        self.text(painter, w - 345, 244, f"TX        {net.bytes_sent / 1024 / 1024:,.1f} MB", 10)
        self.text(painter, w - 345, 275, "MIC       READY", 10)
        self.text(painter, w - 345, 306, "NEURAL TTS ACTIVE", 9, True)

        # Central targeting array
        r1, r2, r3 = 62, 106, 158
        painter.drawEllipse(QRectF(cx - r1, cy - r1, r1 * 2, r1 * 2))
        painter.drawEllipse(QRectF(cx - r2, cy - r2, r2 * 2, r2 * 2))
        painter.drawEllipse(QRectF(cx - r3, cy - r3, r3 * 2, r3 * 2))
        painter.drawLine(cx - 270, cy, cx - 180, cy)
        painter.drawLine(cx + 180, cy, cx + 270, cy)
        painter.drawLine(cx, cy - 270, cx, cy - 180)
        painter.drawLine(cx, cy + 180, cx, cy + 270)

        # Animated scanner marks
        for i in range(0, 360, 10):
            a = math.radians(i + self.angle)
            inner = 168 if i % 30 else 155
            outer = 180 if i % 30 else 195
            x1 = cx + math.cos(a) * inner
            y1 = cy + math.sin(a) * inner
            x2 = cx + math.cos(a) * outer
            y2 = cy + math.sin(a) * outer
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

        # Animated crosshair sweep
        sweep = math.radians(self.angle * 1.7)
        painter.drawLine(
            cx,
            cy,
            int(cx + math.cos(sweep) * 230),
            int(cy + math.sin(sweep) * 230),
        )

        # Scan line with gaps behind panels
        painter.drawLine(370, self.scan_y, w - 370, self.scan_y)

        self.text(painter, cx - 105, cy - 188, "TARGETING ARRAY", 9, True)
        self.text(painter, cx - 48, cy + 188, "VISOR LOCK", 9, True)
        self.text(painter, cx - 30, cy + 205, "ACTIVE", 9)

        # Bottom command panel
        self.panel(painter, 45, h - 210, 470, 150, "LAST COMMAND")
        command = str(status.get("last_command", "None"))[:52]
        self.text(painter, 62, h - 150, command, 12, True)
        self.text(painter, 62, h - 117, "VOICE CHANNEL: ACTIVE", 9)
        self.text(painter, 62, h - 91, "WAKE WORD: JARVIS", 9)
        self.text(painter, 62, h - 65, "COMMAND BUFFER: READY", 9)

        # Bottom diagnostics
        self.panel(painter, w - 515, h - 210, 470, 150, "DIAGNOSTICS")
        self.text(painter, w - 498, h - 150, "CORE LINK         STABLE", 9)
        self.text(painter, w - 498, h - 123, "HUD ENGINE        ONLINE", 9)
        self.text(painter, w - 498, h - 96, "VOICE ENGINE      READY", 9)
        self.text(painter, w - 498, h - 69, "ALL SYSTEMS       NOMINAL", 9, True)

        # Edge data ticks
        for x in range(80, w - 80, 70):
            painter.drawLine(x, 72, x + 28, 72)
            painter.drawLine(x, h - 72, x + 28, h - 72)

        self.text(painter, 45, h - 34, "JARVIS // VISOR LINK ACTIVE", 9, True)
        self.text(painter, w - 210, h - 34, "SYSTEM MONITORING", 9)


app = QApplication(sys.argv)
hud = JarvisHUD()
hud.show()
sys.exit(app.exec())
