import speech_recognition as sr
import pyttsx3
import sounddevice as sd
import wave

from actions import (
    open_calculator,
    take_screenshot,
    lock_pc
)


engine = pyttsx3.init()


def speak(text):
    print("Jarvis:", text)
    engine.say(text)
    engine.runAndWait()


def record_audio(filename="voice.wav", duration=5, samplerate=44100):

    print("🎤 Listening...")

    recording = sd.rec(
        int(duration * samplerate),
        samplerate=samplerate,
        channels=1,
        dtype="int16"
    )

    sd.wait()

    with wave.open(filename, "wb") as file:
        file.setnchannels(1)
        file.setsampwidth(2)
        file.setframerate(samplerate)
        file.writeframes(recording.tobytes())


def listen():

    filename = "voice.wav"

    record_audio(filename)

    recognizer = sr.Recognizer()

    with sr.AudioFile(filename) as source:
        audio = recognizer.record(source)

    try:
        command = recognizer.recognize_google(audio)

        print("You:", command)

        return command.lower()

    except:
        return ""


def handle_command(command):

    if "calculator" in command:
        speak("Opening calculator.")
        open_calculator()


    elif "screenshot" in command:
        speak("Taking screenshot.")
        take_screenshot()


    elif "lock computer" in command or "lock pc" in command:
        speak("Locking computer.")
        lock_pc()


    else:
        speak("I did not understand that command.")



def start_voice():

    speak("Jarvis is online.")

    while True:

        command = listen()


        if "jarvis wake up" in command:

            speak("Online. What do you need?")

            command = listen()

            handle_command(command)



if __name__ == "__main__":
    start_voice()
