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
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setWindowState(Qt.WindowState.WindowFullScreen)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        self.angle = 0.0
        self.scan_y = 0.0
        self.boot_start = time.time()
        self.boot_duration = 3.2
        self.pulse = 0.0
        self.transition = 0.0
        self.last_state = "BOOT"
        self.cpu_history = [0.0] * 60
        self.ram_history = [0.0] * 60

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(35)

    def read_status(self):
        try:
            with open(STATUS_FILE, "r", encoding="utf-8") as file:
                return json.load(file)
        except Exception:
            return {"status": "OFFLINE", "voice": "UNKNOWN", "last_command": "None", "mic_level": 0}

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

    def panel(self, painter, x, y, w, h, title):
        painter.save()
        painter.setPen(QPen(Qt.GlobalColor.cyan, 1))
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
        eased = progress * progress * (3 - 2 * progress)
        max_r = int(70 + eased * 300)
        for i in range(5):
            r = max(18, max_r - i * 58)
            painter.drawEllipse(QRectF(cx - r, cy - r, r * 2, r * 2))
        line_len = int(120 + eased * 720)
        painter.drawLine(cx - line_len, cy, cx + line_len, cy)
        painter.drawLine(cx, cy - line_len, cx, cy + line_len)
        self.text(painter, cx - 155, cy - 35, "J A R V I S", 25, True)
        self.text(painter, cx - 135, cy - 8, "VISOR INITIALIZING", 11)
        blocks = int(eased * 22)
        self.text(painter, cx - 145, cy + 42, "SYSTEM LINK [" + "█" * blocks + "·" * (22 - blocks) + "]", 10)
        self.text(painter, cx - 126, cy + 72, "NEURAL CORE  ::  LOADED", 9)
        self.text(painter, cx - 110, cy + 94, "TELEMETRY    ::  SYNCED", 9)
        if progress >= 0.9:
            self.text(painter, cx - 40, cy + 125, "ONLINE", 15, True)
        painter.restore()

    def draw_state_banner(self, painter, w, status):
        state = str(status.get("status", "STANDBY")).upper()
        voice = str(status.get("voice", "READY")).upper()
        labels = {
            "LISTENING": "LISTENING",
            "SPEAKING": "SPEAKING",
            "THINKING": "THINKING",
            "PROCESSING": "THINKING",
            "WAKE WORD DETECTED": "WAKE SIGNAL",
            "COMMAND RECEIVED": "COMMAND RECEIVED",
            "STANDBY": "STANDBY",
            "OFFLINE": "OFFLINE",
        }
        label = labels.get(state, state)
        painter.setPen(QPen(Qt.GlobalColor.cyan, 2))
        painter.drawRect(w // 2 - 145, 82, 290, 34)
        self.text(painter, w // 2 - 128, 104, f"● {label}  //  {voice}", 10, True)

        if state == "LISTENING":
            level = float(status.get("mic_level", 0))
            for i in range(12):
                wave = (0.25 + level / 100.0) * (0.35 + 0.65 * (0.5 + 0.5 * math.sin(self.pulse * 2 + i * 0.8)))
                bar_h = max(4, int(32 * wave))
                x = w // 2 - 130 + i * 22
                painter.drawRect(x, 124 - bar_h // 2, 10, bar_h)
        elif state in ("SPEAKING", "THINKING", "PROCESSING"):
            for i in range(10):
                r = 2 + int(3 * (0.5 + 0.5 * math.sin(self.pulse * 3 + i)))
                x = w // 2 + 160 + i * 8
                painter.drawEllipse(QRectF(x, 98 - r / 2, r, r))

    def graph(self, painter, x, y, w, h, values, title):
        painter.save()
        painter.setPen(QPen(Qt.GlobalColor.cyan, 1))
        painter.drawRect(x, y, w, h)
        self.text(painter, x + 8, y + 17, title, 8, True)
        painter.setPen(QPen(Qt.GlobalColor.cyan, 1))
        points = []
        for i, value in enumerate(values):
            px = x + 5 + (i / max(1, len(values) - 1)) * (w - 10)
            py = y + h - 6 - (max(0, min(100, value)) / 100) * (h - 28)
            points.append((px, py))
        for a, b in zip(points, points[1:]):
            painter.drawLine(int(a[0]), int(a[1]), int(b[0]), int(b[1]))
        painter.restore()

    def draw_speaking_core(self, painter, cx, cy, state):
        if state not in ("SPEAKING", "THINKING", "PROCESSING", "LISTENING"):
            return
        intensity = 0.5 + 0.5 * math.sin(self.pulse * (4 if state == "SPEAKING" else 2))
        if state == "LISTENING":
            intensity = max(intensity, float(self.read_status().get("mic_level", 0)) / 100.0)
        for i in range(8):
            a = math.radians(i * 45 + self.angle * 2)
            inner = 185 + intensity * 10
            outer = inner + 18 + intensity * 28
            painter.drawLine(int(cx + math.cos(a) * inner), int(cy + math.sin(a) * inner), int(cx + math.cos(a) * outer), int(cy + math.sin(a) * outer))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2
        status = self.read_status()
        state = str(status.get("status", "STANDBY")).upper()

        elapsed = time.time() - self.boot_start
        if elapsed < self.boot_duration:
            self.draw_boot(painter, w, h, min(1.0, elapsed / self.boot_duration))
            return

        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        disk = psutil.disk_usage(os.path.abspath(os.sep)).percent
        net = psutil.net_io_counters()
        now = datetime.datetime.now()
        uptime = max(0, int(time.time() - psutil.boot_time()))
        up_h = uptime // 3600
        up_m = (uptime % 3600) // 60
        self.cpu_history.append(cpu)
        self.cpu_history = self.cpu_history[-60:]
        self.ram_history.append(ram)
        self.ram_history = self.ram_history[-60:]

        painter.setPen(QPen(Qt.GlobalColor.cyan, 2))
        margin, corner = 24, 145
        for x, y, dx, dy in [(margin, margin, 1, 1), (w - margin, margin, -1, 1), (margin, h - margin, 1, -1), (w - margin, h - margin, -1, -1)]:
            painter.drawLine(x, y, x + dx * corner, y)
            painter.drawLine(x, y, x, y + dy * corner)
            painter.drawLine(x + dx * 20, y, x + dx * 20, y + dy * 52)

        self.text(painter, cx - 125, 42, "J A R V I S  //  VISOR", 14, True)
        self.text(painter, cx - 96, 61, "NEURAL INTERFACE ONLINE", 9)
        self.draw_state_banner(painter, w, status)

        self.panel(painter, 45, 90, 315, 285, "SYSTEM TELEMETRY")
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
        self.text(painter, 60, 345, f"NET RX     {net.bytes_recv / 1024 / 1024:,.1f} MB", 9)
        self.text(painter, 60, 365, f"NET TX     {net.bytes_sent / 1024 / 1024:,.1f} MB", 9)

        self.panel(painter, w - 360, 90, 315, 285, "LINK STATUS")
        self.text(painter, w - 345, 122, f"VOICE     {status.get('voice', 'UNKNOWN')}", 11)
        self.text(painter, w - 345, 153, f"STATE     {status.get('status', 'UNKNOWN')}", 11)
        self.text(painter, w - 345, 184, "NETWORK   ONLINE", 11)
        self.text(painter, w - 345, 215, f"RX        {net.bytes_recv / 1024 / 1024:,.1f} MB", 10)
        self.text(painter, w - 345, 244, f"TX        {net.bytes_sent / 1024 / 1024:,.1f} MB", 10)
        self.text(painter, w - 345, 275, "MIC       READY", 10)
        self.text(painter, w - 345, 306, "NEURAL TTS ACTIVE", 9, True)
        self.text(painter, w - 345, 336, f"MIC LEVEL {float(status.get('mic_level', 0)):5.1f}%", 9)
        self.bar(painter, w - 190, 328, 140, 12, float(status.get('mic_level', 0)))

        # Central visor targeting and state-reactive core.
        r1, r2, r3 = 62, 106, 158
        painter.drawEllipse(QRectF(cx - r1, cy - r1, r1 * 2, r1 * 2))
        painter.drawEllipse(QRectF(cx - r2, cy - r2, r2 * 2, r2 * 2))
        painter.drawEllipse(QRectF(cx - r3, cy - r3, r3 * 2, r3 * 2))
        painter.drawLine(cx - 270, cy, cx - 180, cy)
        painter.drawLine(cx + 180, cy, cx + 270, cy)
        painter.drawLine(cx, cy - 270, cx, cy - 180)
        painter.drawLine(cx, cy + 180, cx, cy + 270)
        for i in range(0, 360, 10):
            a = math.radians(i + self.angle)
            inner = 168 if i % 30 else 155
            outer = 180 if i % 30 else 195
            painter.drawLine(int(cx + math.cos(a) * inner), int(cy + math.sin(a) * inner), int(cx + math.cos(a) * outer), int(cy + math.sin(a) * outer))
        sweep = math.radians(self.angle * 1.7)
        painter.drawLine(cx, cy, int(cx + math.cos(sweep) * 230), int(cy + math.sin(sweep) * 230))
        self.draw_speaking_core(painter, cx, cy, state)

        # Live CPU/RAM graphs.
        self.graph(painter, cx - 340, h - 205, 315, 115, self.cpu_history, "CPU HISTORY")
        self.graph(painter, cx + 25, h - 205, 315, 115, self.ram_history, "MEMORY HISTORY")

        # Last command and diagnostics.
        self.panel(painter, 45, h - 210, 470, 150, "LAST COMMAND")
        command = str(status.get("last_command", "None"))[:52]
        self.text(painter, 62, h - 150, command, 12, True)
        self.text(painter, 62, h - 117, "VOICE CHANNEL: ACTIVE", 9)
        self.text(painter, 62, h - 91, "WAKE WORD: JARVIS", 9)
        self.text(painter, 62, h - 65, "COMMAND BUFFER: READY", 9)

        self.panel(painter, w - 515, h - 210, 470, 150, "DIAGNOSTICS")
        self.text(painter, w - 498, h - 150, "CORE LINK         STABLE", 9)
        self.text(painter, w - 498, h - 123, "HUD ENGINE        ONLINE", 9)
        self.text(painter, w - 498, h - 96, "VOICE ENGINE      READY", 9)
        self.text(painter, w - 498, h - 69, "ALL SYSTEMS       NOMINAL", 9, True)

        for x in range(80, w - 80, 70):
            painter.drawLine(x, 72, x + 28, 72)
            painter.drawLine(x, h - 72, x + 28, h - 72)
        painter.drawLine(370, self.scan_y, w - 370, self.scan_y)
        self.text(painter, 45, h - 34, "JARVIS // VISOR LINK ACTIVE", 9, True)
        self.text(painter, w - 210, h - 34, "SYSTEM MONITORING", 9)


app = QApplication(sys.argv)
hud = JarvisHUD()
hud.show()
sys.exit(app.exec())
