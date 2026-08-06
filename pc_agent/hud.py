import sys
import psutil
import datetime

from PySide6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt, QTimer


class JarvisHUD(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Jarvis HUD")

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )

        self.resize(350, 250)


        self.label = QLabel()

        self.label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )


        self.label.setStyleSheet("""
        QLabel {
            color: cyan;
            background-color: rgba(0,0,0,200);
            border: 2px solid cyan;
            border-radius: 20px;
            font-size: 18px;
            padding: 20px;
        }
        """)


        layout = QVBoxLayout()

        layout.addWidget(self.label)

        self.setLayout(layout)


        self.timer = QTimer()

        self.timer.timeout.connect(
            self.update_hud
        )

        self.timer.start(1000)


    def update_hud(self):

        cpu = psutil.cpu_percent()

        ram = psutil.virtual_memory().percent

        current_time = datetime.datetime.now().strftime(
            "%I:%M:%S %p"
        )


        self.label.setText(
f"""
🤖 JARVIS ONLINE

🎤 Voice: READY

🟢 Status: STANDBY

⚙ CPU: {cpu}%

🧠 RAM: {ram}%

🕒 {current_time}
"""
        )



app = QApplication(sys.argv)

hud = JarvisHUD()

hud.show()

sys.exit(app.exec())
