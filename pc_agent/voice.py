import os
import sys
import json
import wave
import datetime
import subprocess
import webbrowser
import re
import asyncio
import tempfile

import sounddevice as sd
import speech_recognition as sr
import edge_tts

from actions import open_discord, take_screenshot, lock_pc

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATUS_FILE = os.path.join(BASE_DIR, "status.json")
AUDIO_FILE = os.path.join(BASE_DIR, "voice.wav")
HUD_PROCESS = None
TTS_VOICE = "en-US-GuyNeural"
TTS_RATE = "-8%"
TTS_VOLUME = "+0%"


def update_status(status, voice="READY", command="None"):
    try:
        with open(STATUS_FILE, "w", encoding="utf-8") as file:
            json.dump({"status": status, "voice": voice, "last_command": command}, file, indent=4)
    except Exception as e:
        print("Status error:", e)


async def _generate_speech(text, output_file):
    communicate = edge_tts.Communicate(text, TTS_VOICE, rate=TTS_RATE, volume=TTS_VOLUME, pitch="-2Hz")
    await communicate.save(output_file)


def _play_audio_windows(audio_file):
    escaped = audio_file.replace("'", "''")
    ps_script = f'''
Add-Type -AssemblyName PresentationCore
$player = New-Object System.Windows.Media.MediaPlayer
$player.Open([Uri]::new('{escaped}'))
$timeout = [DateTime]::UtcNow.AddSeconds(10)
while (-not $player.NaturalDuration.HasTimeSpan -and [DateTime]::UtcNow -lt $timeout) {{ Start-Sleep -Milliseconds 100 }}
if (-not $player.NaturalDuration.HasTimeSpan) {{ throw "Audio file could not be opened." }}
$seconds = [Math]::Ceiling($player.NaturalDuration.TimeSpan.TotalSeconds)
$player.Play()
Start-Sleep -Seconds $seconds
$player.Stop()
$player.Close()
'''
    result = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", ps_script], capture_output=True, text=True, timeout=25)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Windows audio playback failed")


def speak(text):
    print("Jarvis:", text)
    update_status("SPEAKING", "ACTIVE", text)
    output_file = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp:
            output_file = temp.name
        asyncio.run(_generate_speech(text, output_file))
        _play_audio_windows(output_file)
    except Exception as e:
        print("Neural TTS error:", e)
        print("Jarvis text:", text)
    finally:
        if output_file:
            try:
                os.remove(output_file)
            except OSError:
                pass
        update_status("STANDBY", "READY", text)


def show_hud():
    global HUD_PROCESS
    if HUD_PROCESS is not None and HUD_PROCESS.poll() is None:
        return
    HUD_PROCESS = None
    hud_file = os.path.join(BASE_DIR, "hud.py")
    if not os.path.exists(hud_file):
        speak("I cannot find the HUD.")
        return
    try:
        HUD_PROCESS = subprocess.Popen([sys.executable, hud_file], cwd=BASE_DIR)
        print("HUD started.")
    except Exception as e:
        print("HUD error:", e)
        HUD_PROCESS = None


def hide_hud():
    global HUD_PROCESS
    if HUD_PROCESS is None:
        print("HUD is already hidden.")
        return
    pid = HUD_PROCESS.pid
    try:
        HUD_PROCESS.terminate()
        HUD_PROCESS.wait(timeout=2)
    except Exception:
        try:
            subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True)
        except Exception as e:
            print("HUD close error:", e)
    HUD_PROCESS = None
    print("HUD hidden.")


def record_audio(filename=AUDIO_FILE, duration=5, samplerate=44100):
    update_status("LISTENING", "ACTIVE")
    print("🎤 Listening...")
    try:
        recording = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype="int16")
        sd.wait()
    except Exception as e:
        print("Microphone error:", e)
        return False
    try:
        with wave.open(filename, "wb") as file:
            file.setnchannels(1)
            file.setsampwidth(2)
            file.setframerate(samplerate)
            file.writeframes(recording.tobytes())
        return True
    except Exception as e:
        print("Audio file error:", e)
        return False


