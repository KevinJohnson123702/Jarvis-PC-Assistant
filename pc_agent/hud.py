import sys
import psutil
import time

from PySide6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt, QTimer


class JarvisHUD(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Jarvis HUD")

        # Window settings
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )

        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground
        )

        self.resize(300, 180)


        self.label = QLabel()

        self.label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )


        self.label.setStyleSheet("""
            QLabel {
                color: #00ffff;
                font-size: 18px;
                background-color: rgba(0,0,0,170);
                border: 2px solid #00ffff;
                border-radius: 15px;
                padding: 15px;
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


        self.update_hud()



    def update_hud(self):

        cpu = psutil.cpu_percent()

        ram = psutil.virtual_memory().percent

        now = time.strftime(
            "%I:%M:%S %p"
        )


        self.label.setText(
f"""
🤖 JARVIS ONLINE

⚙️ CPU: {cpu}%

🧠 RAM: {ram}%

⏰ {now}

🎤 VOICE READY
"""
        )



app = QApplication(sys.argv)


hud = JarvisHUD()

hud.show()


sys.exit(app.exec())
