import os
import pyautogui
import subprocess
from datetime import datetime


SCREENSHOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)


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
    filepath = os.path.join(SCREENSHOT_DIR, filename)

    image = pyautogui.screenshot()
    image.save(filepath)

    return {
        "status": "Screenshot saved",
        "file": filepath
    }


def open_discord():
    """Open the installed Discord app, with the web version as a fallback."""
    try:
        subprocess.Popen(["cmd", "/c", "start", "", "discord://"], shell=False)
        return {
            "status": "Discord opened"
        }
    except Exception:
        try:
            subprocess.Popen(["cmd", "/c", "start", "", "https://discord.com/app"], shell=False)
            return {
                "status": "Discord web opened"
            }
        except Exception as e:
            return {
                "status": "Could not open Discord",
                "error": str(e)
            }