def listen():
    if not record_audio():
        return ""
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(AUDIO_FILE) as source:
            audio = recognizer.record(source)
        command = recognizer.recognize_google(audio).lower().strip()
        print("You:", command)
        update_status("COMMAND RECEIVED", "READY", command)
        return command
    except sr.UnknownValueError:
        print("Didn't understand.")
        update_status("STANDBY", "READY")
        return ""
    except sr.RequestError as e:
        print("Speech recognition error:", e)
        return ""
    except Exception as e:
        print("Voice error:", e)
        return ""


def normalize_command(command):
    command = command.lower().strip()
    command = re.sub(r"[^a-z0-9' ]+", " ", command)
    return re.sub(r"\s+", " ", command).strip()


def is_jarvis_sleep_command(command):
    return any(p in command for p in ("go to sleep", "go sleep", "jarvis sleep", "go offline", "shut yourself down"))


def is_windows_shutdown_command(command):
    return any(p in command for p in ("shut down the computer", "shutdown the computer", "power off the computer", "turn off the computer", "turn my computer off", "turn pc off"))


def shutdown_windows():
    speak("Shutting down the computer. Goodbye, Kevin.")
    print("Windows will shut down in 5 seconds.")
    try:
        subprocess.run(["shutdown", "/s", "/t", "5"])
    except Exception as e:
        print("Windows shutdown error:", e)


def sleep_jarvis():
    speak("Going to sleep. Jarvis is offline.")
    update_status("OFFLINE", "SLEEPING", "go to sleep")
    hide_hud()
    print("Jarvis is shutting down. Windows will stay on.")
    raise SystemExit(0)


def handle_command(command):
    command = normalize_command(command)
    if is_jarvis_sleep_command(command):
        sleep_jarvis()
    elif is_windows_shutdown_command(command):
        shutdown_windows()
    elif "what time is it" in command or "what's the time" in command or "current time" in command or command == "time" or "clock" in command:
        speak(f"The current time is {datetime.datetime.now().strftime('%I:%M %p')}.")
    elif "show hud" in command or "display hud" in command or "open hud" in command or "start hud" in command:
        speak("Displaying HUD.")
        show_hud()
    elif "hide hud" in command or "close hud" in command or "remove hud" in command or "turn off hud" in command or "get rid of hud" in command:
        speak("Hiding HUD.")
        hide_hud()
    elif "discord" in command or "open discord" in command or "launch discord" in command:
        speak("Opening Discord.")
        open_discord()
    elif "screenshot" in command or "take a screenshot" in command:
        speak("Taking screenshot.")
        result = take_screenshot()
        print("Screenshot:", result.get("file", "unknown"))
    elif "lock pc" in command or "lock computer" in command:
        speak("Locking computer.")
        lock_pc()
    elif (("back" in command and "black" in command) or "back in black" in command):
        speak("Playing Back in Black.")
        webbrowser.open("https://open.spotify.com/search/AC%20DC%20Back%20in%20Black")
    else:
        speak("I did not understand that command.")


def start_voice():
    hour = datetime.datetime.now().hour
    if hour < 12:
        greeting = "Good morning, Kevin. Jarvis is online and ready."
    elif hour < 18:
        greeting = "Good afternoon, Kevin. Jarvis is online and ready."
    else:
        greeting = "Good evening, Kevin. Jarvis is online and ready."
    speak(greeting)
    while True:
        command = normalize_command(listen())
        if not command:
            continue
        if is_jarvis_sleep_command(command):
            sleep_jarvis()
        if is_windows_shutdown_command(command):
            shutdown_windows()
            break
        if "jarvis wake up" in command or "jarvis wakeup" in command or command == "wake up jarvis":
            update_status("WAKE WORD DETECTED", "ACTIVE", command)
            speak("Online. What do you need?")
            command = normalize_command(listen())
            if command:
                handle_command(command)


if __name__ == "__main__":
    start_voice()
