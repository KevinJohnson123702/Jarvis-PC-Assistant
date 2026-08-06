
import os
import pyautogui
import subprocess
from datetime import datetime


def lock_pc():
    os.system("rundll32.exe user32.dll,LockWorkStation")
    return {
        "status": "PC locked"
    }


def shutdown_pc():
    os.system("shutdown /s /t 5")
    return {
        "status": "Shutdown started"
    }


def restart_pc():
    os.system("shutdown /r /t 5")
    return {
        "status": "Restart started"
    }


def take_screenshot():
    filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

    image = pyautogui.screenshot()
    image.save(filename)

    return {
        "status": "Screenshot saved",
        "file": filename
    }


def open_calculator():
    subprocess.Popen("calc.exe")

    return {
        "status": "Calculator opened"
    }
