# pip install mido pyautogui python-rtmidi

import csv
import mido
import pyautogui

# Ask the user what action to take
user_action = input("Type 'move' to move the mouse or 'click' to click: ").strip().lower()

# Validate user input
if user_action not in ['move', 'click']:
    print("Invalid action. The script will exit.")
    exit(1)

def note_name_to_midi(note_name):
    notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    note = ''.join([c for c in note_name if c.isalpha()])
    octave = int(''.join([c for c in note_name if c.isdigit()]))
    note_index = notes.index(note)
    midi_number = (octave + 1) * 12 + note_index
    return midi_number

def load_config_csv(config_path):
    note_to_position = {}
    with open(config_path, newline='') as csvfile:
        csvreader = csv.reader(csvfile)
        next(csvreader, None)  # Skip the header row
        for row in csvreader:
            if not row or row[0].startswith("#"):  # Skip empty lines or comments
                continue
            note_name, x, y = row
            midi_note = note_name_to_midi(note_name)
            note_to_position[midi_note] = (int(x), int(y))
    return note_to_position

# Ask the user for the configuration file name
config_filename = input("Enter the configuration CSV file name: ").strip()
note_to_position = load_config_csv(config_filename)

# This function converts MIDI note numbers to note names (e.g., 60 -> 'C4')
def note_number_to_name(note_number):
    return mido.get_note_name(note_number)

# Open the MIDI input port.
input_name = mido.get_input_names()[0]
inport = mido.open_input(input_name)

print(f"Listening for MIDI input on '{input_name}'... Press Ctrl+C to stop.")

try:
    for msg in inport:
        if msg.type == 'note_on':
            note_name = note_number_to_name(msg.note)
            note_number = msg.note
            if msg.velocity > 0:
                print(f"Note ON: {note_name} (Number: {note_number})")
                if note_number in note_to_position:
                    x, y = note_to_position[note_number]
                    print(f"  -> Clicking at position ({x}, {y})")
                    if user_action == 'click':
                        pyautogui.click(x, y)  # Click at the mapped location
                    else:  # default to move if not click
                        pyautogui.moveTo(x, y)  # Move the mouse to the mapped location
            else:
                print("  -> Note OFF")
except KeyboardInterrupt:
    print("Exiting...")
except Exception as e:
    print(f"An error occurred: {e}")
finally:
    inport.close()  # Close the MIDI port when you're done
