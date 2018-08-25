import ctypes.wintypes, mido, time

'''XINPUT_GAMEPAD and XINPUT_STATE structs from...'''
'''https://docs.microsoft.com/en-us/windows/desktop/api/XInput/ns-xinput-_xinput_gamepad'''
'''https://docs.microsoft.com/en-us/windows/desktop/api/XInput/ns-xinput-_xinput_state'''

xinput = ctypes.windll.xinput9_1_0

class XINPUT_GAMEPAD(ctypes.Structure):
    _fields_ = [
    ("wButtons", ctypes.wintypes.WORD),
    ("bLeftTrigger", ctypes.wintypes.BYTE),
    ("bRightTrigger", ctypes.wintypes.BYTE),
    ("sThumbLX", ctypes.wintypes.SHORT),
    ("sThumbLY", ctypes.wintypes.SHORT),
    ("sThumbRX", ctypes.wintypes.SHORT),
    ("sThumbRY", ctypes.wintypes.SHORT)]

class XINPUT_STATE(ctypes.Structure):
    _fields_ = [
    ("dwPacketNumber", ctypes.wintypes.DWORD),
    ("Gamepad", XINPUT_GAMEPAD)]

'''initialize values'''
outport = mido.open_output("Virtual Port 1", autoreset = True)
state = XINPUT_STATE()
prevGreen = 0
prevRed = 0
prevYellow = 0
prevBlue = 0
prevOrange = 0
prevUp = 0
prevDown = 0
prevLeft = 0
prevRight = 0
prevStart = 0
prevBack = 0
prevWhammyMidiValue = ((state.Gamepad.sThumbRX + 32768) >> 2) - 8192
prevTiltMidiValue = ((state.Gamepad.sThumbRY + 32768) >> 2) - 8192
soundingNotes = []
playMode = 0 #0 = chord mode, 1 = tap mode
chords = ["A", "B", "C", "D", "E", "F", "G", "AA"]
vibratoMode = 1 #off, tilt, whammy
tapIndex = 0
tapNotes = [[69, 67, 65, 62, 60], [68, 66, 64, 61, 59]]

if xinput.XInputGetState(ctypes.wintypes.WORD(0),ctypes.pointer(state)) == 0:
    prevWhammyMidiPos = state.Gamepad.sThumbRX
    prevTiltMidiPos = state.Gamepad.sThumbRY
else:
    print("Controller not found.")
    quit()


def sendMidi(buttonDeltas, whammyMidiValue, tiltMidiValue):
    global playMode
    global vibratoMode
    global tapIndex


    if(vibratoMode == 1 and tiltMidiValue != None): #tilt vibrato, whammy tremolo
        msg = mido.Message("pitchwheel", pitch = tiltMidiValue)
        outport.send(msg)
        print("ay")
    elif(vibratoMode == 2 and whammyMidiValue != None): #whammy vibrato, tilt tremolo
        msg = mido.Message("pitchwheel", pitch = whammyMidiValue)
        outport.send(msg)
        print("ayyyy")

    '''mode swapping'''
    if(buttonDeltas[9] == 0b01): #start hit, change playMode
        playMode = (playMode + 1) % 2
        killSoundingNotes()

    if(buttonDeltas[10] == 0b01): #back hit, change vibrato mode
        vibratoMode = (vibratoMode + 1) % 3


    '''chord mode'''
    if(playMode == 0):
        if(buttonDeltas[6] == 0b01): #downstrum, kill notes, then send appropriate ones
            killSoundingNotes()

            fours = (1 if (buttonDeltas[0] == 0b01 or buttonDeltas[0] == 0b11) else 0)
            twos = (1 if (buttonDeltas[1] == 0b01 or buttonDeltas[1] == 0b11) else 0)
            ones = (1 if (buttonDeltas[2] == 0b01 or buttonDeltas[2] == 0b11) else 0)
            minorModifier = (1 if (buttonDeltas[3] == 0b01 or buttonDeltas[3] == 0b11) else 0)
            seventhModifier = (1 if (buttonDeltas[4] == 0b01 or buttonDeltas[4] == 0b11) else 0)

            chord = determineChord(fours, twos, ones, minorModifier, seventhModifier) #TODO ref global
            midiNotes = chordToMidi(chord)

            for note in midiNotes:
                msg = mido.Message("note_on", note = note)
                outport.send(msg)
                soundingNotes.append(note)

        if(buttonDeltas[5] == 0b01):
            killSoundingNotes()

    elif(playMode == 1):
        if(buttonDeltas[6] == 0b01): #downstrum, kill, then advance index
            killSoundingNotes()
            tapIndex = (tapIndex + 1) % len(tapNotes)
        playTapNotes(buttonDeltas[0], buttonDeltas[1], buttonDeltas[2], buttonDeltas[3], buttonDeltas[4])


