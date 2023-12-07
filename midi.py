import rtmidi

import time

selection = int(input("Enter MIDI Channel (1-16):"))
if selection in range(1, 17):
    channel = 0xB << 4 | selection - 1
    print(hex(channel))