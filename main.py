import numpy as np
import time
from pyfirmata2 import Arduino
import iir_filter
from scipy import signal
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtWidgets
import matplotlib.pyplot as plt
import rtmidi


class QtPanningPlot:

    def __init__(self, title, y1, y2):
        self.pw = pg.PlotWidget()
        self.pw.setYRange(y1,y2)
        self.pw.setXRange(0,500/fs)
        self.plt = self.pw.plot()
        self.data = []
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(100)

    def getWidget(self):
        return self.pw
        
    def update(self):
        self.data=self.data[-500:]
        if self.data:
            self.plt.setData(x=np.linspace(0,len(self.data)/fs,len(self.data)),y=self.data)

    def addData(self,d):
        self.data.append(d)


class callBack:
    
    def __init__(self, iir1, iir2):
        self.raw = []
        self.filtered = []
        self.buff = np.zeros(100)
        self.current_t = 0
        self.prev_t = 0
        self.data = 0
        self.iir1 = iir1
        self.iir2 = iir2
        self.rawplot = QtPanningPlot('Raw Data', -1, 1)
        self.filtplot = QtPanningPlot('Filtered Data', -1, 1)
        self.i = 0
        #self.sr = pg.ValueLabel(suffix = "Hz", siPrefix=True, averageTime= 5)
        self.parameter = 0

    def sample(self, data):

        #Calculate time per 1000 samples
        if self.i % 1000 == 0:
            self.current_t = time.perf_counter()
            #print((1 / ((self.current_t - self.prev_t)/1000)))
            self.prev_t = self.current_t
        #Store and filter data, add to plots
        self.data = data
        self.raw.append(data)
        self.rawplot.addData(data)
        data = self.dofilter(data)
        self.filtered.append(data)
        self.filtplot.addData(data)
        #Calculate roll angle
        if self == callBack2:
            self.calculate_roll()
        self.i += 1

    def dofilter(self, v):

        output = self.iir1.filter(v)
        output = self.iir2.filter(output)
        return output
    def calculate_roll(self):

        roll = np.arctan2(callBack2.data,callBack1.data) * (180 / np.pi)
        #print(roll)
        rollplot.addData(roll)
        self.buff[self.i % 100] = roll


        if self.i % 100 == 0:
            if np.mean(self.buff) > 10:
                if self.parameter < 127:
                    self.parameter += 1
            elif np.mean(self.buff) < -10:
                if self.parameter > 0:
                    self.parameter -= 1
            elif np.mean(self.buff) > 20:
                if self.parameter < 127:
                    self.parameter += 10
            elif np.mean(self.buff) < -20:
                if self.parameter > 0:
                    self.parameter -= 10
            elif np.mean(self.buff) > 30:
                if self.parameter < 127:
                    self.parameter += 50
            elif np.mean(self.buff) < -30:
                if self.parameter > 100:
                    self.parameter -= 50

            msg = [midichannel, midicc, self.parameter]
            if available_ports:
                midiout.send_message(msg)
                print(msg)
            else:
                print(self.parameter)
            paramplot.addData(self.parameter)


def plotter(r1 ,r2, r3, f1, f2, f3):

    plt.figure(1, figsize=[12.8, 8], layout = "compressed")
    def subplotterraw(data, index):
        plt.figure(1, figsize=[12.8, 9.6])
        plt.subplot(1,3,index)
        plt.magnitude_spectrum(callBack1.raw, Fs = 1000, scale = 'dB',window=None, color = '#0044ff', linewidth=0.3)
        plt.title('Frequency Spectrum of Input Data')
        plt.xlabel('Frequency (Hz)')
        plt.xscale('log')
        plt.xlim(0.1, 500)
        plt.ylabel('Gain (dB)')
        plt.legend(["Raw","Filtered"])
    
    def subplotterfilt(data, index):
        plt.subplot(1,3,index)
        plt.magnitude_spectrum(callBack2.filtered, Fs = 1000, scale = 'dB',window=None, color = '#ff007b', linewidth=0.3)
        plt.title('Frequency Spectrum of Filtered Data')
        plt.xlabel('Frequency (Hz)')
        plt.xscale('log')
        plt.xlim(0.1, 500)
        plt.ylabel('Gain (dB)')
        plt.legend(["Raw","Filtered"])
    subplotterraw(r1,1)
    subplotterraw(r2,2)
    subplotterraw(r3,3) 
    subplotterfilt(f1,1)
    subplotterfilt(f2,2)
    subplotterfilt(f3,3)
    plt.show()
