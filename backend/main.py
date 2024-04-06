# $env:GOOGLE_APPLICATION_CREDENTIALS="./credentials.json"
# $env:GOOGLE_API_KEY="c32f73aeaa10b236a61dd9159df1b63ea17647af"

from math import radians, sin, cos, sqrt, atan2
import cv2
import requests
import multiprocessing
import time
import base64
import base64
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
import matplotlib.pyplot as plt
import threading
import numpy as np
import re
import io
from dotenv import load_dotenv
import os
import openai
from openai import OpenAI
import pyglet


#########################33

current_pos=[0,0]
angle=0

cloud_api_key = 'credentials.json'  

global_pi_ip="http://192.168.50.103:5000"

direct_legal_commands=["maps","Maps","read","analyze","call","Call","find","Find","Read","analyse","Analyse","Analyze"]

#----------> publish ke pehel uncomment kar dena, theek hai.

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

cred = credentials.Certificate('firebase_credentials.json')

firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://avtemp-660d8-default-rtdb.asia-southeast1.firebasedatabase.app/'
})

global_legal_distance = 1.5
nav_state=False

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
print("API Key:", api_key)

directions_in_list=[]
nav_it=0

app = Flask(__name__)


# Function to encode the image
def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')


def image_to_ai(image_path,command):
    print(command)
    # Getting the base64 string
    api_key=os.getenv('OPENAI_API_KEY')
    print(os.getenv('OPENAI_API_KEY'))
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
              "text": str(command)
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
    print(response)
    txt= str(response.json().get("choices")[0].get("message").get("content"))
    print(type(txt))
    return str(txt)


def send_audio_to_server():
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

def send_push_notification_request(ad):
    url = f'{ad}/push_notification'
    headers = {'Content-Type': 'application/json'}
    data = {'ipAddress': "192.168.50.103"}

    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            print('Push notification sent successfully')
        else:
            print(f'Failed to send push notification. Status code: {response.status_code}')

    except Exception as e:
        print(f'Error sending push notification: {e}')

def normalize_speech(input_text):
    cleaned_text = re.sub(r'[^a-zA-Z0-9\s]', '', input_text)
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
    return cleaned_text

def send_data_test():
    ref = db.reference('/')
    users_ref = ref.child('users')
    users_ref.set({})

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
    text=image_to_ai("captured_frame.jpg","Only tell me what's written in the image in a single paragraph no special characters not even . or ,. Under 50 words")
    time.sleep(2)
    print(text)
    print(type(text))
    new_text=normalize_speech(text)
    speak(str(new_text))
    return new_text

def check_coord(lat1, lon1, lat2, lon2):
    global global_legal_distance
    
    R = 6371.0

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c

    if distance < global_legal_distance:
        return True
    else:
        return False

def get_stream_vol():
    requests.get('http://192.168.50.103:5000/start_camera')
    return

# def call_volunteer():
#     print("Call Volunteer initiated!")
#     global global_location
#     if(global_location['lat']==None and global_location['lon']==None):
#         print("User location not accessible")
#         return False
#     else:
#         users_ref = db.reference('users/volunteer')
#         volunteer_data = users_ref.get()
#         for volunteer_id, volunteer_info in enumerate(volunteer_data):
#             if volunteer_info is not None:
#                 latitude = volunteer_info.get('location', {}).get('lat')
#                 longitude = volunteer_info.get('location', {}).get('lon')
#                 if latitude is not None and longitude is not None:
#                     print(f"Volunteer {volunteer_id+1} {check_coord(latitude,longitude,global_location['lat'],global_location['lon'])}")
#                     #print(f"Volunteer {volunteer_id + 1}: Latitude {latitude}, Longitude {longitude}")
#                     current_ip_vol = volunteer_info.get('current_ip', {})
#                     process1 = multiprocessing.Process(target=get_stream_vol)
#                     process1.start()
#                     send_push_notification_request(current_ip_vol)
                    
#                     print("Notification Sent!")
#                 else:
#                     print(f"Volunteer {volunteer_id + 1}: Location data not available")




