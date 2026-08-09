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

        # Animation
        self.angle = 0.0
        self.pulse = 0.0
        self.scan_angle = 0.0

        # Boot
        self.boot_start = time.time()
        self.boot_duration = 3.2

        # State transitions
        self.last_state = "BOOT"
        self.transition = 1.0

        # Graph history
        self.cpu_history = [0.0] * 60
        self.ram_history = [0.0] * 60

        # Animation timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(35)

    # ---------------------------------------------------------
    # STATUS
    # ---------------------------------------------------------

    def read_status(self):
        try:
            with open(STATUS_FILE, "r", encoding="utf-8") as file:
                return json.load(file)

        except Exception:
            return {
                "status": "OFFLINE",
                "voice": "UNKNOWN",
                "last_command": "None",
                "mic_level": 0
            }

    # ---------------------------------------------------------
    # ANIMATION
    # ---------------------------------------------------------

    def animate(self):
        self.angle = (self.angle + 2.5) % 360
        self.scan_angle = (self.scan_angle + 4.0) % 360
        self.pulse = (self.pulse + 0.08) % (math.pi * 2)

        status = self.read_status()
        state = str(
            status.get("status", "STANDBY")
        ).upper()

        # Smooth transition whenever state changes
        if state != self.last_state:
            self.last_state = state
            self.transition = 0.0
        else:
            self.transition = min(
                1.0,
                self.transition + 0.045
            )

        self.update()

    # ---------------------------------------------------------
    # TEXT
    # ---------------------------------------------------------

    def text(
        self,
        painter,
        x,
        y,
        value,
        size=11,
        bold=False
    ):
        font = QFont("Consolas", size)
        font.setBold(bold)

        painter.setFont(font)
        painter.drawText(
            int(x),
            int(y),
            str(value)
        )

    # ---------------------------------------------------------
    # PANELS
    # ---------------------------------------------------------

    def panel(
        self,
        painter,
        x,
        y,
        width,
        height,
        title
    ):
        painter.save()

        painter.setPen(
            QPen(
                Qt.GlobalColor.cyan,
                1
            )
        )

        painter.drawRect(
            x,
            y,
            width,
            height
        )

        self.text(
            painter,
            x + 12,
            y + 20,
            title,
            10,
            True
        )

        painter.drawLine(
            x + 10,
            y + 28,
            x + width - 10,
            y + 28
        )

        painter.restore()

    # ---------------------------------------------------------
    # PROGRESS BAR
    # ---------------------------------------------------------

    def bar(
        self,
        painter,
        x,
        y,
        width,
        height,
        value
    ):
        value = max(
            0,
            min(
                100,
                float(value)
            )
        )

        painter.drawRect(
            x,
            y,
            width,
            height
        )

        fill = int(
            (width - 4)
            * value
            / 100
        )

        if fill > 0:
            painter.drawRect(
                x + 2,
                y + 2,
                fill,
                height - 4
            )

    # ---------------------------------------------------------
    # BOOT SEQUENCE
    # ---------------------------------------------------------

    def draw_boot(
        self,
        painter,
        width,
        height,
        progress
    ):
        cx = width // 2
        cy = height // 2

        painter.save()

        painter.setPen(
            QPen(
                Qt.GlobalColor.cyan,
                2
            )
        )

        # Smooth easing
        eased = (
            progress
            * progress
            * (3 - 2 * progress)
        )

        # Expanding rings
        max_radius = int(
            70
            + eased * 300
        )

        for i in range(6):
            radius = max(
                18,
                max_radius - i * 55
            )

            painter.drawEllipse(
                QRectF(
                    cx - radius,
                    cy - radius,
                    radius * 2,
                    radius * 2
                )
            )

        # Crosshair
        line_length = int(
            120
            + eased * 750
        )

        painter.drawLine(
            cx - line_length,
            cy,
            cx + line_length,
            cy
        )

        painter.drawLine(
            cx,
            cy - line_length,
            cx,
            cy + line_length
        )

        # Title
        self.text(
            painter,
            cx - 155,
            cy - 35,
            "J A R V I S",
            25,
            True
        )

        self.text(
            painter,
            cx - 135,
            cy - 8,
            "VISOR INITIALIZING",
            11
        )

        # Progress bar
        blocks = int(
            eased * 22
        )

        self.text(
            painter,
            cx - 145,
            cy + 42,
            "SYSTEM LINK ["
            + "█" * blocks
            + "·" * (22 - blocks)
            + "]",
            10
        )

        self.text(
            painter,
            cx - 126,
            cy + 72,
            "NEURAL CORE  ::  LOADED",
            9
        )

        self.text(
            painter,
            cx - 110,
            cy + 94,
            "TELEMETRY    ::  SYNCED",
            9
        )

        if progress >= 0.9:
            self.text(
                painter,
                cx - 40,
                cy + 125,
                "ONLINE",
                15,
                True
            )

        painter.restore()

    # ---------------------------------------------------------
    # STATE BANNER
    # ---------------------------------------------------------

    def draw_state_banner(
        self,
        painter,
        width,
        status
    ):
        state = str(
            status.get(
                "status",
                "STANDBY"
            )
        ).upper()

        voice = str(
            status.get(
                "voice",
                "READY"
            )
        ).upper()

        labels = {
            "LISTENING": "LISTENING",
            "SPEAKING": "SPEAKING",
            "THINKING": "THINKING",
            "PROCESSING": "THINKING",
            "WAKE WORD DETECTED": "WAKE SIGNAL",
            "COMMAND RECEIVED": "COMMAND RECEIVED",
            "STANDBY": "STANDBY",
            "OFFLINE": "OFFLINE"
        }

        label = labels.get(
            state,
            state
        )

        painter.setPen(
            QPen(
                Qt.GlobalColor.cyan,
                2
            )
        )

        painter.drawRect(
            width // 2 - 145,
            82,
            290,
            34
        )

        self.text(
            painter,
            width // 2 - 128,
            104,
            f"● {label}  //  {voice}",
            10,
            True
        )

        # Microphone waveform
        if state == "LISTENING":

            level = max(
                0,
                min(
                    100,
                    float(
                        status.get(
                            "mic_level",
                            0
                        )
                    )
                )
            )

            for i in range(12):

                wave = (
                    0.25
                    + level / 100.0
                ) * (
                    0.35
                    + 0.65
                    * (
                        0.5
                        + 0.5
                        * math.sin(
                            self.pulse * 2
                            + i * 0.8
                        )
                    )
                )

                bar_height = max(
                    4,
                    int(
                        32 * wave
                    )
                )

                painter.drawRect(
                    width // 2 - 130
                    + i * 22,
                    124 - bar_height // 2,
                    10,
                    bar_height
                )

        # Thinking / speaking indicators
        elif state in (
            "SPEAKING",
            "THINKING",
            "PROCESSING"
        ):

            for i in range(10):

                radius = (
                    2
                    + int(
                        3
                        * (
                            0.5
                            + 0.5
                            * math.sin(
                                self.pulse * 3
                                + i
                            )
                        )
                    )
                )

                painter.drawEllipse(
                    QRectF(
                        width // 2
                        + 160
                        + i * 8,
                        98 - radius / 2,
                        radius,
                        radius
                    )
                )

    # ---------------------------------------------------------
    # GRAPH
    # ---------------------------------------------------------

    def graph(
        self,
        painter,
        x,
        y,
        width,
        height,
        values,
        title
    ):
        painter.save()

        painter.setPen(
            QPen(
                Qt.GlobalColor.cyan,
                1
            )
        )

        painter.drawRect(
            x,
            y,
            width,
            height
        )

        self.text(
            painter,
            x + 8,
            y + 17,
            title,
            8,
            True
        )

        points = []

        for i, value in enumerate(values):

            px = (
                x
                + 5
                + (
                    i
                    / max(
                        1,
                        len(values) - 1
                    )
                )
                * (
                    width - 10
                )
            )

            py = (
                y
                + height
                - 6
                - (
                    max(
                        0,
                        min(
                            100,
                            value
                        )
                    )
                    / 100
                )
                * (
                    height - 28
                )
            )

            points.append(
                (
                    px,
                    py
                )
            )

        for a, b in zip(
            points,
            points[1:]
        ):
            painter.drawLine(
                int(a[0]),
                int(a[1]),
                int(b[0]),
                int(b[1])
            )

        painter.restore()

    # ---------------------------------------------------------
    # VISOR STATE EFFECTS
    # ---------------------------------------------------------

    def draw_state_effects(
        self,
        painter,
        cx,
        cy,
        state
    ):
        blend = self.transition

        # LISTENING
        if state == "LISTENING":

            status = self.read_status()

            level = max(
                0,
                min(
                    100,
                    float(
                        status.get(
                            "mic_level",
                            0
                        )
                    )
                )
            ) / 100

            for ring in range(3):

                radius = (
                    185
                    + ring * 18
                    + (1 - blend) * 14
                    + level
                    * (8 + ring * 5)
                    + 5
                    * math.sin(
                        self.pulse * 2
                        + ring
                    )
                )

                painter.drawEllipse(
                    QRectF(
                        cx - radius,
                        cy - radius,
                        radius * 2,
                        radius * 2
                    )
                )

        # THINKING
        elif state in (
            "THINKING",
            "PROCESSING"
        ):

            for i in range(24):

                angle = math.radians(
                    i * 15
                    + self.angle * 3
                )

                radius1 = (
                    195
                    + 8
                    * math.sin(
                        self.pulse * 2
                        + i
                    )
                )

                radius2 = (
                    radius1
                    + (
                        8
                        if i % 2 == 0
                        else 20
                    )
                )

                painter.drawLine(
                    int(
                        cx
                        + math.cos(angle)
                        * radius1
                    ),
                    int(
                        cy
                        + math.sin(angle)
                        * radius1
                    ),
                    int(
                        cx
                        + math.cos(angle)
                        * radius2
                    ),
                    int(
                        cy
                        + math.sin(angle)
                        * radius2
                    )
                )

        # SPEAKING
        elif state == "SPEAKING":

            for i in range(16):

                angle = math.radians(
                    i * 22.5
                    + self.angle
                )

                radius = (
                    205
                    + 14
                    * math.sin(
                        self.pulse * 4
                        + i
                    )
                )

                painter.drawLine(
                    int(
                        cx
                        + math.cos(angle)
                        * (radius - 10)
                    ),
                    int(
                        cy
                        + math.sin(angle)
                        * (radius - 10)
                    ),
                    int(
                        cx
                        + math.cos(angle)
                        * radius
                    ),
                    int(
                        cy
                        + math.sin(angle)
                        * radius
                    )
                )

        # STANDBY
        elif state == "STANDBY":

            radius = (
                190
                + 3
                * math.sin(
                    self.pulse
                )
            )

            painter.drawEllipse(
                QRectF(
                    cx - radius,
                    cy - radius,
                    radius * 2,
                    radius * 2
                )
            )

        # OFFLINE
        elif state == "OFFLINE":

            painter.setPen(
                QPen(
                    Qt.GlobalColor.red,
                    2
                )
            )

            painter.drawLine(
                cx - 25,
                cy - 25,
                cx + 25,
                cy + 25
            )

            painter.drawLine(
                cx + 25,
                cy - 25,
                cx - 25,
                cy + 25
            )

    # ---------------------------------------------------------
    # PAINT HUD
    # ---------------------------------------------------------

    def paintEvent(self, event):

        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        width = self.width()
        height = self.height()

        cx = width // 2
        cy = height // 2

        status = self.read_status()

        state = str(
            status.get(
                "status",
                "STANDBY"
            )
        ).upper()

        # Boot
        elapsed = (
            time.time()
            - self.boot_start
        )

        if elapsed < self.boot_duration:

            self.draw_boot(
                painter,
                width,
                height,
                min(
                    1.0,
                    elapsed
                    / self.boot_duration
                )
            )

            return

        # System information
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent

        disk = psutil.disk_usage(
            os.path.abspath(
                os.sep
            )
        ).percent

        net = psutil.net_io_counters()

        now = datetime.datetime.now()

        uptime = max(
            0,
            int(
                time.time()
                - psutil.boot_time()
            )
        )

        uptime_hours = uptime // 3600

        uptime_minutes = (
            uptime % 3600
        ) // 60

        self.cpu_history.append(cpu)
        self.cpu_history = (
            self.cpu_history[-60:]
        )

        self.ram_history.append(ram)
        self.ram_history = (
            self.ram_history[-60:]
        )

        # -----------------------------------------------------
        # CORNER VISOR FRAME
        # -----------------------------------------------------

        painter.setPen(
            QPen(
                Qt.GlobalColor.cyan,
                2
            )
        )

        margin = 24
        corner = 145

        corners = [
            (
                margin,
                margin,
                1,
                1
            ),
            (
                width - margin,
                margin,
                -1,
                1
            ),
            (
                margin,
                height - margin,
                1,
                -1
            ),
            (
                width - margin,
                height - margin,
                -1,
                -1
            )
        ]

        for x, y, dx, dy in corners:

            painter.drawLine(
                x,
                y,
                x + dx * corner,
                y
            )

            painter.drawLine(
                x,
                y,
                x,
                y + dy * corner
            )

            painter.drawLine(
                x + dx * 20,
                y,
                x + dx * 20,
                y + dy * 52
            )

        # -----------------------------------------------------
        # HEADER
        # -----------------------------------------------------

        self.text(
            painter,
            cx - 125,
            42,
            "J A R V I S  //  VISOR",
            14,
            True
        )

        self.text(
            painter,
            cx - 96,
            61,
            "NEURAL INTERFACE ONLINE",
            9
        )

        self.draw_state_banner(
            painter,
            width,
            status
        )

        # -----------------------------------------------------
        # SYSTEM TELEMETRY
        # -----------------------------------------------------

        self.panel(
            painter,
            45,
            90,
            315,
            285,
            "SYSTEM TELEMETRY"
        )

        self.text(
            painter,
            60,
            122,
            f"CPU       {cpu:5.1f}%",
            11
        )

        self.bar(
            painter,
            170,
            113,
            170,
            13,
            cpu
        )

        self.text(
            painter,
            60,
            157,
            f"MEMORY    {ram:5.1f}%",
            11
        )

        self.bar(
            painter,
            170,
            148,
            170,
            13,
            ram
        )

        self.text(
            painter,
            60,
            192,
            f"STORAGE   {disk:5.1f}%",
            11
        )

        self.bar(
            painter,
            170,
            183,
            170,
            13,
            disk
        )

        self.text(
            painter,
            60,
            228,
            f"UPTIME    {uptime_hours:02d}h "
            f"{uptime_minutes:02d}m",
            11
        )

        self.text(
            painter,
            60,
            259,
            f"TIME      "
            f"{now.strftime('%I:%M:%S %p')}",
            11
        )

        self.text(
            painter,
            60,
            290,
            f"DATE      "
            f"{now.strftime('%m/%d/%Y')}",
            11
        )

        self.text(
            painter,
            60,
            320,
            "PROCESSOR LINK    STABLE",
            9
        )

        self.text(
            painter,
            60,
            345,
            f"NET RX     "
            f"{net.bytes_recv / 1024 / 1024:,.1f} MB",
            9
        )

        self.text(
            painter,
            60,
            365,
            f"NET TX     "
            f"{net.bytes_sent / 1024 / 1024:,.1f} MB",
            9
        )

        # -----------------------------------------------------
        # LINK STATUS
        # -----------------------------------------------------

        self.panel(
            painter,
            width - 360,
            90,
            315,
            285,
            "LINK STATUS"
        )

        self.text(
            painter,
            width - 345,
            122,
            f"VOICE     "
            f"{status.get('voice', 'UNKNOWN')}",
            11
        )

        self.text(
            painter,
            width - 345,
            153,
            f"STATE     "
            f"{status.get('status', 'UNKNOWN')}",
            11
        )

        self.text(
            painter,
            width - 345,
            184,
            "NETWORK   ONLINE",
            11
        )

        self.text(
            painter,
            width - 345,
            215,
            f"RX        "
            f"{net.bytes_recv / 1024 / 1024:,.1f} MB",
            10
        )

        self.text(
            painter,
            width - 345,
            244,
            f"TX        "
            f"{net.bytes_sent / 1024 / 1024:,.1f} MB",
            10
        )

        self.text(
            painter,
            width - 345,
            275,
            "MIC       READY",
            10
        )

        self.text(
            painter,
            width - 345,
            306,
            "NEURAL TTS ACTIVE",
            9,
            True
        )

        mic_level = float(
            status.get(
                "mic_level",
                0
            )
        )

        self.text(
            painter,
            width - 345,
            336,
            f"MIC LEVEL {mic_level:5.1f}%",
            9
        )

        self.bar(
            painter,
            width - 190,
            328,
            140,
            12,
            mic_level
        )

        # -----------------------------------------------------
        # CENTRAL VISOR
        # -----------------------------------------------------

        for radius in (
            62,
            106,
            158
        ):

            painter.drawEllipse(
                QRectF(
                    cx - radius,
                    cy - radius,
                    radius * 2,
                    radius * 2
                )
            )

        # Crosshair
        painter.drawLine(
            cx - 270,
            cy,
            cx - 180,
            cy
        )

        painter.drawLine(
            cx + 180,
            cy,
            cx + 270,
            cy
        )

        painter.drawLine(
            cx,
            cy - 270,
            cx,
            cy - 180
        )

        painter.drawLine(
            cx,
            cy + 180,
            cx,
            cy + 270
        )

        # Rotating targeting ticks
        for i in range(
            0,
            360,
            10
        ):

            angle = math.radians(
                i + self.angle
            )

            inner = (
                168
                if i % 30
                else 155
            )

            outer = (
                180
                if i % 30
                else 195
            )

            painter.drawLine(
                int(
                    cx
                    + math.cos(angle)
                    * inner
                ),
                int(
                    cy
                    + math.sin(angle)
                    * inner
                ),
                int(
                    cx
                    + math.cos(angle)
                    * outer
                ),
                int(
                    cy
                    + math.sin(angle)
                    * outer
                )
            )

        # Rotating scanner beam
        sweep = math.radians(
            self.scan_angle
        )

        painter.drawLine(
            cx,
            cy,
            int(
                cx
                + math.cos(sweep)
                * 230
            ),
            int(
                cy
                + math.sin(sweep)
                * 230
            )
        )

        # State-specific effects
        self.draw_state_effects(
            painter,
            cx,
            cy,
            state
        )

        # -----------------------------------------------------
        # GRAPHS
        # -----------------------------------------------------

        self.graph(
            painter,
            cx - 340,
            height - 205,
            315,
            115,
            self.cpu_history,
            "CPU HISTORY"
        )

        self.graph(
            painter,
            cx + 25,
            height - 205,
            315,
            115,
            self.ram_history,
            "MEMORY HISTORY"
        )

        # -----------------------------------------------------
        # LAST COMMAND
        # -----------------------------------------------------

        self.panel(
            painter,
            45,
            height - 210,
            470,
            150,
            "LAST COMMAND"
        )

        self.text(
            painter,
            62,
            height - 150,
            str(
                status.get(
                    "last_command",
                    "None"
                )
            )[:52],
            12,
            True
        )

        self.text(
            painter,
            62,
            height - 117,
            "VOICE CHANNEL: ACTIVE",
            9
        )

        self.text(
            painter,
            62,
            height - 91,
            "WAKE WORD: JARVIS",
            9
        )

        self.text(
            painter,
            62,
            height - 65,
            "COMMAND BUFFER: READY",
            9
        )

        # -----------------------------------------------------
        # DIAGNOSTICS
        # -----------------------------------------------------

        self.panel(
            painter,
            width - 515,
            height - 210,
            470,
            150,
            "DIAGNOSTICS"
        )

        self.text(
            painter,
            width - 498,
            height - 150,
            "CORE LINK         STABLE",
            9
        )

        self.text(
            painter,
            width - 498,
            height - 123,
            "HUD ENGINE        ONLINE",
            9
        )

        self.text(
            painter,
            width - 498,
            height - 96,
            "VOICE ENGINE      READY",
            9
        )

        self.text(
            painter,
            width - 498,
            height - 69,
            "ALL SYSTEMS       NOMINAL",
            9,
            True
        )

        # Footer
        self.text(
            painter,
            45,
            height - 34,
            "JARVIS // VISOR LINK ACTIVE",
            9,
            True
        )

        self.text(
            painter,
            width - 210,
            height - 34,
            "SYSTEM MONITORING",
            9
        )


# -------------------------------------------------------------
# START HUD
# -------------------------------------------------------------

app = QApplication(sys.argv)

hud = JarvisHUD()
hud.show()

sys.exit(
    app.exec()
)
