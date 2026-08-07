import sys
import json
import psutil
import datetime

from PySide6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt, QTimer


class JarvisHUD(QWidget):

    def __init__(self):

        super().__init__()


        # Transparent window
        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground
        )


        self.setWindowTitle(
            "Jarvis HUD"
        )


        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )


        # Size and position
        self.resize(
            350,
            250
        )


        # Top-left corner
        self.move(
            20,
            20
        )


        self.label = QLabel()


        self.label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )


        self.label.setStyleSheet(
            """
            QLabel {

                color: cyan;

                background-color: rgba(0, 0, 0, 120);

                border: 2px solid rgba(0, 255, 255, 180);

                border-radius: 15px;

                font-size: 16px;

                padding: 15px;

            }
            """
        )


        layout = QVBoxLayout()

        layout.addWidget(
            self.label
        )

        self.setLayout(
            layout
        )


        self.timer = QTimer()


        self.timer.timeout.connect(
            self.update_hud
        )


        self.timer.start(
            1000
        )



    def read_status(self):

        try:

            with open(
                "status.json",
                "r"
            ) as file:

                return json.load(file)


        except:

            return {
                "status": "OFFLINE",
                "voice": "UNKNOWN",
                "last_command": "None"
            }



    def update_hud(self):


        status = self.read_status()


        cpu = psutil.cpu_percent()

        ram = psutil.virtual_memory().percent


        current_time = datetime.datetime.now().strftime(
            "%I:%M:%S %p"
        )


        self.label.setText(
f"""
🤖 JARVIS ONLINE


🎤 Voice:
{status["voice"]}


🟢 Status:
{status["status"]}


⚙ CPU:
{cpu}%


🧠 RAM:
{ram}%


📌 Last Command:
{status["last_command"]}


🕒 {current_time}
"""
        )



app = QApplication(
    sys.argv
)


hud = JarvisHUD()

hud.show()


sys.exit(
    app.exec()
)
