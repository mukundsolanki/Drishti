from flask import Flask, render_template, Response,request,jsonify
import picamera
import io
import os
import time
import speech_recognition as sr
import pyttsx3
import requests
import threading
import RPi.GPIO as GPIO
import websockets
import asyncio
import cv2, base64
from io import BytesIO
from picamera import PiCamera
import pyglet
import http.client
from pathlib import Path
from openai import OpenAI
from gtts import gTTS 
import warnings
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
from scipy.io.wavfile import write
warnings.filterwarnings("ignore", category=DeprecationWarning)

call=0
call2=0

BUTTON2 = 17

GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON2, GPIO.IN)

check_stream_web=False

back_end_ip="192.168.50.246"

check_navigation=False
nav_state=True

def load_env(filename):
    with open(filename) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                key, value = line.split('=', 1)
                os.environ[key] = value

load_env('.env')

#os.environ.get('api_key')

api_key=os.environ.get('api_key')
print(api_key)

# Function to encode the image
def convert_text_to_speech(text, output_location):
    language = 'en'
    myobj = gTTS(text=text, lang=language, slow=False) 
    myobj.save(output_location) 
    os.system(f"mpg321 {output_location}")
    return

def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

async def transmit(websocket, path):
    print("Client Connected !")
    try:
        with PiCamera() as camera:
            camera.resolution = (640, 480)  # Adjust resolution as needed
            camera.start_preview()
            await asyncio.sleep(2)  # Allow camera to warm up
            global check_stream_web
            stream = BytesIO()
            for _ in camera.capture_continuous(stream, format='jpeg'):
                stream.seek(0)
                data = base64.b64encode(stream.read()).decode('utf-8')
                await websocket.send(data)
                stream.seek(0)
                stream.truncate()

                # Exit the loop if the client closes the connection
                if websocket.closed:
                    break
                if not check_stream_web:
                    break

    except websockets.exceptions.ConnectionClosedError:
        print("Client Disconnected !")

def start_websockets_server():
    asyncio.set_event_loop(asyncio.new_event_loop())  # Create a new event loop
    loop = asyncio.get_event_loop()
    start_server = websockets.serve(transmit, port=3050)
    loop.run_until_complete(start_server)
    loop.run_forever()


def generate_frames():
    with picamera.PiCamera() as camera:
        camera.resolution = (640, 480)
        camera.framerate = 24
        # Give the camera some warm-up time
        time.sleep(2)
        stream = io.BytesIO()
        for _ in camera.capture_continuous(stream, format='jpeg', use_video_port=True):
            stream.seek(0)
            yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + stream.read() + b'\r\n'
            stream.seek(0)
            stream.truncate()
            time.sleep(0.1)  # Adjust sleep duration as needed
            

    
def send_text_to_server(text, server_url):
    try:
        print(type(text))
        data = {'text': str(text)}
        response = requests.post(server_url, data=data)
        if response.status_code == 200:
            print("Text successfully sent to the server.")
            return "Success",200
        else:
            print("Failed to send text. Server responded with status code:", response.status_code)
            return "Success"
    except Exception as e:
        print("An error occurred:", e)
        return "Failed"

def convert_speech_to_text(audio_file_path,translate='en'):
    print("Speech Conversion Started!")
    try:
        SECRET_KEY = "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"
        client = OpenAI(api_key=SECRET_KEY)
        audio_file= open(audio_file_path, "rb")
        transcript = client.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_file,
            language=translate
        )
        print(transcript.text)
        return str(transcript.text)
    except:
        return "Failed",500

def record_and_save():
    filename = "audio_capture.wav"
    freq=44100
    duration=5
    alpha=2
    convert_text_to_speech("Listening","audio_better.mp3")
    time.sleep(0.5)
    recording = sd.rec(int(duration * freq), samplerate=freq, channels=2)
    
    # Record audio for the given number of seconds
    sd.wait()
    
    # Convert the recording to a single channel and float data type
    recording_mono = np.mean(recording, axis=1, dtype=np.float32)
    
    # Define a noise estimate (can be obtained from a silent part of the recording)
    noise_estimate = np.mean(np.abs(recording_mono))
    
    # Apply spectral subtraction for noise reduction
    filtered_recording = recording_mono - alpha * noise_estimate
    
    # Scale the filtered recording to the range [-1, 1]
    filtered_recording /= np.max(np.abs(filtered_recording))
    
    # Convert the NumPy array to audio file
    write(filename, freq, np.array(filtered_recording * 32767, dtype=np.int16))

        
