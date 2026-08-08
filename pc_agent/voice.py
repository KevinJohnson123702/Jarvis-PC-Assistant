```python
import pyttsx3
import sounddevice as sd
import speech_recognition as sr
import wave
import webbrowser
import datetime
import json
import subprocess
import os
import sys

from actions import (
    open_calculator,
    take_screenshot,
    lock_pc
)


# -------------------------
# FILE PATHS
# -------------------------

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

STATUS_FILE = os.path.join(
    BASE_DIR,
    "status.json"
)


# -------------------------
# HUD STATUS
# -------------------------

def update_status(status, voice="READY", command="None"):

    data = {
        "status": status,
        "voice": voice,
        "last_command": command
    }

    try:
        with open(
            STATUS_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                data,
                file,
                indent=4
            )

    except Exception as e:

        print(
            "Status error:",
            e
        )


# -------------------------
# HUD CONTROL
# -------------------------

hud_process = None


def show_hud():

    global hud_process

    if hud_process is not None:
        return

    hud_path = os.path.join(
        BASE_DIR,
        "hud.py"
    )

    try:

        hud_process = subprocess.Popen(
            [
                sys.executable,
                hud_path
            ],
            cwd=BASE_DIR
        )

        print(
            "HUD started."
        )

    except Exception as e:

        print(
            "HUD error:",
            e
        )

        hud_process = None



def hide_hud():

    global hud_process

    if hud_process is not None:

        try:

            hud_process.terminate()

        except:

            pass

        hud_process = None

        print(
            "HUD hidden."
        )


# -------------------------
# VOICE ENGINE
# -------------------------

engine = pyttsx3.init()

voices = engine.getProperty(
    "voices"
)


if len(voices) > 0:

    engine.setProperty(
        "voice",
        voices[0].id
    )


engine.setProperty(
    "rate",
    165
)

engine.setProperty(
    "volume",
    1.0
)


def speak(text):

    update_status(
        "SPEAKING",
        "ACTIVE",
        text
    )

    print(
        "Jarvis:",
        text
    )

    engine.say(
        text
    )

    engine.runAndWait()

    update_status(
        "STANDBY",
        "READY",
        text
    )


# -------------------------
# MICROPHONE
# -------------------------

def record_audio(
    filename="voice.wav",
    duration=5,
    samplerate=44100
):

    update_status(
        "LISTENING",
        "ACTIVE"
    )

    print(
        "🎤 Listening..."
    )

    try:

        recording = sd.rec(
            int(
                duration * samplerate
            ),
            samplerate=samplerate,
            channels=1,
            dtype="int16"
        )

        sd.wait()

    except Exception as e:

        print(
            "Microphone error:",
            e
        )

        return False


    try:

        with wave.open(
            filename,
            "wb"
        ) as file:

            file.setnchannels(
                1
            )

            file.setsampwidth(
                2
            )

            file.setframerate(
                samplerate
            )

            file.writeframes(
                recording.tobytes()
            )

        return True

    except Exception as e:

        print(
            "Audio file error:",
            e
        )

        return False


# -------------------------
# SPEECH RECOGNITION
# -------------------------

def listen():

    filename = os.path.join(
        BASE_DIR,
        "voice.wav"
    )

    success = record_audio(
        filename
    )

    if not success:

        return ""


    recognizer = sr.Recognizer()


    try:

        with sr.AudioFile(
            filename
        ) as source:

            audio = recognizer.record(
                source
            )


        command = recognizer.recognize_google(
            audio
        )

        command = command.lower().strip()


        print(
            "You:",
            command
        )


        update_status(
            "COMMAND RECEIVED",
            "READY",
            command
        )


        return command


    except sr.UnknownValueError:

        print(
            "❌ Didn't understand"
        )

        update_status(
            "STANDBY",
            "READY"
        )

        return ""


    except sr.RequestError as e:

        print(
            "Speech recognition error:",
            e
        )

        update_status(
            "ERROR",
            "READY"
        )

        return ""


    except Exception as e:

        print(
            "Voice error:",
            e
        )

        update_status(
            "ERROR",
            "READY"
        )

        return ""


# -------------------------
# SHUTDOWN
# -------------------------

def shutdown_pc():

    speak(
        "Going to sleep. Goodbye, Kevin."
    )

    print(
        "Computer shutting down in 5 seconds..."
    )

    subprocess.run(
        [
            "shutdown",
            "/s",
            "/t",
            "5"
        ]
    )


# -------------------------
# COMMANDS
# -------------------------

def handle_command(command):


    # CALCULATOR
    if "calculator" in command:

        speak(
            "Opening calculator."
        )

        open_calculator()


    # SCREENSHOT
    elif "screenshot" in command:

        speak(
            "Taking screenshot."
        )

        take_screenshot()


    # LOCK PC
    elif (
        "lock pc" in command
        or
        "lock computer" in command
    ):

        speak(
            "Locking computer."
        )

        lock_pc()


    # SPOTIFY
    elif (
        "back" in command
        and
        "black" in command
    ):

        speak(
            "Playing Back in Black."
        )

        webbrowser.open(
            "https://open.spotify.com/search/AC%20DC%20Back%20in%20Black"
        )


    # TIME
    elif (
        "time" in command
        or
        "clock" in command
    ):

        current_time = datetime.datetime.now().strftime(
            "%I:%M %p"
        )

        speak(
            f"The current time is {current_time}."
        )


    # SHOW HUD
    elif (
        "show hud" in command
        or
        "display hud" in command
    ):

        speak(
            "Displaying HUD."
        )

        show_hud()


    # HIDE HUD
    elif (
        "hide hud" in command
        or
        "remove hud" in command
    ):

        speak(
            "Hiding HUD."
        )

        hide_hud()


    # SHUTDOWN
    elif (
        "go to sleep" in command
        or
        "go sleep" in command
    ):

        shutdown_pc()


    # UNKNOWN COMMAND
    else:

        speak(
            "I did not understand that command."
        )


# -------------------------
# START JARVIS
# -------------------------

def start_voice():

    hour = datetime.datetime.now().hour


    if hour < 12:

        greeting = (
            "Good morning, Kevin. "
            "Jarvis is online and ready."
        )

    elif hour < 18:

        greeting = (
            "Good afternoon, Kevin. "
            "Jarvis is online and ready."
        )

    else:

        greeting = (
            "Good evening, Kevin. "
            "Jarvis is online and ready."
        )


    speak(
        greeting
    )


    while True:

        command = listen()


        # WAKE WORD
        if (
            "jarvis wake up" in command
            or
            "jarvis wakeup" in command
        ):

            update_status(
                "WAKE WORD DETECTED",
                "ACTIVE",
                command
            )


            speak(
                "Online. What do you need?"
            )


            command = listen()


            if command:

                handle_command(
                    command
                )


# -------------------------
# RUN
# -------------------------

if __name__ == "__main__":

    start_voice()
```