def ai_normalized(prompt):
    client = OpenAI(
        api_key=os.getenv('OPENAI_API_KEY'),
    )

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": str(prompt+" sounds like which number, just provide me the number and nothing else, the number should be outputed in numeric form and if there is any issue recognizing the output should be 0. The output should be always just a number in numeric form. The number intended in range of 0 to 10 and if the prediction goes beyond 10 just return 0"),
            }
        ],
        model="gpt-3.5-turbo",
    )
    response = chat_completion.choices[0].message.content
    print(response)
    return response

def ai_normalized__(prompt):
    client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY'),
    )

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": str(prompt+" is similar to which number, only provide me the number in numeric form and if number is already in numeric form return as it is. if it is not similar, sounds similar to any number then return 0."),
            }
        ],
        model="gpt-3.5-turbo",
    )
    response = chat_completion.choices[0].message.content
    print(response)
    return response

def call_volunteer():
    # speak("Call Volunteer initiated!")
    print("Call Volunteer initiated!")
    global global_location
    # speak("Where do you want to go?")
    response=requests.get('http://192.168.50.103:5000/consume_audio')
    global user_needs
    user_needs = response.json().get("text")
    if global_location['lat'] is None and global_location['lon'] is None:
        print("User location not accessible")
        # speak("User location not accessible")
        return False
    else:
        users_ref = db.reference('users/volunteer')
        volunteer_data = users_ref.get()
        for volunteer_id, volunteer_info in enumerate(volunteer_data):
            if volunteer_info is not None:
                latitude = volunteer_info.get('location', {}).get('lat')
                longitude = volunteer_info.get('location', {}).get('lon')
                if latitude is not None and longitude is not None:
                    print(f"Volunteer {volunteer_id+1} {check_coord(latitude, longitude, global_location['lat'], global_location['lon'])}")
                    # speak("Volunteer selected nearby")
                    call_volunteer_test_thread = threading.Thread(target=get_stream_vol)
                    call_volunteer_test_thread.daemon = True  
                    call_volunteer_test_thread.start()
                    current_ip_vol = volunteer_info.get('current_ip', {})
                    print(current_ip_vol)
                    send_push_notification_request(current_ip_vol)
                    print("Notification Sent!")
                    # speak('Notification Sent!')
                    return
                else:
                    print(f"Volunteer {volunteer_id + 1}: Location data not available")
                    # speak('Volunteers unavailable')

def normalize_call(com_list):
    if com_list[1] == "volunteer":
        call_volunteer()
        return

def word_to_number(word):
    number_list = ["One", "one", "Two", "two", "Three", "three", "Four", "four", "Five", "five"]
    for index, nums in enumerate(number_list):
        if word.lower() == nums.lower():
            return index // 2 + 1
    return None 

def normalize_string_advance(input_string):
    # Remove special characters, convert capital letters to lowercase, and normalize spaces
    normalized_string = re.sub(r'[^a-zA-Z0-9\s,.]', '', input_string).lower().strip()
    # Normalize spaces
    normalized_string = re.sub(r'\s+', ' ', normalized_string)
    return normalized_string

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


def get_building_support(support):
    icn_spots = db.reference('users/ICN')
    icn_spots=icn_spots.get()
    for ele in icn_spots:
        icn_name=db.reference(f'users/ICN/{ele}')
        icn_name=icn_name.get()
        icn_n=icn_name.get("name")
        if icn_n==support:
            icn_name=db.reference(f'users/ICN/{ele}')
            icn_name=icn_name.get()
            return icn_name

def find_map_spots():
    global global_location
    name_list=[]
    icn_spots = db.reference('users/ICN')
    icn_spots=icn_spots.get()
    for ele in icn_spots:
        icn_spots_sub = db.reference(f'users/ICN/{ele}/location')
        icn_spots_sub = icn_spots_sub.get()
        result=check_coord(global_location.get("lat"),global_location.get("lon"),icn_spots_sub.get("latitude"),icn_spots_sub.get("longitude"))
        if result:
            icn_name=db.reference(f'users/ICN/{ele}')
            icn_name=icn_name.get()
            print(icn_name.get("name"))
            name_list.append(icn_name.get("name"))
    return name_list

