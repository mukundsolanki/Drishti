import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav

def record_and_save_audio(file_name, duration=5, sample_rate=44100):
    """
    Records audio for a specified duration and saves it to a WAV file.

    Parameters:
    - file_name (str): Name of the WAV file to save.
    - duration (float): Duration of recording in seconds (default is 5 seconds).
    - sample_rate (int): Sampling rate of the audio (default is 44100 Hz).
    """
    # Record audio
    audio_data = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype=np.float32)
    print("Recording audio for {} seconds...".format(duration))
    sd.wait()  # Wait for the recording to finish
    print("Recording finished.")
    
    # Save audio to file
    wav.write(file_name, sample_rate, audio_data)

    print("Audio saved as:", file_name)
    
    
    
record_and_save_audio("my_recorded_audio.wav", duration=5)
