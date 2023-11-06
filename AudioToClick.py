# pip install pyaudio numpy aubio pyautogui

import csv
import numpy as np
import pyautogui
import aubio
import pyaudio

# Ask the user what action to take
user_action = input("Type 'move' to move the mouse or 'click' to click: ").strip().lower()

# Validate user input
if user_action not in ['move', 'click']:
    print("Invalid action. The script will exit.")
    exit(1)

# A4 is commonly set at 440 Hz
A4_FREQUENCY = 440.0
A4_NOTE = 'A4'
SEMITONE_RATIO = 2 ** (1/12)

def note_to_frequency(note):
    note_distances = {'C': -9, 'C#': -8, 'D': -7, 'Eb': -6, 'E': -5, 'F': -4,
                      'F#': -3, 'G': -2, 'Ab': -1, 'A': 0, 'Bb': 1, 'B': 2}
    base_note = note[:-1]
    octave = int(note[-1])
    distance_from_a4 = note_distances[base_note] + (octave - 4) * 12
    frequency = A4_FREQUENCY * (SEMITONE_RATIO ** distance_from_a4)
    return frequency

def load_config_csv(config_path):
    pitch_to_position = {}
    try:
        with open(config_path, newline='') as csvfile:
            csvreader = csv.reader(csvfile)
            for row in csvreader:
                if not row or row[0].startswith("#"):  # Skip empty lines or comments
                    continue
                note, x, y = row
                pitch = note_to_frequency(note)  # Convert note to frequency
                pitch_to_position[pitch] = (int(x), int(y))
    except FileNotFoundError:
        print(f"No configuration file found at {config_path}. Exiting.")
        exit(1)
    except ValueError as e:
        print(f"Error reading the configuration file: {e}. Exiting.")
        exit(1)
    
    return pitch_to_position

# Ask the user for the configuration file name
config_filename = input("Enter the configuration CSV file name: ").strip()
pitch_to_position = load_config_csv(config_filename)

# Audio processing setup
buffer_size = 2048
pyaudio_instance = pyaudio.PyAudio()
stream = pyaudio_instance.open(format=pyaudio.paFloat32, channels=1, rate=44100, input=True, frames_per_buffer=buffer_size)
pitch_o = aubio.pitch("default", buffer_size, buffer_size//2, 44100)
pitch_o.set_unit("Hz")
pitch_o.set_tolerance(0.8)

try:
    print("Listening for pitches. Press CTRL+C to stop.")
    while True:
        audiobuffer = stream.read(buffer_size)
        signal = np.frombuffer(audiobuffer, dtype=np.float32)
        pitch = pitch_o(signal)[0]
        confidence = pitch_o.get_confidence()
        
        if confidence > 0.8:  # Adjust the confidence level if needed
            print(f"Detected pitch: {pitch} Hz with confidence: {confidence}")
            closest_pitch = min(pitch_to_position.keys(), key=lambda p: abs(p - pitch))
            if abs(closest_pitch - pitch) < 1:  # You may need to adjust this threshold
                x, y = pitch_to_position[closest_pitch]
                print(f"  -> Moving mouse to position ({x}, {y})")
                if user_action == 'click':
                    pyautogui.click(x, y)  # Click at the mapped location
                else:  # default to move if not click
                    pyautogui.moveTo(x, y)  # Move the mouse to the mapped location
except KeyboardInterrupt:
    print("\nExiting by user request.")
except Exception as e:
    print(f"An error occurred: {e}")
finally:
    stream.stop_stream()
    stream.close()
    pyaudio_instance.terminate()