def help_navigate(support):
    print(support.get("data"))
    name_list=[]
    ln=len(support.get("data"))+1
    for i in range(1,ln):
        data_gen=support.get("data")
        sub_data=(data_gen.get("data"+str(i)))
        if(sub_data.get("numeric")==0):
            name_list.append(sub_data.get("text"))
    unique_list=list(set(name_list))
    print(unique_list)
    print("There are ",len(unique_list)," number of checkpoints. Where would you like to go?")
    num=1
    for names in unique_list:
        print(num," , , ",names)
        num=num+1
    time.sleep(2)
    print("Which checkpoint should i navigate you to?")
    global global_pi_ip
    print("Hello 1")
    response=requests.get('http://192.168.50.103:5000/consume_audio')
    com=response.json().get("text")
    # com=transcribe_audio2("audio_const.wav")
    com_list = list(com.split(" "))
    com_ele=normalize_string_advance(com_list[0])
    com_ele_num = word_to_number(com_ele)
    print("Com list ",com_list)
    no_of_zero=0
    print("ln",ln)
    for i in range(1,ln):
        print("loop ",i)
        data_gen=support.get("data")
        sub_data=(data_gen.get("data"+str(i)))
        if(sub_data.get("numeric")==0):
            no_of_zero=no_of_zero+1
        if(com_ele_num==no_of_zero-1):
            # response=requests.get(f'{global_pi_ip}/stream_button_state')
            # print(response)
            # name_list.append(sub_data.get("text"))
            nm=1
            while(True):
                print(sub_data.get("numeric")," ",sub_data.get("text"))
                subd=support.get("data")
                combstr="data"+str(nm)
                enum=subd.get(combstr)
                enum_enum=enum.get("numeric")
                enum_txt=enum.get("text")
                print(enum_txt,enum_enum)
                nm=nm+1
                if(enum_enum==0):
                    break
            # while(!=0):
            #     print(data_gen.get("data"+str(nm)).get("text"))
            #     nm=nm+1
            return
                
            

def find_map():
    name_list=find_map_spots()
    print("There are ",len(name_list)," number of options. Which one do you want me to load?")
    num=1
    for names in name_list:
        print(num," , , ",names)
        num=num+1
    time.sleep(2)
    print("Which building do you want to enter?")
    global global_pi_ip
    response=requests.get(f'{global_pi_ip}/consume_audio')
    com=response.json().get("text")
    print(com)
    com2=normalize_string_advance(com)
    # com=transcribe_audio2("audio_const.wav")
    com_list = list(com2.split(" "))
    print("Com list ",com_list,"\n")
    print("Com ele ",com_list[0],"\n")
    # return
    if(com_list[0]=="First." or com_list[0]=="first." or com_list[0]=="First" or com_list[0]=="first" or com_list[0]=="Won" or com_list[0]=="won" or com_list[0]==1):
        building_confirmed=name_list[0]
        print(building_confirmed)
        result_obj=get_building_support(building_confirmed)
        print(result_obj)

    if(com_list[0]=="Two" or com_list[0]=="two" or com_list[0]=="to" or com_list[0]=="too" or com_list[0]==2):   
        building_confirmed=name_list[1]
        print(building_confirmed)
        result_obj=get_building_support(building_confirmed)
        print(result_obj)
        
    help_navigate(result_obj)

def scene(desc):
    extract_frame()
    speak("Analyzing the scene")
    output=image_to_ai("captured_frame.jpg",desc)
    print(output)
    speak(str(output))
    print(output) 
    return output

def analyze():

    extract_frame()
    speak("How can I help you?")
    response=requests.get('http://192.168.50.103:5000/consume_audio')
    # print("Response is ",response)
    if response:
        print(response.json())
        com=response.json().get("text")
        # com=requests.get("http://192.168.127.103:5000/consume_audio")
        # print(com)
        print(type(com))
        com_normal=normalize_speech(str(com))
        print(com_normal)
        output=image_to_ai("captured_frame.jpg",str(com_normal))
        print(output)
        speak(str(output))
        print(output) 
    else:
        print("No response")

