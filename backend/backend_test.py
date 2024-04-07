from math import radians, sin, cos, sqrt, atan2
import cv2
import requests
import multiprocessing
import time
from flask import Flask, request, jsonify
import socket
from google.cloud import speech_v1p1beta1
from google.cloud.speech_v1p1beta1 import types
from google.cloud import vision
from google.cloud import texttospeech
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from firebase_admin import db
import threading
import re
import io
import speech_recognition as sr
import pyttsx3

#
import pyglet

cloud_api_key = 'credentials.json'  

global_pi_ip="http://192.168.29.193:8080"

direct_legal_commands=["read","analyze","call","find"]

#----------> uncomment while using

# global_location = {
#     'lat':None,
#     'lon':None
# }

global_location={
    'lat':22.962601,
    'lon':76.046091
}

cred = credentials.Certificate('firebase_credentials.json')

firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://avtemp-660d8-default-rtdb.asia-southeast1.firebasedatabase.app/'
})

global_legal_distance = 1.5


app = Flask(__name__)

def record_and_save():
    filename="audio_capture.wav"
    # Initialize the recognizer
    recognizer = sr.Recognizer()

    # Initialize the text-to-speech engine
    engine = pyttsx3.init()

    # Capture audio from the microphone
    with sr.Microphone() as source:
        print("Listening... ")
        recognizer.adjust_for_ambient_noise(source)  
        audio = recognizer.listen(source)

        with open(filename, "wb") as f:
            f.write(audio.get_wav_data())

        print(f"Audio saved as {filename}")

def send_text_to_server():
    url = f'{global_pi_ip}/speak_now'
    file_path = "output.mp3" 
    with open(file_path, "rb") as file:
        files = {'audio': file}
        requests.post(url, files=files)
    return

def synthesize_text(text):
    """Synthesizes speech from the input string of text."""
    
    
    from google.cloud import texttospeech

    client = texttospeech.TextToSpeechClient()

    input_text = texttospeech.SynthesisInput(text=text)

    # Note: the voice can also be specified by name.
    # Names of voices can be retrieved with client.list_voices().
    voice = texttospeech.VoiceSelectionParams(
        language_code="hi-IN",
        name="hi-IN-Neural2-A",
        # ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding="LINEAR16",
        pitch= 0,
        speaking_rate= 1.15
    )

    response = client.synthesize_speech(
        request={"input": input_text, "voice": voice, "audio_config": audio_config}
    )

    # The response's audio_content is binary.
    with open("output.mp3", "wb") as out:
        out.write(response.audio_content)
        print('Audio content written to file "output.mp3"')
    # player = pyglet.media.Player()
    # sound = pyglet.media.load("output.mp3", streaming=False)
    # player.queue(sound)
    # player.play()
    # def on_eos():
    #     pyglet.app.exit()

    # player.push_handlers(on_eos)
    # pyglet.app.run()
    # return 

def speak(text):
    synthesize_text(text)
    send_audio_to_server()
    return


def normalize_speech(input_text):
    cleaned_text = re.sub(r'[^a-zA-Z0-9\s]', '', input_text)
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
    return cleaned_text
    

def transcribe_audio(audio_file_path):
    global cloud_api_key
    api_key=cloud_api_key
    client = speech_v1p1beta1.SpeechClient.from_service_account_file(api_key)

    with io.open(audio_file_path, 'rb') as audio_file:
        content = audio_file.read()

    audio = types.RecognitionAudio(content=content)
    config = types.RecognitionConfig(
        encoding=speech_v1p1beta1.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=44100,
        language_code='en-US',
    )

    response = client.recognize(config=config, audio=audio)

    complete_transcript = ''

    for result in response.results:
        complete_transcript += result.alternatives[0].transcript + ' '

    retrieve_call(complete_transcript.strip())  



@app.route('/get_audio', methods=['POST'])
def get_audio():
    try:
        if 'audio' not in request.files:
            return 'No audio file provided', 400

        audio_file = request.files['audio']

        audio_file.save('audio_received.wav')

        transcribe_audio('audio_received.wav')
        

        return 'WAV file received and saved successfully'

    except Exception as e:
        return f'Error: {str(e)}', 500

@app.route('/directions', methods=['POST'])
def receive_data():
    try:
        data = request.json
        print("Vol User backend Received data:", data)
        return "Data received successfully", 200
        
    except Exception as e:
        print("Error processing data:", e)
        return jsonify({"message": "Error processing data"}), 500




if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
