

import cv2
import requests
import time
import base64
import base64
from flask import Flask, request, jsonify
import socket
from google.cloud import speech_v1p1beta1
from google.cloud.speech_v1p1beta1 import types
import re
import io
import openai
from openai import OpenAI

#
import pyglet
cloud_api_key = 'backend\credentials.json'  

global_pi_ip="http://192.168.50.103:5000"

direct_legal_commands=["maps","Maps","read","analyze","call","Call","find","Find","Read","analyse","Analyse","Analyze"]

#----------> uncomment while using

# global_location = {
#     'lat':None,
#     'lon':None
# }


user_needs=None

state = False

global_location={
    'lat':22.96317188502606,
    'lon':76.0449281707406
}

user_location={'latitude':25.234,'longitude':34.454}




app = Flask(__name__)


# Function to encode the image
def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')


def image_to_ai(image_path,command):
    # print(command)
    # Getting the base64 string
    base64_image = encode_image(image_path)

    headers = {
      "Content-Type": "application/json",
      "Authorization": f"Bearer {api_key}"
    }

    payload = {
      "model": "gpt-4-vision-preview",
      "messages": [
        {
          "role": "user",
          "content": [
            {
              "type": "text",
              "text": command
            },
            {
              "type": "image_url",
              "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image}"
              }
            }
          ]
        }
      ],
      "max_tokens": 300
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    # print("response:     "+response)
    txt= str(response.json().get("choices")[0].get("message").get("content"))
    print(txt)
    return str(txt)


def send_audio_to_server():
    url = f'{global_pi_ip}/speak_now'
    file_path = "backend\output.mp3" 
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
    with open("backend\output.mp3", "wb") as out:
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
    headers = {
    'Content-Type': 'application/json',
    'Text': text
    }
    requests.get("http://192.168.50.103:5000/speak_better", headers=headers)
    return

def get_ip():
    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)
    print("Server ip : ",ip)
    return ip



def normalize_speech(input_text):
    cleaned_text = re.sub(r'[^a-zA-Z0-9\s]', '', input_text)
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
    return cleaned_text


def extract_frame():
    speak("Capturing Image")
    stream_url = 'http://192.168.50.103:5000/stream'
    capture = cv2.VideoCapture(stream_url) # For capturing video using webcam
    success,image=capture.read()
    if success:
        cv2.imwrite('captured_frame.jpg', image)
        key= cv2.waitKey(1)
        capture.release()
        cv2.destroyAllWindows()
        return
    else:
        print("Error encountered!!")
        return

def pi_ocr():
    extract_frame()
    speak("Image captured")
    speak("Processing your request")
    text=image_to_ai("captured_frame.jpg","Only tell me what's written in the image in a single paragraph no special characters not even . or ,.")
    # print(type(text))
    new_text=normalize_speech(text)
    speak(new_text)
    return new_text

def get_stream_vol():
    requests.get('http://192.168.50.103:5000/start_camera')
    return

def transcribe_audio2(audio_file_path):
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

    return (complete_transcript.strip()) 


def retrieve_call(com):
    print(com)
    com_list = list(com.split(" "))
    print(com_list)
    for commands in direct_legal_commands:
        if com_list[0] == commands and (commands=="read" or commands=="Read"):
            print(commands)
            speak("Read command initiated")
            text=pi_ocr()
            return text
 

# def find_object(desc):
#     extract_frame()
#     sentence=desc+" in the following image and direct me or tell me how do i find that object as the following image is taken from my POV. Under 20 words"
#     output=image_to_ai("captured_frame.jpg",str(sentence))
#     print(output)
#     speak(str(output))



def login_using_qr():
    
    stream_url = f"{global_pi_ip}/stream" # To stream using raspberry pi Only!

    capture = cv2.VideoCapture(stream_url) # For capturing video using webcam

    while True:
        success,image=capture.read()
        if success:
            try:
                cv2.imshow("Capture",image)
                detect = cv2.QRCodeDetector()
                value, points, straight_qrcode = detect.detectAndDecode(image)
                key= cv2.waitKey(1)
                if(value):
                    cv2.destroyAllWindows()
                    speak("Login Successful")
                    return value
                else:
                    continue
            except:
                cv2.destroyAllWindows()
                speak("Login Failed")
                return "Failed"
        else:
            cv2.destroyAllWindows()
            speak("Login Failed")
            return "Failed"
        
def request_login():
    login_ip = login_using_qr()
    print(login_ip)
    url = f"http://{login_ip}:8080/login"
    try:
        server_ip=get_ip()
        response = requests.post(url,data=server_ip)
        if response.status_code == 200:
            print("Request successful")
        else:
            print(f"Request failed with status code {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")


##test


###############################################################
###############################################################

request_login()
# extract_frame()
# print(pi_ocr())

###############################################################
###############################################################


# print(get_ip())

# pi_ocr()


@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return 'No file part'
    file = request.files['file']
    if file.filename == '':
        return 'No selected file'
    file.save('backend/uploaded_audio.wav')  # Save the received audio file
    return 'File uploaded successfully'



@app.route('/user_info', methods=['GET'])
def get_user_info():
    try:
        return jsonify({'text': "Hello there!"}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    
@app.route('/set_state')
def set_state():
    # global state
    # state=True
    print("Hello")
    return "Success",200

@app.route('/user_location', methods=['POST'])
def receive_user_location():
    try:
        data = request.form 
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        if latitude is not None and longitude is not None:
            global global_location
            global_location={
                'lat':float(latitude),
                'lon':float(longitude)
            }
            print(f"Received user location: Latitude={latitude}, Longitude={longitude}")
            return jsonify({'message': 'User location received'}), 200
        else:
            return jsonify({'error': 'Latitude or longitude missing in the request'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_text', methods=['POST'])
def get_text():
    print("get text called")
    try:
        text = request.form['text']
        
        if isinstance(text, tuple):
            txt="Failed"
        elif isinstance(text, str):
            txt=text
        print("Received text:", txt)
        output=retrieve_call(txt)
        return str(output), 200
    except Exception as e:
        print("An error occurred:", e)
        return "Error at get_text"


@app.route('/get_audio_const', methods=['POST'])
def get_audio_const():
    print("Called")
    try:
        if 'audio' not in request.files:
            return 'No audio file provided', 400

        audio_file = request.files['audio']

        audio_file.save('backend/audio_const.wav')

        # transcribe_audio('audio_const.wav')
        

        return 'WAV file received and saved successfully',200

    except Exception as e:
        return f'Error: {str(e)}', 500
@app.route('/get_location', methods=['GET'])
def get_user_location():
    return jsonify({'latitude': user_location['latitude'], 'longitude': user_location['longitude']}), 200
@app.route('/directions', methods=['POST'])
def receive_data():
    try:
        data = request.json
        print("Vol User backend Received data:", data)
        return "Data received successfully", 200
        
    except Exception as e:
        print("Error processing data:", e)
        return jsonify({"message": "Error processing data"}), 500
@app.route('/get_state', methods=['POST'])
def get_state():
    try:
        data = request.json
        print("state:", data)
        return "Data received successfully", 200
        
    except Exception as e:
        print("Error processing data:", e)
        return jsonify({"message": "Error processing data"}), 500



if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)