def find_object(desc):
    extract_frame()
    sentence=desc+" in the following image and direct me or tell me how do i find that object as the following image is taken from my POV. Under 20 words"
    output=image_to_ai("captured_frame.jpg",str(sentence))
    print(output)
    speak(str(output))

def analyze_test_v1():

    # extract_frame()
    # speak("How can I help you?")
    # response=requests.get('http://192.168.127.103:5000/consume_audio')
    # print("Response is ",response)
    if True:
        # print(response.json())
        # com=response.json().get("text")
        com="Describe me the following image and every detail about it in detail."
        # com=requests.get("http://192.168.127.103:5000/consume_audio")
        # print(com)
        # print(type(com))
        # com_normal=normalize_speech(str(com))
        com_normal=com
        # print(com_normal)
        output=image_to_ai("test.jpg",str(com_normal))
        print(output)
        # speak(str(output))
        # print(output) 

def nav_speak(cat,desc,num):
    #reception data3 1
    cord_data = db.reference('users/maps/'+str(desc)+'/map')
    cord_data_san=cord_data.get()
    count=0
    for items in cord_data_san:
        try:
            print(items)
            if(items['checkpoint']):
                count=count+1
            if(items['checkpoint']==cat):
                break
        except:
            continue
    count2=0
    directions=[]
    for items in cord_data_san:
        try:
            if(count2==count-1):
                directions.append(items)
                try:
                    if(items['checkpoint']==cat):
                        return directions
                except:
                    continue
            if(items['checkpoint']):
                count2=count2+1
                    
        except:
            continue

def pick_subcat(data,desc):
    ok=2
    available_checkpoints=[]
    for item in data:
        try:
            if item['checkpoint']:
                if(ok!=0):
                    ok=ok-1
                    continue
                available_checkpoints.append(item['checkpoint'])
            else:
                continue
        except:
            continue
    
    i_temp=1
    speak("Please choose a checkpoint from the following, use 0 to terminate the query")
    for ck in available_checkpoints:
        speak("Option "+str(i_temp)+" "+str(ck))
        i_temp=i_temp+1
    response=requests.get('http://192.168.50.103:5000/consume_audio')
    # print("Response is ",response)
    if response:
        print(response.json())
        com=response.json().get("text")
        com_filtered=normalize_string_advance(com)
        num_out=ai_normalized(com_filtered)
        print(num_out)
        if(num_out==0):
            return
        selected_ck=available_checkpoints[int(num_out)-1]
        return nav_speak(selected_ck,desc,num_out)

def directions_to_list(directions):
    direction_list = []
    
    for direction in directions:
        for key, value in direction.items():
            if key == 'forward':
                direction_list.append(f"walk {value} steps forward")
            elif key == 'left':
                direction_list.append(f"turn {value} degrees to the left")
            elif key == 'right':
                direction_list.append(f"turn {value} degrees to the right")
            elif key == 'checkpoint':
                direction_list.append(f"you will find the {value}.")
    
    return direction_list
def set_nav_stat():
    get_nav_state_req=requests.get("http://192.168.50.103:5000/set_nav_state")
    print("Nav state called")
    print(get_nav_state_req)
    return
    
def navigate(desc):
    global nav_it
    global directions_in_list
    nav_it=0
    cord_data = db.reference('users/maps/'+str(desc)+'/map')
    cord_data_san=cord_data.get()
    directions=pick_subcat(cord_data_san,desc)
    directions_in_list=directions_to_list(directions)
    print(directions_in_list+" directions")
    # set_nav_stat()
    # directions_in_list=['walk 20 steps forward', 'turn 50 degrees to the right', 'walk 10 steps forward', 'you will find the reception .']
    # direction=0
    # print(len(directions_in_list))
    # while(True):
    #     global nav_state
    #     # speak("Start 1")
    #     if(direction<len(directions_in_list)):
    #         # print("Nav status ")
    #         # print(nav_state)
    #         if(nav_state==True):
    #             # speak("Start 2")
    #             print(directions_in_list[direction])
    #             direction=direction+1
    #             nav_state=False
        
        
    #     break
    return
    
