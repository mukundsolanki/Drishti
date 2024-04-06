# from google.cloud import speech_v1p1beta1
# from google.cloud.speech_v1p1beta1 import types
# import io

# def transcribe_audio(api_key, audio_file_path):
#     client = speech_v1p1beta1.SpeechClient.from_service_account_file(api_key)

#     with io.open(audio_file_path, 'rb') as audio_file:
#         content = audio_file.read()

#     audio = types.RecognitionAudio(content=content)
#     config = types.RecognitionConfig(
#         encoding=speech_v1p1beta1.RecognitionConfig.AudioEncoding.LINEAR16,
#         sample_rate_hertz=44100,
#         language_code='en-US',
#     )

#     response = client.recognize(config=config, audio=audio)

#     complete_transcript = ''

#     for result in response.results:
#         complete_transcript += result.alternatives[0].transcript + ' '

#     return complete_transcript.strip()

# if __name__ == '__main__':
    

#     transcribe_audio(api_key, audio_file_path)




# OCR


from google.cloud import vision

client = vision.ImageAnnotatorClient()

# Read the image file
with open('./test_image.jpg', 'rb') as image_file:
    content = image_file.read()

# Perform OCR on the image
image = vision.Image(content=content)
response = client.text_detection(image=image)

# Extract text from the response
texts = response.text_annotations
for text in texts:
    print(f'Detected text: {text.description}')
    break

# stream to pic




