import speech_recognition as sr
import pyttsx3
import sounddevice as sd
import wave
import webbrowser
import datetime
import json
import subprocess
import os

from actions import (
    open_calculator,
    take_screenshot,
    lock_pc
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

    with open(
        "status.json",
        "w"
    ) as file:
        json.dump(
            data,
            file,
            indent=4
        )


# -------------------------
# HUD CONTROL
# -------------------------

hud_process = None


def show_hud():

    global hud_process

    if hud_process is None:

        hud_path = os.path.join(
            os.path.dirname(__file__),
            "hud.py"
        )

        hud_process = subprocess.Popen(
            [
                "python",
                hud_path
            ]
        )



def hide_hud():

    global hud_process

    if hud_process is not None:

        hud_process.terminate()

        hud_process = None



# -------------------------
# VOICE SETUP
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
# LISTENING
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


    recording = sd.rec(
        int(duration * samplerate),
        samplerate=samplerate,
        channels=1,
        dtype="int16"
    )


    sd.wait()


    with wave.open(
        filename,
        "wb"
    ) as file:

        file.setnchannels(1)

        file.setsampwidth(2)

        file.setframerate(samplerate)

        file.writeframes(
            recording.tobytes()
        )



def listen():

    filename = "voice.wav"


    record_audio(
        filename
    )


    recognizer = sr.Recognizer()


    with sr.AudioFile(
        filename
    ) as source:

        audio = recognizer.record(
            source
        )


    try:

        command = recognizer.recognize_google(
            audio
        )


        command = command.lower()


        print(
            "You:",
            command
        )


        return command



    except:

        return ""



# -------------------------
# COMMANDS
# -------------------------

def handle_command(command):


    if "calculator" in command:

        speak(
            "Opening calculator."
        )

        open_calculator()



    elif "screenshot" in command:

        speak(
            "Taking screenshot."
        )

        take_screenshot()



    elif (
        "lock pc" in command
        or
        "lock computer" in command
    ):

        speak(
            "Locking computer."
        )

        lock_pc()



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



    elif "show hud" in command:

        speak(
            "Displaying HUD."
        )

        show_hud()



    elif "hide hud" in command:

        speak(
            "Hiding HUD."
        )

        hide_hud()



    else:

        speak(
            "I did not understand that command."
        )



# -------------------------
# START
# -------------------------

def start_voice():

    hour = datetime.datetime.now().hour


    if hour < 12:

        speak(
            "Good morning, Kevin. Jarvis is online and ready."
        )

    elif hour < 18:

        speak(
            "Good afternoon, Kevin. Jarvis is online and ready."
        )

    else:

        speak(
            "Good evening, Kevin. Jarvis is online and ready."
        )



    while True:

        command = listen()


        if "jarvis wake up" in command:


            update_status(
                "WAKE WORD DETECTED",
                "ACTIVE",
                command
            )


            speak(
                "Online. What do you need?"
            )


            command = listen()


            handle_command(
                command
            )



if __name__ == "__main__":

    start_voice()
