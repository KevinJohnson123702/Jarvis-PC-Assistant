import speech_recognition as sr
import pyttsx3


engine = pyttsx3.init()


def speak(text):
    engine.say(text)
    engine.runAndWait()


def listen():

    recognizer = sr.Recognizer()

    with sr.Microphone() as source:

        print("🎤 Listening...")

        recognizer.adjust_for_ambient_noise(source)

        audio = recognizer.listen(source)


    try:

        command = recognizer.recognize_google(audio)

        print("You said:", command)

        return command.lower()


    except:

        return ""


def start_voice():

    speak("Jarvis is online.")

    while True:

        command = listen()


        if "jarvis wake up" in command:

            speak("Online. What do you need?")


if __name__ == "__main__":
    start_voice()