def record_and_save_():
    filename = "audio_capture.wav"
    # Initialize the recognizer
    recognizer = sr.Recognizer()

    # Initialize the text-to-speech engine
    engine = pyttsx3.init()

    # Capture audio from the microphone
    with sr.Microphone() as source:
        convert_text_to_speech("Listening","audio_better.mp3")
        print("Listening... ")
        recognizer.adjust_for_ambient_noise(source)  
        try:
            audio = recognizer.listen(source, timeout=5)
        except sr.WaitTimeoutError:
            print("Timeout. No speech detected.")
            return

        with open(filename, "wb") as f:
            f.write(audio.get_wav_data())

        print(f"Audio saved as {filename}")
        convert_text_to_speech("audio saved","audio_better.mp3")
        return


def set_button():
    while True:
        global call2 #starting mei zero hai
        state = GPIO.input(BUTTON2) #state click pe 0 hai aur default 1
        if(not state):
            if call2==2:
                requests.get("http://192.168.50.246:8080/get_state",json={"state":state})
                time.sleep(1)
                call2=0
                continue
            call2=call2+1
        
        
            
        
def on_button():
    while True:
        global check_stream_web
        global call #initially 0, haan yeh bhi bhai
        global back_end_ip
        global nav_state
        global back_end_ip
        # print(nav_state)
        state = GPIO.input(BUTTON2) #initially it should be 0
        # if (not state and check_stream_web==True ):
        #     check_stream_web=False
        #     call=call+1
        #     time.sleep(1) #changed to 1 from 3 Test
        #     continue
        if(nav_state):
            print("Nav True")
            if(not state and check_stream_web==False and call<2):
                call=call+1
                continue
            if (not state and check_stream_web==False and call==2):
                #print(state)
                call=0
                convert_text_to_speech("Button pressed","audio_better.mp3")
                record_and_save()
                text=convert_speech_to_text("audio_capture.wav")

                # print("header sent type ",type(text))
                # print(type(text))
                if isinstance(text, tuple):
                    txt="Failed"
                elif isinstance(text, str):
                    txt=text
                send_text_to_server(str(txt),f'http://{back_end_ip}:8080/get_text')
                time.sleep(1)
                continue
        else:
            print("Nav False")
            if(not state and check_stream_web==False and call<2):
                call=call+1
                continue
            if (not state and check_stream_web==False and call==2):
                #print(state)
                call=0
                convert_text_to_speech("nav button pressed","audio_better.mp3")
                res=requests.get('http://192.168.50.246:8080/set_state')
                print(res)
                print("Code passed res")
                time.sleep(1)
                continue
        
        # requests.get("http://192.168.29.28:8080/get_state",json={"state":state})
        # time.sleep(1)
        time.sleep(2)


app = Flask(__name__)


try_button = threading.Thread(target=on_button)
try_button.daemon = True  
try_button.start()

set_button = threading.Thread(target=set_button)
set_button.daemon = True  
#set_button.start()


@app.route('/consume_audio')
def consume_route():
    try:
        record_and_save()
        text=convert_speech_to_text("audio_capture.wav")
        txt={
            "text":text
        }
        return jsonify(txt)
    except:
        return "Failed"
    
@app.route('/set_nav_state')
def nav_state_f():
    global nav_state
    nav_state=False
    print("New value of Nav state is set to "+str(nav_state))
    return "Success",200

@app.route('/set_nav_state_false')
def nav_state_false():
    global nav_state
    nav_state=True
    print("New value of Nav state is set to "+str(nav_state))
    return "Success",200
    
@app.route('/stream_button_state')
def stream_button_state():
    global check_navigation
    check_navigation=True
    return "Success",200

@app.route('/stream')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/volunteer_audio', methods=['POST'])
def volunteer_audio():
    if 'file' not in request.files:
        return 'No file part', 400
    
    file = request.files['file']
    if file.filename == '':
        return 'No selected file', 400

    if file:
        file.save('file.mp4')  # Provide the path where you want to save the file
        return 'File uploaded successfully', 200

@app.route('/start_camera')
def start_camera():
    global check_stream_web
    check_stream_web=True
    print("Started server on port:", 5000)
    threading.Thread(target=start_websockets_server).start()
    return "Camera streaming started!"

@app.route('/speak_better')
def speak_better():
    text_from_header = request.headers.get('Text', None)
    convert_text_to_speech(text_from_header,"audio_better.mp3")
    return "Success",200

@app.route('/speak_now',methods=['POST'])
def speak_now():
    if 'audio' not in request.files:
            return 'No audio file provided', 400
    audio_file = request.files['audio']
    audio_file.save('output.mp3')
    player = pyglet.media.Player()
    sound = pyglet.media.load("output.mp3", streaming=False)
    player.queue(sound)
    player.play()
    def on_eos():
        pyglet.app.exit()       
    player.push_handlers(on_eos)
    pyglet.app.run()
    return "Success",200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)



