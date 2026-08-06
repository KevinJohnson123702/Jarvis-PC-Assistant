import os
import pyautogui
from datetime import datetime


def lock_pc():
    os.system("rundll32.exe user32.dll,LockWorkStation")
    return {
        "status": "PC locked"
    }


def take_screenshot():
    filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

    image = pyautogui.screenshot()
    image.save(filename)

    return {
        "status": "Screenshot saved",
        "file": filename
    }