def find_maps_near_user():
    ##
    get_nav_state_req=requests.get("http://192.168.50.103:5000/set_nav_state")
    print(get_nav_state_req)
    global global_location
    matches=[]
    ref = db.reference('users/maps')
    opt=ref.get()
    for item in opt:
        print(item)
        cord_data = db.reference('users/maps/'+str(item))
        cord_data_san=cord_data.get()
        latitude_map=cord_data_san['latitude']
        longitude_map=cord_data_san['longitude']
        # print(latitude_map,longitude_map)
        if(check_coord(global_location["lat"],global_location["lon"],latitude_map,longitude_map)):
            matches.append({item:cord_data_san['name']})
    print(matches)
    if(len(matches)==0):
        speak("Sorry No Maps available at this location.")
        get_nav_state_req=requests.get("http://192.168.50.103:5000/set_nav_state_false")
        print(get_nav_state_req)
        return 
    speak("There are total "+str(len(matches))+" options of maps available, please choose from them, if not then please respond with 0.")
    i=1
    for items in matches:
        for key in items:
            speak("Option "+str(i)+" "+items[key])
            i=i+1
    response=requests.get('http://192.168.50.103:5000/consume_audio')
    # print("Response is ",response)
    if response:
        print(response.json())
        com=response.json().get("text")
        com_filtered=normalize_string_advance(com)
        # num_out=word_to_number(com_filtered)
        num_out=ai_normalized(com_filtered)
        num_out=int(num_out)
        print("Number retrieved from open ai is "+str(num_out))
        if(num_out==0):
            get_nav_state_req=requests.get("http://192.168.50.103:5000/set_nav_state_false")
            print(get_nav_state_req)
            return
        else:
            print(num_out)
            print(matches[int(num_out-1)])
            for key in matches[int(num_out-1)]:
                print("Navigation proceeded")
                navigate(key)
    # get_nav_state_req=requests.get("http://192.168.50.103:5000/set_nav_state_false")
    # print(get_nav_state_req)
    return
        

def retrieve_call(com):
    # com="maps maps maps"
    print(com)
    com_list = list(com.split(" "))
    # com_list=["maps"]
    print(com_list)
    for commands in direct_legal_commands:
        if com_list[0] == commands and (commands=="read" or commands=="Read"):
            print(commands)
            speak("Read command initiated")
            text=pi_ocr()
            return text
        if com_list[0] == commands and (commands=="analyze" or commands=="analyse" or commands=="Analyze" or commands=="Analyse"):
            print(commands)
            speak("Analyze command initiated")
            response=analyze()
            speak(response)
            return response,200
        if com_list[0] == commands and (commands=="maps" or commands=="Maps"):
            print(commands)
            speak("Searching for maps near you")
            find_maps_near_user()
            # navigate("data2")
            return "Success",200
        if com_list[0] == commands and (commands=="find" or commands=="Find"):
            print(commands)
            speak("find command initiated")
            normalize_call(com_list)
            find_object(com)
            return True,200
        if com_list[0] == commands and (commands == "Call" or commands=="call"):
            print(commands)
            speak("Calling nearest volunteer")
            call_volunteer()
            return "Success",200
 
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



def upload_icn(get_op):
    icn_ref = db.reference('users/ICN')
    icn_data = icn_ref.get()
    len_of_icn=len(icn_data)
    num=1
    for ele in get_op:
        print()
        if(ele.get("name")!=None):
            icn_ref_name=db.reference(f'users/ICN/data{len_of_icn+1}/name')
            icn_ref_name.push({ele.get("name")})
        if(ele.get("latitude")!=None):
            lat=ele.get("latitude")
            lon=ele.get("longitude")
            icn_ref_loc = db.reference(f'users/ICN/data{len_of_icn+1}/location')
            icn_ref_loc.set({
                "latitude":float(lat),
                "longitude":float(lon)
            })
        icn_ref_data = db.reference(f'users/ICN/data{len_of_icn+1}/data/data{num}')
        num_val=int(ele.get("numeric"))
        text_val=str(ele.get("text"))
        final_data={
            "numeric":num_val,
            "text":text_val
        }
        icn_ref_data.set(final_data)
        num=num+1
 