def killSoundingNotes():
    global soundingNotes
    for note in soundingNotes:
        msg = mido.Message("note_off", note = note)
        outport.send(msg)
    soundingNotes = []


def playTapNotes(green, red, yellow, blue, orange):
    global tapNotes
    global tapIndex
    global soundingNotes
    if(green == 0b01):
        msg = mido.Message("note_on", note = tapNotes[tapIndex][0])
        outport.send(msg)
        soundingNotes.append(tapNotes[tapIndex][0])
    elif(green == 0b10):
        msg = mido.Message("note_off", note = tapNotes[tapIndex][0])
        outport.send(msg)
        if tapNotes[tapIndex][0] in soundingNotes: soundingNotes.remove(tapNotes[tapIndex][0])
    if(red == 0b01):
        msg = mido.Message("note_on", note = tapNotes[tapIndex][1])
        outport.send(msg)
        soundingNotes.append(tapNotes[tapIndex][1])
    elif(red == 0b10):
        msg = mido.Message("note_off", note = tapNotes[tapIndex][1])
        outport.send(msg)
        if tapNotes[tapIndex][1] in soundingNotes: soundingNotes.remove(tapNotes[tapIndex][1])
    if(yellow == 0b01):
        msg = mido.Message("note_on", note = tapNotes[tapIndex][2])
        outport.send(msg)
        soundingNotes.append(tapNotes[tapIndex][2])
    elif(yellow == 0b10):
        msg = mido.Message("note_off", note = tapNotes[tapIndex][2])
        outport.send(msg)
        if tapNotes[tapIndex][2] in soundingNotes: soundingNotes.remove(tapNotes[tapIndex][2])
    if(blue == 0b01):
        msg = mido.Message("note_on", note = tapNotes[tapIndex][3])
        outport.send(msg)
        soundingNotes.append(tapNotes[tapIndex][3])
    elif(blue == 0b10):
        msg = mido.Message("note_off", note = tapNotes[tapIndex][3])
        outport.send(msg)
        if tapNotes[tapIndex][3] in soundingNotes: soundingNotes.remove(tapNotes[tapIndex][3])
    if(orange == 0b01):
        msg = mido.Message("note_on", note = tapNotes[tapIndex][4])
        outport.send(msg)
        soundingNotes.append(tapNotes[tapIndex][4])
    elif(orange == 0b10):
        msg = mido.Message("note_off", note = tapNotes[tapIndex][4])
        outport.send(msg)
        if tapNotes[tapIndex][4] in soundingNotes: soundingNotes.remove(tapNotes[tapIndex][4])

def determineChord(fours, twos, ones, minorModifier, seventhModifier):
    global chords
    binary = (ones | (twos << 1) | (fours << 2))
    chord = ""

    '''change these chord names to change tuning'''
    '''known chords you can swap out: A#, C#, D#, F#, G#'''
    if(binary == 0b000):
        chord = chords[0]
    elif(binary == 0b001):
        chord = chords[1]
    elif(binary == 0b010):
        chord = chords[2]
    elif(binary == 0b011):
        chord = chords[3]
    elif(binary == 0b100):
        chord = chords[4]
    elif(binary == 0b101):
        chord = chords[5]
    elif(binary == 0b110):
        chord = chords[6]
    elif(binary == 0b111): #for m7 variant, it would be hard to hit 5 buttons with four fingers, but it can be done
        chord = chords[7] # (so let's just put A... again.. but higher)
    if(minorModifier == 1):
        chord += "m"
    if(seventhModifier == 1):
        chord += "7"

    return chord