def midimenu(ports):

    channel = 0
    cc = 0
    for port in available_ports:
        print(port)
    while True:
        selection = int(input("Enter MIDI port number:"))
        if selection in range(0, len(available_ports)):
            midiout.open_port(selection)
            break
        else: print("Invalid input./n")
    while True:
        selection = int(input("Enter MIDI Channel (1-16):"))
        if selection in range(1, 17):
            channel = 0xB << 4 | selection - 1
            break
        else: print("Invalid input./n")
    while True:
        selection = int(input("Enter MIDI CC Destination (0-127):"))
        if selection in range(0, 127):
            cc = selection
            break
        else: print("Invalid input./n")

    return channel, cc


#MIDI Initialisation
try: 
    midiout = rtmidi.MidiOut()
    available_ports = midiout.get_ports()
except :
    print("No MIDI available: Output will print to terminal")

if available_ports:
    midichannel, midicc = midimenu(available_ports)
else:
    print("No MIDI available: Output will print to terminal")

#Filter and Callback Initialisation
fs = 1000
f1 = 1
f2 = 450
sos1 = signal.butter(1, f1, 'highpass', output='sos', fs=fs)
sos2 = signal.butter(4, f2, 'lowpass', output='sos', fs=fs)
iir1 = iir_filter.IIR_filter(sos1)
iir2 = iir_filter.IIR_filter(sos2)


#UI Initialisation
app = pg.mkQApp()
mw = QtWidgets.QMainWindow()
mw.setWindowTitle('100Hz dual PlotWidget')
mw.resize(2000,1200)
cw = QtWidgets.QWidget()
mw.setCentralWidget(cw)
layout = QtWidgets.QGridLayout()
cw.setLayout(layout)


#Define Callbacks and Plot Widgets, add plots to layout
callBack1 = callBack(iir1, iir2)
callBack2 = callBack(iir1, iir2)
paramplot = QtPanningPlot("Message", 0, 127)
rollplot = QtPanningPlot("Message", -180, 180)

layout.addWidget(callBack1.rawplot.getWidget(), 0, 0)
layout.addWidget(callBack2.rawplot.getWidget(), 0, 1)
layout.addWidget(callBack1.filtplot.getWidget(), 1, 0)
layout.addWidget(callBack2.filtplot.getWidget(), 1, 1)
layout.addWidget(rollplot.getWidget(), 2, 0)
layout.addWidget(paramplot.getWidget(), 2, 1)

#Arduino sampling initialisation
PORT = Arduino.AUTODETECT
board = Arduino(PORT)
board.samplingOn(1000 / fs)

analog_in_x = board.get_pin('a:1:i')
analog_in_z = board.get_pin('a:2:i')
analog_in_x.register_callback(callBack1.sample)
analog_in_z.register_callback(callBack2.sample)
analog_in_x.enable_reporting()
analog_in_z.enable_reporting()

mw.show()
pg.exec()
board.exit()


plotter(callBack1.raw, callBack2.raw, callBack2.raw, 
        callBack1.filtered, callBack2.filtered, callBack2.filtered)

with open ("raw_x.csv","w") as file:
    for sample in callBack1.raw:
        file.write(str(sample)+"\n")

with open ("raw_z.csv","w") as file:
    for sample in callBack2.raw:
        file.write(str(sample)+"\n")