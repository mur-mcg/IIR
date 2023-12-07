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

    def __init__(self, title):
        self.pw = pg.PlotWidget()
        self.pw.setYRange(-1,1)
        self.pw.setXRange(0,500/fs)
        self.plt = self.pw.plot()
        self.data = []
        # any additional initalisation code goes here (filters etc)
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

class QtIntPlot:

    def __init__(self, title):
        self.pw = pg.PlotWidget()
        self.pw.setYRange(-90,90)
        self.pw.setXRange(0,500/fs)
        self.plt = self.pw.plot()
        self.data = []
        # any additional initalisation code goes here (filters etc)
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(100)

    def getWidget(self):
        return self.pw
        
    def update(self):
        self.data = self.data[-500:]
        if self.data:
            self.plt.setData(x=np.linspace(0,len(self.data)/fs,len(self.data)),y=self.data)

    def addData(self,d):
        self.data.append(d)

class callBack:
    
    def __init__(self, iir1, iir2, iir3):
        self.raw = []
        self.filtered = []
        self.buff = np.zeros(100)
        self.tnow = 0
        self.tlast = 0
        self.tdiff = np.zeros(100)
        self.last = 0
        self.iir1 = iir1
        self.iir2 = iir2
        self.iir3 = iir3
        self.rawplot = QtPanningPlot('Raw Data')
        self.filtplot = QtPanningPlot('Filtered Data')
        self.i = 0
        #self.sr = pg.ValueLabel(suffix = "Hz", siPrefix=True, averageTime= 5)
        self.sr = pg.TextItem(text='', color=(200, 200, 200))
        self.parameter = 0


    def sample(self, data):
        self.tnow = time.perf_counter()
#        if self.tlast != 0: self.tdiff[self.i % 100] = self.tnow - self.tlast
        #print(self.tnow - self.tlast)
        #self.sr.setValue(1 / (self.tnow - self.tlast))
        self.tlast = self.tnow
#        if self.i % 100 == 0:
#            self.sr.setValue(1 / np.mean(self.tdiff))
#        self.raw.append(data)
        self.rawplot.addData(data)
        data = self.dofilter(data)
        if data > 0.1 or data < -0.1:
            data = self.last
        self.last = data
        self.filtplot.addData(data)

        pitch = (np.arctan2(np.negative(callBack2.last), np.sqrt(callBack3.last * callBack3.last + callBack1.last * callBack1.last))) * (180 / np.pi) - 10
        if self == callBack1: print("x")
        if self == callBack2: print("y")
        if self == callBack3: print("z")
        pitchplot.addData(pitch)
        if self == callBack1:
            self.buff = np.roll(self.buff, 1)
            self.buff[0] = pitch
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
            cc = [0xBF, 70, self.parameter]
            midiout.send_message(cc)
            print(cc)
            paramplot.addData(self.parameter)
        self.i += 1


    def dofilter(self, v):

        output = self.iir2.filter(v)
        output = self.iir3.filter(output)
        return output

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
midiout = rtmidi.MidiOut()
available_ports = midiout.get_ports()
for port in available_ports:
    print(port)
if available_ports:
    midiout.open_port(1)

PORT = Arduino.AUTODETECT

fs = 1000
f0 = 48.0
f1 = 52.0
f2 = 200
f3 = 450
sos1 = signal.butter(4, [f0,f1], 'bandstop', output='sos', fs=fs)
sos2 = signal.butter(4, f2, 'highpass', output='sos', fs=fs)
sos3 = signal.butter(4, f3, 'lowpass', output='sos', fs=fs)

iir1 = iir_filter.IIR_filter(sos1)
iir2 = iir_filter.IIR_filter(sos2)
iir3 = iir_filter.IIR_filter(sos3)

app = pg.mkQApp()
mw = QtWidgets.QMainWindow()
mw.setWindowTitle('100Hz dual PlotWidget')
mw.resize(2000,1200)
cw = QtWidgets.QWidget()
mw.setCentralWidget(cw)

layout = QtWidgets.QGridLayout()
cw.setLayout(layout)

callBack1 = callBack(iir1, iir2, iir3)
callBack2 = callBack(iir1, iir2, iir3)
callBack3 = callBack(iir1, iir2, iir3)
paramplot = QtIntPlot("Message")
pitchplot = QtIntPlot("Message")

layout.addWidget(callBack1.rawplot.getWidget(), 0, 0)
layout.addWidget(callBack2.rawplot.getWidget(), 0, 1)
layout.addWidget(callBack3.rawplot.getWidget(), 0, 2)
layout.addWidget(callBack1.filtplot.getWidget(), 1, 0)
layout.addWidget(callBack2.filtplot.getWidget(), 1, 1)
layout.addWidget(callBack3.filtplot.getWidget(), 1, 2)
layout.addWidget(pitchplot.getWidget(), 2, 0)
layout.addWidget(paramplot.getWidget(), 2, 1)

board = Arduino(PORT)
board.samplingOn(1000 / fs)

board.analog[0].register_callback(callBack1.sample)
board.analog[1].register_callback(callBack2.sample)
board.analog[2].register_callback(callBack3.sample)

board.analog[0].enable_reporting()
board.analog[1].enable_reporting()
board.analog[2].enable_reporting()

mw.show()

pg.exec()
board.exit()
#print(np.average(callBack1.filtered))
plotter(callBack1.raw, callBack2.raw, callBack3.raw, 
        callBack1.filtered, callBack2.filtered, callBack3.filtered)