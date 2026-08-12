import sys
import os
import json
import psutil
import datetime
import math
import time

from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import Qt, QTimer, QRectF, QPointF
from PySide6.QtGui import QPainter, QPen, QFont, QColor, QBrush, QPolygonF


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATUS_FILE = os.path.join(BASE_DIR, "status.json")


class JarvisHUD(QWidget):
    """Original Jarvis visor HUD with animated telemetry and state effects."""

    CYAN = QColor(35, 220, 255)
    CYAN_SOFT = QColor(35, 220, 255, 90)
    CYAN_FAINT = QColor(35, 220, 255, 35)
    WHITE = QColor(210, 250, 255)
    RED = QColor(255, 70, 90)

    def __init__(self):
        super().__init__()

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setWindowTitle("Jarvis HUD")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setWindowState(Qt.WindowState.WindowFullScreen)

        self.angle = 0.0
        self.scan_angle = 0.0
        self.pulse = 0.0
        self.state_blend = 1.0
        self.last_state = "BOOT"

        self.boot_start = time.time()
        self.boot_duration = 3.0

        self.cpu_history = [0.0] * 80
        self.ram_history = [0.0] * 80

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(35)

    def read_status(self):
        try:
            with open(STATUS_FILE, "r", encoding="utf-8") as file:
                return json.load(file)
        except Exception:
            return {
                "status": "OFFLINE",
                "voice": "UNKNOWN",
                "last_command": "None",
                "mic_level": 0,
            }

    def animate(self):
        self.angle = (self.angle + 1.8) % 360
        self.scan_angle = (self.scan_angle + 3.2) % 360
        self.pulse = (self.pulse + 0.105) % (math.pi * 2)

        state = str(self.read_status().get("status", "STANDBY")).upper()
        if state != self.last_state:
            self.last_state = state
            self.state_blend = 0.0
        else:
            self.state_blend = min(1.0, self.state_blend + 0.075)

        self.update()

    def pen(self, color=None, width=1):
        return QPen(color or self.CYAN, width)

    def text(self, painter, x, y, value, size=10, bold=False, color=None):
        font = QFont("Consolas", size)
        font.setBold(bold)
        painter.setFont(font)
        painter.setPen(color or self.WHITE)
        painter.drawText(int(x), int(y), str(value))

    def line(self, painter, x1, y1, x2, y2, color=None, width=1):
        painter.setPen(self.pen(color, width))
        painter.drawLine(int(x1), int(y1), int(x2), int(y2))

    def panel(self, painter, x, y, width, height, title):
        painter.save()
        painter.setPen(self.pen(self.CYAN_SOFT, 1))
        painter.setBrush(QBrush(QColor(0, 20, 30, 25)))
        painter.drawRoundedRect(QRectF(x, y, width, height), 8, 8)

        painter.setPen(self.pen(self.CYAN, 1))
        painter.drawLine(x + 12, y + 28, x + width - 12, y + 28)

        tab = QPolygonF([
            QPointF(x + 10, y),
            QPointF(x + min(width - 20, 145), y),
            QPointF(x + min(width - 35, 132), y + 18),
            QPointF(x + 10, y + 18),
        ])
        painter.drawPolyline(tab)
        self.text(painter, x + 18, y + 14, title, 9, True, self.CYAN)
        painter.restore()

    def bar(self, painter, x, y, width, height, value):
        value = max(0.0, min(100.0, float(value)))
        painter.save()
        painter.setPen(self.pen(self.CYAN_SOFT, 1))
        painter.setBrush(QBrush(QColor(0, 15, 25, 80)))
        painter.drawRect(int(x), int(y), int(width), int(height))
        fill = int((width - 4) * value / 100.0)
        if fill:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(self.CYAN))
            painter.drawRect(int(x + 2), int(y + 2), fill, int(height - 4))
        painter.restore()

    def glow_circle(self, painter, cx, cy, radius, alpha=35):
        painter.save()
        painter.setPen(Qt.PenStyle.NoPen)
        for spread in (26, 18, 10):
            a = max(5, int(alpha * (1 - (26 - spread) / 30)))
            painter.setBrush(QBrush(QColor(35, 220, 255, a)))
            r = radius + spread
            painter.drawEllipse(QRectF(cx - r, cy - r, r * 2, r * 2))
        painter.restore()

    def draw_boot(self, painter, width, height, progress):
        cx = width / 2
        cy = height / 2
        eased = progress * progress * (3 - 2 * progress)
        painter.save()

        self.glow_circle(painter, cx, cy, 80 + eased * 160, 28)
        painter.setPen(self.pen(self.CYAN, 2))

        for i in range(5):
            r = 40 + eased * 220 - i * 42
            if r > 8:
                painter.drawEllipse(QRectF(cx - r, cy - r, r * 2, r * 2))

        sweep = math.radians(self.scan_angle * 2)
        self.line(painter, cx, cy, cx + math.cos(sweep) * (120 + eased * 480), cy + math.sin(sweep) * (120 + eased * 480), self.CYAN, 2)

        arm = 120 + eased * 620
        self.line(painter, cx - arm, cy, cx - 30, cy, self.CYAN_SOFT, 1)
        self.line(painter, cx + 30, cy, cx + arm, cy, self.CYAN_SOFT, 1)
        self.line(painter, cx, cy - arm, cx, cy - 30, self.CYAN_SOFT, 1)
        self.line(painter, cx, cy + 30, cx, cy + arm, self.CYAN_SOFT, 1)

        self.text(painter, cx - 82, cy - 12, "J A R V I S", 24, True, self.WHITE)
        self.text(painter, cx - 92, cy + 15, "VISOR CORE INITIALIZING", 9, True, self.CYAN)

        blocks = int(eased * 24)
        self.text(painter, cx - 125, cy + 52, "LINK [" + "█" * blocks + "·" * (24 - blocks) + "]", 9, True, self.CYAN)
        self.text(painter, cx - 92, cy + 78, "TELEMETRY  SYNC", 8, False, self.CYAN_SOFT)
        if progress >= 0.9:
            self.text(painter, cx - 30, cy + 112, "ONLINE", 13, True, self.CYAN)
        painter.restore()

    def draw_state_banner(self, painter, width, status):
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

        x = width / 2 - 155
        y = 78
        w = 310
        h = 40

        painter.save()
        painter.setPen(self.pen(self.CYAN, 1))
        painter.setBrush(QBrush(QColor(0, 18, 28, 70)))
        painter.drawRoundedRect(QRectF(x, y, w, h), 8, 8)
        self.text(painter, x + 16, y + 17, "●", 10, True, self.RED if state == "OFFLINE" else self.CYAN)
        self.text(painter, x + 32, y + 17, label, 10, True, self.WHITE)
        self.text(painter, x + 32, y + 33, voice, 8, False, self.CYAN_SOFT)

        if state == "LISTENING":
            level = max(0.0, min(100.0, float(status.get("mic_level", 0)))) / 100.0
            base_x = x + w - 115
            for i in range(10):
                wave = 0.18 + level * 0.82
                wave *= 0.35 + 0.65 * (0.5 + 0.5 * math.sin(self.pulse * 2.5 + i * 0.75))
                bh = max(4, int(24 * wave))
                self.line(painter, base_x + i * 9, y + 27 - bh / 2, base_x + i * 9, y + 27 + bh / 2, self.CYAN, 2)
        elif state in ("THINKING", "PROCESSING"):
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(self.CYAN))
            for i in range(3):
                r = 3 + 2 * (0.5 + 0.5 * math.sin(self.pulse * 3 + i * 1.7))
                painter.drawEllipse(QRectF(x + w - 82 + i * 18 - r, y + 27 - r, r * 2, r * 2))
        elif state == "SPEAKING":
            for i in range(8):
                bh = 5 + int(15 * (0.5 + 0.5 * math.sin(self.pulse * 4 + i * 0.9)))
                self.line(painter, x + w - 98 + i * 10, y + 27 - bh / 2, x + w - 98 + i * 10, y + 27 + bh / 2, self.CYAN, 2)
        painter.restore()

    def draw_state_effects(self, painter, cx, cy, state, mic_level):
        blend = self.state_blend
        painter.save()
        painter.setPen(self.pen(self.CYAN, 1))

        if state == "LISTENING":
            level = max(0.0, min(100.0, mic_level)) / 100.0
            for ring in range(3):
                radius = 178 + ring * 16 + level * (12 + ring * 7) + math.sin(self.pulse * 2 + ring) * 4 + (1 - blend) * 20
                painter.drawEllipse(QRectF(cx - radius, cy - radius, radius * 2, radius * 2))
        elif state in ("THINKING", "PROCESSING"):
            for i in range(32):
                a = math.radians(i * 11.25 + self.angle * 3)
                inner = 185 + 5 * math.sin(self.pulse * 2 + i)
                outer = inner + (18 if i % 4 == 0 else 8)
                self.line(painter, cx + math.cos(a) * inner, cy + math.sin(a) * inner, cx + math.cos(a) * outer, cy + math.sin(a) * outer, self.CYAN, 2 if i % 4 == 0 else 1)
        elif state == "SPEAKING":
            for i in range(20):
                a = math.radians(i * 18 + self.angle)
                amp = 10 + 10 * (0.5 + 0.5 * math.sin(self.pulse * 4 + i))
                r1 = 190
                r2 = r1 + amp
                self.line(painter, cx + math.cos(a) * r1, cy + math.sin(a) * r1, cx + math.cos(a) * r2, cy + math.sin(a) * r2, self.CYAN, 2)
        elif state == "OFFLINE":
            self.line(painter, cx - 28, cy - 28, cx + 28, cy + 28, self.RED, 3)
            self.line(painter, cx + 28, cy - 28, cx - 28, cy + 28, self.RED, 3)

        painter.restore()

    def graph(self, painter, x, y, width, height, values, title):
        painter.save()
        painter.setPen(self.pen(self.CYAN_SOFT, 1))
        painter.setBrush(QBrush(QColor(0, 15, 25, 45)))
        painter.drawRoundedRect(QRectF(x, y, width, height), 6, 6)
        self.text(painter, x + 10, y + 17, title, 8, True, self.CYAN)

        for row in range(1, 4):
            gy = y + 24 + row * (height - 30) / 4
            self.line(painter, x + 6, gy, x + width - 6, gy, self.CYAN_FAINT, 1)

        points = []
        usable_h = height - 30
        for i, value in enumerate(values):
            px = x + 7 + (i / max(1, len(values) - 1)) * (width - 14)
            clamped = max(0.0, min(100.0, float(value)))
            py = y + height - 7 - (clamped / 100.0) * usable_h
            points.append((px, py))

        painter.setPen(self.pen(self.CYAN, 1))
        for a, b in zip(points, points[1:]):
            painter.drawLine(int(a[0]), int(a[1]), int(b[0]), int(b[1]))
        painter.restore()

    def draw_frame(self, painter, width, height):
        painter.save()
        margin = 22
        length = min(185, max(110, int(width * 0.11)))
        depth = 62
        corners = [
            (margin, margin, 1, 1),
            (width - margin, margin, -1, 1),
            (margin, height - margin, 1, -1),
            (width - margin, height - margin, -1, -1),
        ]

        for x, y, dx, dy in corners:
            self.line(painter, x, y, x + dx * length, y, self.CYAN, 2)
            self.line(painter, x, y, x, y + dy * depth, self.CYAN, 2)
            self.line(painter, x + dx * 22, y, x + dx * 22, y + dy * 38, self.CYAN_SOFT, 1)

        rail_y_top = 24
        rail_y_bottom = height - 24
        self.line(painter, width * 0.32, rail_y_top, width * 0.68, rail_y_top, self.CYAN_SOFT, 1)
        self.line(painter, width * 0.32, rail_y_bottom, width * 0.68, rail_y_bottom, self.CYAN_SOFT, 1)

        for i in range(18):
            tick_x = width * 0.34 + i * (width * 0.32 / 18)
            tick_h = 4 + (5 if i % 3 == 0 else 0)
            self.line(painter, tick_x, rail_y_top - tick_h / 2, tick_x, rail_y_top + tick_h / 2, self.CYAN, 1)
        painter.restore()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()
        cx = width / 2
        cy = height / 2

        status = self.read_status()
        state = str(status.get("status", "STANDBY")).upper()

        elapsed = time.time() - self.boot_start
        if elapsed < self.boot_duration:
            self.draw_boot(painter, width, height, min(1.0, elapsed / self.boot_duration))
            return

        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        disk = psutil.disk_usage(os.path.abspath(os.sep)).percent
        net = psutil.net_io_counters()
        now = datetime.datetime.now()
        mic_level = float(status.get("mic_level", 0))

        self.cpu_history.append(cpu)
        self.cpu_history = self.cpu_history[-80:]
        self.ram_history.append(ram)
        self.ram_history = self.ram_history[-80:]

        self.draw_frame(painter, width, height)
        self.text(painter, cx - 105, 43, "J A R V I S  //  VISOR", 13, True, self.WHITE)
        self.text(painter, cx - 92, 59, "LOCAL NEURAL INTERFACE", 8, False, self.CYAN_SOFT)
        self.draw_state_banner(painter, width, status)

        self.panel(painter, 42, 105, 310, 275, "SYSTEM TELEMETRY")
        self.text(painter, 58, 143, f"CPU       {cpu:5.1f}%", 10, True)
        self.bar(painter, 160, 133, 175, 12, cpu)
        self.text(painter, 58, 177, f"MEMORY    {ram:5.1f}%", 10, True)
        self.bar(painter, 160, 167, 175, 12, ram)
        self.text(painter, 58, 211, f"STORAGE   {disk:5.1f}%", 10, True)
        self.bar(painter, 160, 201, 175, 12, disk)
        self.text(painter, 58, 248, f"TIME      {now.strftime('%I:%M:%S %p')}", 10)
        self.text(painter, 58, 278, f"DATE      {now.strftime('%m/%d/%Y')}", 10)
        self.text(painter, 58, 310, f"NET RX    {net.bytes_recv / 1024 / 1024:,.1f} MB", 9)
        self.text(painter, 58, 335, f"NET TX    {net.bytes_sent / 1024 / 1024:,.1f} MB", 9)
        self.text(painter, 58, 360, "PROCESSOR LINK   STABLE", 8, True, self.CYAN)

        right_x = width - 352
        self.panel(painter, right_x, 105, 310, 275, "LINK STATUS")
        self.text(painter, right_x + 16, 143, f"VOICE     {status.get('voice', 'UNKNOWN')}", 10, True)
        self.text(painter, right_x + 16, 177, f"STATE     {state}", 10, True)
        self.text(painter, right_x + 16, 211, "NETWORK   LOCAL", 10)
        self.text(painter, right_x + 16, 245, f"MIC       {mic_level:5.1f}%", 10)
        self.bar(painter, right_x + 110, 235, 175, 12, mic_level)
        self.text(painter, right_x + 16, 280, "VOICE ENGINE      READY", 9)
        self.text(painter, right_x + 16, 307, "HUD ENGINE        ONLINE", 9, True, self.CYAN)
        self.text(painter, right_x + 16, 334, "NEURAL LINK       ACTIVE", 9)
        self.text(painter, right_x + 16, 361, "LOCAL CONTROL     ENABLED", 8)

        self.glow_circle(painter, cx, cy + 18, 72, 35)
        painter.save()
        painter.setPen(self.pen(self.CYAN_SOFT, 1))
        for radius in (58, 98, 145, 176):
            painter.drawEllipse(QRectF(cx - radius, cy + 18 - radius, radius * 2, radius * 2))

        for i in range(0, 360, 12):
            a = math.radians(i + self.angle)
            inner = 152 if i % 36 else 145
            outer = 170 if i % 36 else 182
            self.line(painter, cx + math.cos(a) * inner, cy + 18 + math.sin(a) * inner, cx + math.cos(a) * outer, cy + 18 + math.sin(a) * outer, self.CYAN, 2 if i % 36 == 0 else 1)

        sweep = math.radians(self.scan_angle)
        self.line(painter, cx, cy + 18, cx + math.cos(sweep) * 205, cy + 18 + math.sin(sweep) * 205, self.CYAN_SOFT, 1)

        core_r = 25 + 4 * math.sin(self.pulse * 2)
        painter.setPen(self.pen(self.CYAN, 2))
        painter.drawEllipse(QRectF(cx - core_r, cy + 18 - core_r, core_r * 2, core_r * 2))
        painter.restore()

        self.draw_state_effects(painter, cx, cy + 18, state, mic_level)
        self.text(painter, cx - 25, cy + 22, "CORE", 8, True, self.CYAN)
        self.text(painter, cx - 68, cy + 40, state, 8, True, self.WHITE)

        self.graph(painter, cx - 345, height - 165, 300, 105, self.cpu_history, "CPU HISTORY")
        self.graph(painter, cx + 45, height - 165, 300, 105, self.ram_history, "MEMORY HISTORY")

        self.panel(painter, 42, height - 165, 330, 105, "LAST COMMAND")
        command = str(status.get("last_command", "None"))
        self.text(painter, 58, height - 115, command[:42], 9, True)
        self.text(painter, 58, height - 88, "WAKE WORD    JARVIS", 8, False, self.CYAN_SOFT)
        self.text(painter, 58, height - 64, "COMMAND LINK READY", 8, True, self.CYAN)

        diag_x = width - 372
        self.panel(painter, diag_x, height - 165, 330, 105, "DIAGNOSTICS")
        self.text(painter, diag_x + 16, height - 115, "CORE LINK       STABLE", 8)
        self.text(painter, diag_x + 16, height - 91, "VOICE ENGINE    READY", 8)
        self.text(painter, diag_x + 16, height - 67, "ALL SYSTEMS     NOMINAL", 8, True, self.CYAN)

        self.text(painter, 42, height - 25, "JARVIS // ORIGINAL VISOR INTERFACE", 8, True, self.CYAN_SOFT)
        self.text(painter, width - 205, height - 25, "LOCAL MONITORING", 8, False, self.CYAN_SOFT)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    hud = JarvisHUD()
    hud.show()
    sys.exit(app.exec())