def cleanup_icn(inn):
    icn_ref_data = db.reference(f'users/ICN/data{inn}')
    icn_ref_data.delete()
       
def update_location_to_map(latitude, longitude):
    ref = db.reference('users/maps')
    snapshot = ref.get()
    num_objects = len(snapshot.keys()) if snapshot else 0
    try:
        ref = db.reference('users/maps')
        category_ref = ref.child(str("data"+str(num_objects)))
        current_map = category_ref.get()
        print(current_map['latitude'])
        if current_map['latitude']!=0 and current_map['longitude']!=0:
            return
        current_map['latitude'] = float(latitude)
        current_map['longitude'] = float(longitude)
        category_ref.set(current_map)
        
        print("Latitude and longitude updated successfully.")
        return True
    except Exception as e:
        print("Error:", e)
        return False      
       
def add_new_data_to_map(key,data):
    ref = db.reference('users/maps')
    snapshot = ref.get()
    num_objects = len(snapshot.keys()) if snapshot else 0
    try:
        ref = db.reference('users/maps')
        category_ref = ref.child(str("data"+str(num_objects)+"/map"))
        current_map = category_ref.get()
        current_map.append({str(key):data})
        category_ref.set(current_map)
        print("Added "+data)
        return True
    except Exception as e:
        print("Error:", e)
        return False

def create_new_checkpoint(data):
    key_list = list(data.split(" "))
    key_list.remove(key_list[0])
    local_name=' '.join(key_list)
    map_data={
        "latitude": 0,
        "longitude": 0,
        "map": [
            None,
            {"checkpoint": str(data)},
        ],
        "name": str(local_name)
    }
    ref = db.reference('users/maps')
    snapshot = ref.get()
    num_objects = len(snapshot.keys()) if snapshot else 0   
    category_ref = ref.child(str("data"+str(num_objects+1)))
    category_ref.set(map_data)
    print("Added "+local_name)
    return

def check_new_checkpoint(data):
    key_list = list(data.split(" "))
    if key_list[0]=="new*" or key_list[0]=="New*":
        create_new_checkpoint(data)
    else:
        add_new_data_to_map("checkpoint",data)

def plot_map_data(category):
    try:
        # Get a reference to the database service
        ref = db.reference('users/maps')

        # Get reference to the specific category
        category_ref = ref.child(category)

        # Get current map data
        current_map = category_ref.get()

        # Initialize plot
        fig, ax = plt.subplots()
        ax.set_aspect('equal')

        # Plot checkpoints
        print(current_map)
        for step in current_map['map']:
            if 'checkpoint' in step:
                checkpoint = step['checkpoint']
                ax.plot(step['latitude'], step['longitude'], 'ro')
                ax.text(step['latitude'], step['longitude'], checkpoint)

        # Plot movements
        current_position = [current_map['latitude'], current_map['longitude']]
        for step in current_map['map']:
            if 'forward' in step:
                distance = step['forward']
                # Update current position based on forward movement
                # Example: current_position = [current_position[0] + dx, current_position[1] + dy]
                ax.arrow(current_position[0], current_position[1], dx, dy, head_width=0.1, head_length=0.1, fc='blue', ec='blue')
            elif 'right' in step:
                angle = step['right']
                # Rotate current position based on right turn
                # Example: Rotate current_position by angle
                # Update current position based on forward movement
                # Example: current_position = [current_position[0] + dx, current_position[1] + dy]
                ax.arrow(current_position[0], current_position[1], dx, dy, head_width=0.1, head_length=0.1, fc='blue', ec='blue')

        plt.xlabel('Latitude')
        plt.ylabel('Longitude')
        plt.title('Map with Movements')
        plt.show()
    except Exception as e:
        print("Error:", e)


##test

def display_blank_page():
    fig, ax = plt.subplots()
    ax.set_aspect('equal')
    plt.xlabel('X-Axis')
    plt.ylabel('Y-Axis')
    plt.title('Indoor Navigation System Visualization')
    plt.xlim(-10, 10)
    plt.ylim(-10, 10)