def chordToMidi(chordName):
    notes = [] #will store the notes to hit
    if(chordName.startswith("1")):
        notes = [60, 65, 69, 72]
    if(chordName.startswith("2")):
        notes = [60, 64, 69, 72]
    if(chordName.startswith("3")):
        notes = [58, 62, 65, 70]
    if(chordName.startswith("4")):
        notes = [62, 65, 68, 72]

    if(chordName.startswith("A#")):
        notes = [58, 62, 65, 70]
    elif(chordName.startswith("C#")):
        notes = [61, 65, 68, 73]
    elif(chordName.startswith("D#")):
        notes = [63, 67, 70, 75]
    elif(chordName.startswith("F#")):
        notes = [66, 70, 73, 78]
    elif(chordName.startswith("G#")):
        notes = [56, 60, 63, 68]
    elif(chordName.startswith("AA")):
        notes = [69, 73, 76, 81]
    elif(chordName.startswith("A")):
        notes = [57, 61, 64, 69]
    elif(chordName.startswith("B")):
        notes = [59, 63, 66, 71]
    elif(chordName.startswith("C")):
        notes = [60, 64, 67, 72]
    elif(chordName.startswith("D")):
        notes = [62, 66, 69, 74]
    elif(chordName.startswith("E")):
        notes = [64, 68, 71, 76]
    elif(chordName.startswith("F")):
        notes = [65, 69, 72, 77]
    elif(chordName.startswith("G")):
        notes = [67, 71, 74, 79]

    '''for i in range(len(notes)):
        notes[i] = notes[i] - 12'''

    if(chordName.endswith("m")):
        notes[1] = notes[1] - 1
    elif(chordName.endswith("7")):
        if(chordName.endswith("m7")):
            notes[1] = notes[1] - 1
            notes[3] = notes[3] - 1
        else:
            notes[3] = notes[3] - 1

    return notes

'''request updated values in a loop'''
while True:
    if xinput.XInputGetState(ctypes.wintypes.WORD(0),ctypes.pointer(state)) == 0:
        green = (state.Gamepad.wButtons & 0b0001000000000000) >> 12
        red = (state.Gamepad.wButtons & 0b0010000000000000) >> 13
        yellow = (state.Gamepad.wButtons & 0b1000000000000000) >> 15
        blue = (state.Gamepad.wButtons & 0b0100000000000000) >> 14
        orange = (state.Gamepad.wButtons & 0b0000000100000000) >> 8
        up = (state.Gamepad.wButtons & 0b0000000000000001)
        down = (state.Gamepad.wButtons & 0b0000000000000010) >> 1
        left = (state.Gamepad.wButtons & 0b0000000000001000) >> 3
        right = (state.Gamepad.wButtons & 0b0000000000000100) >> 2
        start = (state.Gamepad.wButtons & 0b0000000000010000) >> 4
        back = (state.Gamepad.wButtons & 0b0000000000100000) >> 5
        whammyMidiValue = ((state.Gamepad.sThumbRX + 32768) >> 2) - 8192
        tiltMidiValue = ((state.Gamepad.sThumbRY + 32768) >> 2) - 8192

        buttonDeltas = []
        buttonDeltas.append((prevGreen << 1) | green)
        buttonDeltas.append((prevRed << 1) | red)
        buttonDeltas.append((prevYellow << 1) | yellow)
        buttonDeltas.append((prevBlue << 1) | blue)
        buttonDeltas.append((prevOrange << 1) | orange)
        buttonDeltas.append((prevUp << 1) | up)
        buttonDeltas.append((prevDown << 1) | down)
        buttonDeltas.append((prevLeft << 1) | left)
        buttonDeltas.append((prevRight << 1) | right)
        buttonDeltas.append((prevStart << 1) | start)
        buttonDeltas.append((prevBack << 1) | back)

        '''if there was no change in tilt/whammy, we don't need to send MIDI CCs'''
        if(whammyMidiValue == prevWhammyMidiValue):
            whammyMidiValue = None
        else:
            prevWhammyMidiValue = whammyMidiValue

        if(tiltMidiValue == prevTiltMidiValue):
            tiltMidiValue = None
        else:
            prevTiltMidiValue = tiltMidiValue

        '''what's new is old'''
        prevGreen = green
        prevRed = red
        prevYellow = yellow
        prevBlue = blue
        prevOrange = orange
        prevUp = up
        prevDown = down
        prevLeft = left
        prevRight = right
        prevStart = start
        prevBack = back

        sendMidi(buttonDeltas, whammyMidiValue, tiltMidiValue)

        printBlock = ("\n"
            + ("\ngreen:  {}".format(green))
            + ("\nred:    {}".format(red))
            + ("\nyellow: {}".format(yellow))
            + ("\nblue:   {}".format(blue))
            + ("\norange: {}".format(orange))
            + ("\nup:     {}".format(up))
            + ("\ndown:   {}".format(down))
            + ("\nleft:   {}".format(left))
            + ("\nright:  {}".format(right))
            + ("\nstart:  {}".format(start))
            + ("\nback:   {}".format(back))
            + ("\nwhammy midi value: " + (str(whammyMidiValue) if whammyMidiValue != None else str(prevWhammyMidiValue)))
            + ("\ntilt midi value:   " + (str(tiltMidiValue) if tiltMidiValue != None else str(prevTiltMidiValue)))
            + ("\nvibrato mode: " + (str(vibratoMode))))

        print(printBlock, end = "\r")

    else:
        print("Controller not found.")
        quit()
