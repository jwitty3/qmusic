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
import os

def main():
    
    global notes, bassline, scales, states, root, sounds, afters, basssounds, bassbox, loopbox, fig, axes, canvas
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

    root = Tk()
    root.title('Quantum Music')

    pygame.mixer.init(size=32)
    sounds = []
    afters = []
    basssounds = []
    bassbox = IntVar()
    loopbox = IntVar()


    #generate data array by measuring a state
    def generate():
        dim = int(bignvalue.get())
        littlen = int(littlenvalue.get())

        global states
        states = [coherent(dim, np.sqrt(littlen)), basis(dim, n=littlen), fock(dim, n=littlen), thermal_dm(dim, littlen), maximally_mixed_dm(dim), phase_basis(dim, littlen), projection(dim, 2, 2)]
        operators = [create(dim),destroy(dim),displace(dim, 1),qeye(dim),momentum(dim),num(dim),phase(dim),position(dim),qzero(dim),tunneling(dim)]
        data = np.array([])

        graph()

        for i in range(int(length.get())):
            x = qm.measure(states[int(state.current())], operators[int(operator.current())])
            x = int(str(x[1].data)[3:4])
            data = np.append(data, x)

        sound(data)

    #play sounds
    def sound(state):
        cancelsound()

        playbutton.configure(command=cancelsound)
        playbutton['text'] = "Stop"

        bassindex = 0;
        bpm = int(speed.get())
        dur = 2.0
        fs = 44100
        global sounds
        global afters
        global basssounds
        sounds = []
        afters = []
        basssounds = []
        freqs = np.array([0])
        #indices of notes in notes array
        if scalebox.current() == -1:
            scale = np.fromstring(scalebox.get(), dtype=int, sep=",")
        else:
            scale = np.array(scales[scalebox.current()])

        #generate array of note frequencies in selected scale
        for i in range(int(max(state) + 1)):
            freq = notes[scale[i % scale.size]] * 2**np.floor(i / scale.size)
            freqs = np.append(freqs, freq)

        #generate sounds using pygame sounds
        for index in range(state.size):
            #to change the wave in the buffer variable, use "signal.square" or "np.sine" (or maybe "signal.sweep.poly") or "signal.sawtooth"
            t = 2 * np.pi * np.arange(fs * dur * 60 / bpm)
            buffer = signal.sawtooth(t * freqs[int(state[index])] / fs).astype(np.float32)
            sound = pygame.mixer.Sound(buffer)
            sounds.append(sound)
            afters.append(1)

        #generate bassline
        for index in range(int(bassline.size / 4)):
            bassarr = bassline[index]
            y = 2 * np.pi * np.arange(fs * bassarr[1] * 2 * 60 / bpm)
            buffer = np.sin(y * notes[int(bassarr[2])] * bassarr[3] / fs).astype(np.float32)
            bassbuffer = pygame.mixer.Sound(buffer)
            basssounds.append(bassbuffer)
            bassindex += 1

        interval = int(sounds[0].get_length() * 1000)

        #play sounds using recursive tkinter after()
        def playbass(bassind):
            basssounds[bassind].play()
            if bassind < len(basssounds) - 1:
                basssounds[bassind] = root.after(interval * int(bassline[bassind][0]), lambda : playbass(bassind + 1))

        def playnotes(ind):
            sounds[ind].play()
            if ind < len(sounds) - 1:
                afters[ind] = root.after(interval, lambda : playnotes(ind + 1))
            elif int(loopbox.get()) == 1:
                playnotes(0)
            else:
                cancelsound()

        playnotes(0)
        if int(bassbox.get()) == 1:
            playbass(0)

    #stop playing sounds
    def cancelsound():

        playbutton.configure(command=generate)
        playbutton['text'] = "Play"

        #get arrays of after objects
        global afters
        global basssounds

        #cancel all after objects
        for i in afters:
            root.after_cancel(i)
        for i in basssounds:
            root.after_cancel(i)

    #build widgets
    content = ttk.Frame(root)
    labels = ttk.Frame(content)
    inputs = ttk.Frame(content)
    title = ttk.Label(content, text="Quantum Music")
    bignvaluelabel = ttk.Label(labels, text="N")
    littlenvaluelabel = ttk.Label(labels, text="n")
    statelabel = ttk.Label(labels, text="State")
    operatorlabel = ttk.Label(labels, text="Operator")
    lengthlabel = ttk.Label(labels, text="Music Length")
    speedlabel = ttk.Label(labels, text="Speed")
    basslabel = ttk.Label(labels, text="Bassline")
    looplabel = ttk.Label(labels, text="Loop")
    scalelabel = ttk.Label(labels, text="Scale")
    bignvalue = ttk.Entry(inputs)
    littlenvalue = ttk.Entry(inputs)
    length = ttk.Entry(inputs)
    speed = ttk.Entry(inputs)
    bass = ttk.Checkbutton(inputs, variable=bassbox, onvalue=1, offvalue=0)
    loop = ttk.Checkbutton(inputs, variable=loopbox, onvalue=1, offvalue=0)
    scalebox = ttk.Combobox(inputs)
    scalebox['values'] = ('C Minor Pentatonic', 'C Major', 'C Blues')
    state = ttk.Combobox(inputs)
    state['values'] = ('Coherent', 'Basis', 'Fock', 'Thermal', 'maximally_mixed', 'phase_basis', 'projection')
    operator = ttk.Combobox(inputs)
    operator['values'] = ('Create', 'Destroy', 'Displace', 'Identity', 'Momentum', 'Num', 'Phase', 'Position', 'Zero', 'Tunneling')
    playbutton = ttk.Button(content, text="Play", command=generate)

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
    style.configure("TLabel", font=("Arial", 13))

    #display widgets
    content.pack(fill="both", expand=True)
    title.pack(pady=20)
    playbutton.pack(side="bottom", expand=True, pady=20, anchor="n")
    labels.pack(side="left", fill="both", expand=True)
    inputs.pack(side="left", fill="both", expand=True)
    bignvalue.pack(expand=True, anchor="e", padx=20, pady=10)
    littlenvalue.pack(expand=True, anchor="e", padx=20, pady=10)
    length.pack(expand=True, anchor="e", padx=20, pady=10)
    speed.pack(expand=True, anchor="e", padx=20, pady=10)
    bass.pack(expand=True, anchor="e", padx=20, pady=10)
    loop.pack(expand=True, anchor="e", padx=20, pady=10)
    scalebox.pack(expand=True, anchor="e", padx=20, pady=10)
    state.pack(expand=True, anchor="e", padx=20, pady=10)
    operator.pack(expand=True, anchor="e", padx=20, pady=10)
    bignvaluelabel.pack(expand=True, anchor="e", padx=20, pady=10)
    littlenvaluelabel.pack(expand=True, anchor="e", padx=20, pady=10)
    lengthlabel.pack(expand=True, anchor="e", padx=20, pady=10)
    speedlabel.pack(expand=True, anchor="e", padx=20, pady=10)
    basslabel.pack(expand=True, anchor="e", padx=20, pady=10)
    looplabel.pack(expand=True, anchor="e", padx=20, pady=10)
    scalelabel.pack(expand=True, anchor="e", padx=20, pady=10)
    statelabel.pack(expand=True, anchor="e", padx=20, pady=10)
    operatorlabel.pack(expand=True, anchor="e", padx=20, pady=10)
    
    fig, axes = plt.subplots(figsize=(5, 5))
    plot_fock_distribution(states[int(state.current())], fig=fig, ax=axes)
    canvas = FigureCanvasTkAgg(fig, master = content)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True, padx=20)

    def graph():
        global fig
        global axes
        global canvas

        axes.clear()
        plot_fock_distribution(states[int(state.current())], fig=fig, ax=axes)
        canvas.draw()
    
    def close():
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", close)
    
    #start window
    root.mainloop()

if __name__ == "__main__":
    main()