def plot_forward(ax, current_position, distance):
    global current_pos
    global angle
    distance=int(distance)
    distance=distance/10
    angle_rad = np.radians(angle)
    dx = distance * np.sin(angle_rad)
    dy = distance * np.cos(angle_rad)
    ax.arrow(current_position[0], current_position[1], dx, dy, head_width=0.1, head_length=0.1, fc='blue', ec='blue')
    print(current_pos)
    current_pos=[current_position[0] + dx, current_position[1] + dy]
    
def plot_backward(ax, current_position, distance):
    print("No support for backward nav")

def plot_right(ang):
    global  angle
    ang=int(ang)
    angle=angle+ang
    
def plot_left(ang):
    global angle
    ang=int(ang)
    angle=angle-ang

def plot_checkpoint(ax, name, latitude, longitude):
    ax.plot(latitude, longitude, 'ro')
    ax.text(latitude, longitude, name)

def create_chart(category):
    ref = db.reference('users/maps')
    category_ref = ref.child(str(category+"/map"))
    opt=category_ref.get()
    for subcat in opt:
        if subcat!=None:
            for item in subcat:
                if(item=="checkpoint"):
                    key_list = list(subcat[item].split(" "))
                    if key_list[0]=="new*" or key_list[0]=="New*":
                        continue
                    plot_checkpoint(plt.gca(), subcat[item], current_pos[0],current_pos[1])
                elif(item=="forward"):
                    plot_forward(plt.gca(), current_pos, subcat[item])
                elif(item=="right"):
                    plot_right(subcat[item])
                elif(item=="left"):
                    plot_left(subcat[item])
                else:
                    continue
    plt.show()
# Example usage:

# display_blank_page()
# plot_forward(plt.gca(), current_pos, 10)
# plot_right(90)
# plot_forward(plt.gca(), current_pos, 10)
# plot_right(90)
# plot_forward(plt.gca(), current_pos, 10)
# plot_left(45)
# plot_forward(plt.gca(), current_pos, 10)
# plot_checkpoint(plt.gca(), "Checkpoint A", current_pos[0],current_pos[1])
# plt.show()  # Show the entire plot

# speak("Hello there their are some issues with the current facility")

# print("Returned back")

# analyze_test_v1()


###############################################################
###############################################################

request_login()

# find_maps_near_user()


###############################################################
###############################################################
# print(image_to_ai("captured_frame.jpg","Tell me everything about the image in 50 words"))
# find_maps_near_user()
# navigate("data3")
# print(nav_speak("reception ","data3",1))
# print(ai_normalized("to"))

# analyze()
# help_navigate({'data': {'data1': {'numeric': 0, 'text': 'Entry'}, 'data2': {'numeric': 15, 'text': 'Steps Forward'}, 'data3': {'numeric': 90, 'text': 'Degree Left turn'}, 'data4': {'numeric': 0, 'text': 'Study room'}, 'data5': {'numeric': 0, 'text': 'Entry'}, 'data6': {'numeric': 15, 'text': 'Steps forward'}, 'data7': {'numeric': 90, 'text': 'Degree Right'}, 'data8': {'numeric': 0, 'text': 'Bedroom'}}, 'location': {'latitude': 22.962601, 'longitude': 76.046091}, 'name': 'location 3'})


# response=requests.get('http://192.168.127.103:5000/consume_audio')
# print(response.json().get("text"))

# find_map()
# 
# for i in range (0,4):
#     upload_icn([{"latitude":56.88,"longitude":23.65,"numeric":45,"text":"Hello"},{"numeric":46,"text":"Hello"},{"numeric":47,"text":"Hello"},{"numeric":48,"text":"Hello"}])
# cleanup(4)

# get_stream_vol()
# print(get_ip())

# pi_ocr()

# find_map()


