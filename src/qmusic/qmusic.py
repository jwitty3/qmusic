#qutip, numpy, matplotlib, pil.imagetk, scipy, tkinter
from qutip import *
from qutip import measurement as qm
import numpy as np
from pylab import *
from PIL import ImageTk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from  scipy import signal
import pygame
from tkinter import *
from tkinter import ttk
from tkinter import messagebox
import os
import re
import ctypes
import platform

def main():
    axes = None
    sounds = []
    #frequencies of notes
    notes = np.array([
        261.63, #C        0
        277.18, #C#Db     1
        293.66, #D        2
        311.13,	#D#Eb     3
        329.63,	#E        4
        349.23, #F        5
        369.99, #F#Gb     6
        392.00, #G        7
        415.30, #G#Ab     8
        440.00, #A        9
        466.16, #A#Bb     10
        493.88, #B        11
        0])
    #[note length, played note length, notes array index, octave multiplier]
    bassline = np.array([
        [32, 0, 8, 1],
        [32, 32, 8, .25], 
        [32, 32, 0, .5], 
        [32, 32, 8, .25],
        [32, 32, 0, .5], 
        [16, 16, 8, .25],
        [16, 16, 10, .25], 
        [4, 4, 0, .5]])
    scales = np.array([
        [0, 3, 5, 7, 10],       #C Minor Pentatonic
        [0, 2, 4, 5, 7, 9, 11], #C Major
        [0, 3, 5, 6, 7, 10]     #C Blues
    ], dtype=np.ndarray)

    states = [coherent(20, 1.73)]

    if (platform.system() == "Windows"):
        awareness = ctypes.c_int()
        errorCode = ctypes.windll.shcore.GetProcessDpiAwareness(0, ctypes.byref(awareness))
        errorCode = ctypes.windll.shcore.SetProcessDpiAwareness(2)
        success = ctypes.windll.user32.SetProcessDPIAware()
    
    root = Tk()
    root.title('Quantum Music')
    
    pygame.mixer.init(size=32)
    bassbox = IntVar()
    loopbox = IntVar()
    looptimer = 1#root.after(0, lambda: None)
    
    #generate data array by measuring a state
    def generate():
        scale = []
        if scalebox.current() == -1:
            test = "^(([0-9]|1[01])\,[\s]*)+([0-9]|1[01])?\s*$"
            val = scalebox.get() + " "
            if re.sub(test, "", val) == "":
                scale = np.fromstring(val, dtype=int, sep=",")
            else:
                messagebox.showerror('Input Error', "'Scale' input must be a list of integers less than or equal to 11")
                return
        else:
            scale = np.array(scales[scalebox.current()])
        dim = 20 if bignvalue.get() == "" else int(bignvalue.get())
        littlen = 0 if littlenvalue.get() == "" else int(littlenvalue.get())

        states = [coherent(dim, np.sqrt(littlen)), basis(dim, n=littlen), fock(dim, n=littlen), thermal_dm(dim, littlen), maximally_mixed_dm(dim)]
        operators = [create(dim),destroy(dim),displace(dim, 1),qeye(dim),momentum(dim),num(dim),phase(dim),position(dim),qzero(dim),tunneling(dim)]
        data = np.array([])

        graph(states)
        
        
        for i in range(int(length.get())):
            x = qm.measure(states[int(state.current())], operators[int(operator.current())])
            x = int(str(x[1].data)[3:4])
            data = np.append(data, x)

        generatesound(data, scale)

    #play sounds
    def generatesound(state, scale):
        playbutton.configure(command=cancelsound)
        playbutton['text'] = "Stop"
        
        bassindex = 0;
        bpm = int(speed.get())
        fs = 44100
        freqs = np.array([0])
        #indices of notes in notes array

        #generate array of note frequencies in selected scale
        for i in range(int(max(state) + 1)):
            freq = notes[scale[i % scale.size]] * 2**np.floor(i / scale.size)
            freqs = np.append(freqs, freq)

        #generate sounds using pygame sounds
        buffer = np.array([]).astype(np.float32)
        for index in range(state.size):
            #to change the wave in the buffer variable, use "signal.square" or "np.sine" (or maybe "signal.sweep.poly") or "signal.sawtooth"
            t = 2 * np.pi * np.arange(fs * 2 * 60 / bpm)
            buffer = np.concatenate((buffer, signal.sawtooth(t * freqs[int(state[index])] / fs).astype(np.float32)))
        
        #generate bassline
        bassbuffer = np.array([]).astype(np.float32)
        for index in range(int(bassline.size / 4)):
            bassarr = bassline[index]
            y = 2 * np.pi * np.arange(fs * bassarr[1] * 2 * 60 / bpm)
            bassbuffer = np.concatenate((bassbuffer, np.sin(y * notes[int(bassarr[2])] * bassarr[3] / fs).astype(np.float32)))
            bassindex += 1
        
        
        basssound = pygame.mixer.Sound(bassbuffer)
        sound = pygame.mixer.Sound(buffer)
        sounds.append(sound)
        sounds.append(basssound)
        setvolume(sounds)
        def playsound():
            if (playbutton['text'] == "Play"):
                return
            sound.play()
            nonlocal looptimer
            looptimer = root.after(int(sound.get_length() * 1000), lambda: playsound() if loopbox.get() == 1 else cancelsound())   
        playsound()
        if (bassbox.get() == 1):
            basssound.play()
        
    #stop playing sounds
    def cancelsound():
        playbutton.configure(command=generate)
        playbutton['text'] = "Play"
        pygame.mixer.stop()
        root.after_cancel(looptimer)
        
    def setvolume(obj):
        for sound in sounds:
            sound.set_volume(1 / (10 - volumeslider.get()) - .1)
    
    def validatenum(input, max, message):
        if max == "bignvalue":
            max = 19 if bignvalue.get() == "" else int(bignvalue.get()) - 1
        if input == "":
            return True
        if input.isdigit():
            if int(input) <= int(max):
                return True
            else:
                messagebox.showerror('Input Out of Bounds', message)
        return False
    
    def validatescale(input):
        test = "^[\,\s0-9]*$"
        if re.sub(test, "", input) == "":
            return True
        return False
    
    #build widgetsa
    content = ttk.Frame(root)
    labels = ttk.Frame(content)
    inputs = ttk.Frame(content)
    playcontainer = ttk.Frame(content)
    
    #validate command
    vcmd = inputs.register(validatenum);
    vcmds = inputs.register(validatescale);
    
    title = ttk.Label(content, text="Quantum Music")
    bignvaluelabel = ttk.Label(labels, text="N")
    littlenvaluelabel = ttk.Label(labels, text="n")
    statelabel = ttk.Label(labels, text="State")
    operatorlabel = ttk.Label(labels, text="Operator")
    lengthlabel = ttk.Label(labels, text="Music Length")
    speedlabel = ttk.Label(labels, text="Speed (BPM)")
    basslabel = ttk.Label(labels, text="Bassline")
    looplabel = ttk.Label(labels, text="Loop")
    scalelabel = ttk.Label(labels, text="Scale")
    bignvalue = ttk.Entry(inputs, validate = "key", validatecommand = (vcmd, '%P', 100, "N valaue must be an integer less than 100"))
    littlenvalue = ttk.Entry(inputs, validate = "key", validatecommand = (vcmd, '%P', "bignvalue", "n value must be an integer less than N"))
    length = ttk.Entry(inputs, validate = "key", validatecommand = (vcmd, '%P', 385, "Length value must be an integer less than 385"))
    speed = ttk.Entry(inputs, validate = "key", validatecommand = (vcmd, '%P', 1000, "Speed value must be an integer less than 1000"))
    bass = ttk.Checkbutton(inputs, variable=bassbox, onvalue=1, offvalue=0)
    loop = ttk.Checkbutton(inputs, variable=loopbox, onvalue=1, offvalue=0)
    scalebox = ttk.Combobox(inputs, validate = "key", validatecommand = (vcmds, '%P'))
    scalebox['values'] = ('C Minor Pentatonic', 'C Major', 'C Blues')
    state = ttk.Combobox(inputs)
    state['values'] = ('Coherent', 'Basis', 'Fock', 'Thermal', 'Maximally Mixed')
    operator = ttk.Combobox(inputs)
    operator['values'] = ('Create', 'Destroy', 'Displace', 'Identity', 'Momentum', 'Num', 'Phase', 'Position', 'Zero', 'Tunneling')
    playbutton = ttk.Button(playcontainer, text="Play", command=generate)
    volumeslider = ttk.Scale(playcontainer, from_=0, to=9.09, orient="horizontal", value=9.09, command=lambda x: setvolume(sounds))
    volumelabel = ttk.Label(playcontainer, text="Volume")

    bignvalue.insert(0, "20")
    littlenvalue.insert(0, "3")
    length.insert(0, "16")
    speed.insert(0, "480")
    scalebox.current(0)
    state.current(0)
    operator.current(5)

    state.state(["readonly"])
    operator.state(["readonly"])

    style = ttk.Style(content)
    style.configure("TLabel", font=("Arial", 12))

    #display widgets
    content.pack(fill="both", expand=True)
    title.pack(pady=20)
    playcontainer.pack(side="bottom", expand=True, pady=25)
    playbutton.pack(side="left", expand=True, padx=25)
    volumelabel.pack(side="left", expand=True, padx=10)
    volumeslider.pack(side="left", expand=True)
    labels.pack(side="left", fill="both", expand=True, padx=20)
    inputs.pack(side="left", fill="both", expand=True, padx=20)
    bignvalue.pack(expand=True, anchor="e", pady=10)
    littlenvalue.pack(expand=True, anchor="e", pady=10)
    length.pack(expand=True, anchor="e", pady=10)
    speed.pack(expand=True, anchor="e", pady=10)
    bass.pack(expand=True, anchor="e", pady=10)
    loop.pack(expand=True, anchor="e", pady=10)
    scalebox.pack(expand=True, anchor="e", pady=10)
    state.pack(expand=True, anchor="e", pady=10)
    operator.pack(expand=True, anchor="e", pady=10)
    bignvaluelabel.pack(expand=True, anchor="e", pady=10)
    littlenvaluelabel.pack(expand=True, anchor="e", pady=10)
    lengthlabel.pack(expand=True, anchor="e", pady=10)
    speedlabel.pack(expand=True, anchor="e", pady=10)
    basslabel.pack(expand=True, anchor="e", pady=10)
    looplabel.pack(expand=True, anchor="e", pady=10)
    scalelabel.pack(expand=True, anchor="e", pady=10)
    statelabel.pack(expand=True, anchor="e", pady=10)
    operatorlabel.pack(expand=True, anchor="e", pady=10)
    
    fig, axes = plt.subplots(figsize=(5, 5))
    plot_fock_distribution(states[int(state.current())], fig=fig, ax=axes)
    canvas = FigureCanvasTkAgg(fig, master = content)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True, padx=20)

    def graph(states):
        axes.clear()
        plot_fock_distribution(states[int(state.current())], fig=fig, ax=axes)
        canvas.draw()
    
    def close():
        root.destroy()
        quit()
    
    root.protocol("WM_DELETE_WINDOW", close)
    
    #start window
    root.mainloop()

if __name__ == "__main__":
    main()