# call_volunteer()
@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return 'No file part'
    file = request.files['file']
    if file.filename == '':
        return 'No selected file'
    file.save('uploaded_audio.wav')  # Save the received audio file
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
    global nav_it
    global directions_in_list
    if(len(directions_in_list)<=0):
        return "Success",200
    print(nav_it)
    print(f' -> {len(directions_in_list)}')
    if(nav_it<int(len(directions_in_list)-1)):
        speak(directions_in_list[nav_it])
        nav_it=nav_it+1 
        return "Success",200  
    nav_it=0
    get_nav_state_req=requests.get("http://192.168.50.103:5000/set_nav_state_false")
    print(get_nav_state_req)
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
    
    
@app.route('/get_nav_state')
def get_nav_state():
    print("nav state triggered")
    global nav_state
    nav_state=True
    return "Success",200


@app.route('/get_audio_const', methods=['POST'])
def get_audio_const():
    print("Called")
    try:
        if 'audio' not in request.files:
            return 'No audio file provided', 400

        audio_file = request.files['audio']

        audio_file.save('audio_const.wav')

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

@app.route('/city_tag', methods=['POST'])
def city_tag():
    try:
        data = request.json
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        input_text = data.get('inputText')

        # Process the data as needed
        print(f"Received data: Latitude - {latitude}, Longitude - {longitude}, Input Text - {input_text}")
        print(input_text)
        
        # Send a response
        response = {'message': 'Data received successfully'}
        return jsonify(response),200
    except Exception as e:
        print(f"Error handling request: {e}")
        response = {'message': 'Failed to process request'}
        return jsonify(response),500

###This is a VERY SENSITIVE section please do not change code without taking a backup!!

@app.route('/checkpoint', methods=['POST'])
def receive_checkpoint():
    data = request.form['data']
    print("Received data:", data)
    check_new_checkpoint(data)
    return 'Data received successfully!', 200

@app.route('/upward-arrow', methods=['POST'])
def receive_upward_arrow():
    data = request.form['text']
    print("Received data:", data)
    add_new_data_to_map("forward",data)
    return 'Data received successfully!', 200

@app.route('/downward-arrow', methods=['POST'])
def receive_downward_arrow():
    data = request.form['text']
    print("Received data:", data)
    add_new_data_to_map("backward",data)
    return 'Data received successfully!', 200

@app.route('/left-arrow', methods=['POST'])
def receive_left_arrow():
    data = request.form['text']
    print("Received data:", data)
    add_new_data_to_map("left",data)
    return 'Data received successfully!', 200

@app.route('/right-arrow', methods=['POST'])
def receive_right_arrow():
    data = request.form['text']
    print("Received data:", data)
    add_new_data_to_map("right",data)
    return 'Data received successfully!', 200

@app.route('/send-coordinates', methods=['POST'])
def receive_coordinates():
    latitude1 = request.form['latitude']
    longitude1 = request.form['longitude']
    update_location_to_map(latitude1,longitude1)
    print("Received coordinates: Latitude {}, Longitude {}".format(latitude1, longitude1))
    return 'Coordinates received successfully!', 200


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)


#Structure of the sample data


# ref = db.reference('/')
#     users_ref = ref.child('users')
#     users_ref.set({
#         'volunteer':{
#             1:{
#                 'current_ip':'http://192.168.29.28:8080',
#                 'location':{
#                     'lat':11.23,
#                     'lon':12.34
#                 }
#             },
#             2:{
#                 'current_ip':'http://192.168.29.28:8080',
#                 'location':{
#                     'lat':21.23,
#                     'lon':22.34
#                 }
#             },
#             3:{
#                 'current_ip':'http://192.168.29.28:8080',
#                 'location':{
#                     'lat':31.23,
#                     'lon':32.34
#                 }
#             },
#             4:{
#                 'current_ip':'http://192.168.29.28:8080',
#                 'location':{
#                     'lat':41.23,
#                     'lon':42.34
#                 }
#             }
#         },
#         'pi_user':{
#             1:{
#                 'current_location':{
#                     'lat':1.23,
#                     'lon':1.34
#                 }
#             },
#             2:{
#                 'current_location':{
#                     'lat':2.23,
#                     'lon':2.34
#                 }
#             }
#         }
#     })

#direction