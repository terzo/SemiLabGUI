import tkinter as tk
import tkinter.font as tkFont
from keithley import *
import math
import time

import threading

def mean(array):
    #straight foward!
    return 1.0*sum(array)/len(array)

def std_dev(array):
    #also quite easy
    return math.sqrt(1.0*(sum([(x-mean(array))**2 for x in array])/len(array)))

def isfloat(value):
    try:
        float(value)
        return True
    except ValueError:
        return False

def isint(value):
    try:
        int(value)
        return True
    except ValueError:
        return False

class StatusFrame(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent

        self.var_status = tk.StringVar()
        tk_statuslabel = tk.Label(self, text="Status:", anchor=tk.NW)
        tk_statuslabel.pack(side=tk.TOP, fill=tk.X)
        tk_status = tk.Label(self, textvariable=self.var_status, relief=tk.SUNKEN)
        tk_status.pack(side=tk.TOP, fill=tk.X)

    def set_status(self, status):
        self.var_status.set(status)

class ValueFrame(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent

        self.volt_value = tk.StringVar()
        self.volt_value.set("0.0")

        tk_label = tk.Label(self, text="Voltage: ")
        tk_label.grid(row=0, column=0, sticky=tk.W)
        tk_value = tk.Label(self, textvariable=self.volt_value, anchor=tk.E, relief=tk.SUNKEN, width=10, font=tkFont.Font(size=18))
        tk_value.grid(row=0, column=1, sticky=(tk.E, tk.W))

        tk_label = tk.Label(self, text="Current: ")
        tk_label.grid(row=1, column=0, sticky=tk.W)
        self.curr_value = tk.StringVar()
        tk_value = tk.Label(self, textvariable=self.curr_value, anchor=tk.E, relief=tk.SUNKEN, width=10,font=tkFont.Font(size=18))
        tk_value.grid(row=1, column=1, sticky=(tk.E, tk.W))

        tk_label = tk.Label(self, text="Current Limit: ")
        tk_label.grid(row=2, column=0, sticky=tk.W)
        self.currLimit_value = tk.StringVar()
        tk_value = tk.Label(self, textvariable=self.currLimit_value, anchor=tk.E, relief=tk.SUNKEN, width=10,font=tkFont.Font(size=18) )
        tk_value.grid(row=2, column=1, sticky=(tk.E, tk.W))

        self.columnconfigure(1, weight=1)
        self.pack(fill=tk.BOTH)

class CurrentFrame(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent

        # add setting for the current limit
        tk_label_up = tk.Label(self, text="Limit")
        tk_label_up.grid(row = 0, column = 1, sticky=(tk.W))
        tk_label_up = tk.Label(self, text="Range")
        tk_label_up.grid(row = 0, column = 3, sticky=(tk.W))
        tk_labelcurrlim = tk.Label(self, text="Set Current: ", width=12)
        tk_labelcurrlim.grid(row =1, column = 0, rowspan = 1, sticky=(tk.E,tk.W))
        self.currentLimit_var = tk.StringVar()
        self.tk_setCL = tk.Spinbox(self, from_=1e-9, to=1e-3, textvariable=self.currentLimit_var, increment=10e-6, width=17)
        self.tk_setCL.config(validate = 'key', validatecommand = parent.vfloat)
        self.tk_setCL.grid(row = 1, column = 1, columnspan=2, sticky=(tk.E,tk.W))
        currentRange_var = tk.StringVar()
        currentRange_var.set(10e-6)
        self.tk_setCR = tk.Spinbox(self, values=(10e-5,10e-6,10e-7,10e-8,10e-9), textvariable=currentRange_var, width=17)
        self.tk_setCR.config(validate = 'key', validatecommand = parent.vfloat)
        self.tk_setCR.grid(row = 1, column = 3, columnspan=2, sticky=(tk.E,tk.W))
        tk_setlimit = tk.Button(self, text="Set", command=self.set_clicked,padx=20, pady=10)
        tk_setlimit.grid(row = 0, column = 5, rowspan=2, sticky=(tk.E))

    def set_clicked(self):
        """Set the target voltage"""
        try:
            # if we cannot convert the value to float we don't do anything
            curr = float(self.currentLimit_var.get())
            self.currentLimit_var.set(curr)
        except ValueError:
            return

    def set_currentlimit(self,current):
        self.currentLimit_var.set(10e-6)

class RampFrame(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent

        # add setting for the ramping
        tk_label_up = tk.Label(self, text="Step up")
        tk_label_up.grid(row = 0, column = 1, sticky=(tk.W))
        tk_label_up = tk.Label(self, text="Step down")
        tk_label_up.grid(row = 0, column = 2, sticky=(tk.W))
        tk_label_up = tk.Label(self, text="Step wait")
        tk_label_up.grid(row = 0, column = 3, sticky=(tk.W))
        tk_label_up = tk.Label(self, text="nAverage")
        tk_label_up.grid(row = 0, column = 4, sticky=(tk.W))
        tk_labelramp = tk.Label(self, text="Ramping options: ")
        tk_labelramp.grid(row = 1, column = 0, sticky=(tk.W))
        self.stepSizeUp_var = tk.StringVar()
        self.stepSizeUp_var.set(1.0)
        self.stepSizeDown_var = tk.StringVar()
        self.stepSizeDown_var.set(5.0)
        self.stepWait_var = tk.StringVar()
        self.stepWait_var.set(0.5)
        self.nAverage_var = tk.StringVar()
        self.nAverage_var.set(10)
        tk_setStepSizeUp = tk.Spinbox(self, from_=1, to=10, textvariable=self.stepSizeUp_var, increment=1, width=7)
        tk_setStepSizeUp.config(validate = 'key', validatecommand = parent.vfloat)
        tk_setStepSizeUp.grid(row = 1, column = 1, sticky=(tk.E,tk.W))
        tk_setStepSizeDown = tk.Spinbox(self, from_=1, to=10, textvariable=self.stepSizeDown_var, increment=1, width=7)
        tk_setStepSizeDown.config(validate = 'key', validatecommand = parent.vfloat)
        tk_setStepSizeDown.grid(row = 1, column = 2, sticky=(tk.E,tk.W))
        tk_setStepWait = tk.Spinbox(self, from_=0.0, to=60.0, textvariable=self.stepWait_var, increment=0.1,width=7)
        tk_setStepWait.config(validate = 'key', validatecommand = parent.vfloat)
        tk_setStepWait.grid(row = 1, column = 3, sticky=(tk.E,tk.W))
        tk_setnAverage = tk.Spinbox(self, from_=1, to=1000.0, textvariable=self.nAverage_var, increment=1,width=7)
        tk_setnAverage.config(validate = 'key', validatecommand = parent.vint)
        tk_setnAverage.grid(row = 1, column = 4, sticky=(tk.E,tk.W))
        # add setting for voltage
        tk_labelvolt = tk.Label(self, text="Set voltage: ")
        tk_labelvolt.grid(row = 3, column = 0,sticky=(tk.E,tk.W))
        self.startV_var = tk.StringVar()
        self.startV_var.set(0.0)
        self.volt_var = tk.StringVar()
        self.volt_var.set(0.0)
        self.idletime_var = tk.StringVar()
        self.idletime_var.set(0.0)
        tk_label_vstart = tk.Label(self, text="Start")
        tk_label_vstart.grid(row = 2, column = 1, sticky=(tk.W))
        tk_label_vstop = tk.Label(self, text="Stop")
        tk_label_vstop.grid(row = 2, column = 2, sticky=(tk.W))
        tk_label_vstop = tk.Label(self, text="Idle")
        tk_label_vstop.grid(row = 2, column = 4, sticky=(tk.W))
        tk_startV = tk.Spinbox(self, from_=-1100, to=0.0, textvariable=self.startV_var, width=1)
        tk_startV.config(validate = 'key', validatecommand = parent.vfloat)
        tk_startV.grid(row = 3, column = 1, columnspan = 1,  sticky=(tk.E,tk.W))

        tk_stopV = tk.Spinbox(self, from_=-1100, to=0.0, textvariable=self.volt_var, width=1)
        tk_stopV.config(validate = 'key', validatecommand = parent.vfloat)
        tk_stopV.grid(row = 3, column = 2, columnspan = 2,  sticky=(tk.E,tk.W))
        tk_idle = tk.Spinbox(self, from_=0, to=1e6, textvariable=self.idletime_var, width=1)
        tk_idle.config(validate = 'key', validatecommand = parent.vfloat)
        tk_idle.grid(row = 3, column = 4, columnspan = 1,  sticky=(tk.E,tk.W))
        self.tk_setvolt = tk.Button(self, text="Ramp\nVoltage", command=self.ramp_clicked, padx=12, pady=15, height = 3, width = 5, state=tk.DISABLED)
        self.tk_setvolt.grid(row = 0, column = 5, rowspan =4, sticky=(tk.E,tk.W,tk.S))
        self.pack(fill=tk.X)

    def ramp_clicked(self):
        if self.tk_setvolt["text"]=="Stop":
            self.parent.abort=True
            return
        else:
            self.parent.abort=False
            self.tk_setvolt["text"]="Stop"

        threading.Thread(target=self.parent.set_voltage,args=()).start()

class SaveFrame(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent

        self.folder_path = tk.StringVar()
        path_entry = tk.Entry(master=self,textvariable=self.folder_path)
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        browse_button = tk.Button(self, text="Browse", command=self.browse_clicked)
        browse_button.pack(side=tk.RIGHT, fill=tk.X)
        save_button = tk.Button(self, text="Save", command=self.savedata_clicked)
        save_button.pack(side=tk.RIGHT, fill=tk.X)

    def browse_clicked(self):
        # Allow user to select a directory and store it in global var
        # called folder_path
        filename = tk.filedialog.asksaveasfilename(initialfile=self.folder_path.get(), defaultextension=".txt")
        self.folder_path.set(filename)

    def savedata_clicked(self):
        # #create directory
        # data["OutputFolder"]=os.path.dirname(folder_path.get())
        # #data["OutputFolder"]+=os.sep+data["StructureName"]
        # items=data["OutputFolder"].split(os.sep)
        # growing=""
        # for item in items:
        #     growing+=item+os.sep
        #     if not os.path.isdir(growing):
        #         os.mkdir(growing)
        #create full filename
        fullfilename=self.folder_path.get()
        #fullfilename=data["OutputFolder"]+os.sep+data["options"]["Measurement"]+"_"+data["StructureName"]+"_"+mytime
        #save png image
        #data["canvas"].SaveAs(fullfilename+".png")
        #writing to file
        file=open(fullfilename,'w')
        self.parent.write_header(file)

        data = self.parent.data
        for i in range(len(data["data"]["x"])):
            file.write("%e %e " % (data["data"]["x"][i],data["data"]["xdev"][i]))
            for j in range(1,data["ycount"]+1):
                file.write("%e %e " % (data["data"]["y%d" % j][i],data["data"]["y%ddev" % j][i]))
            #file.write("%.1f %.1f\n" % (data["data"]["temp"][i],data["data"]["humid"][i]))
            file.write("%.1f\n" % (data["data"]["time"][i]))
        file.close()
        return

class BottomFrame(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent

        # add setting for the gpib
        tk_labelgpib = tk.Label(self, text="GPIB address: ")
        tk_labelgpib.pack(side=tk.LEFT)
        self.gpib_value = tk.StringVar()
        self.gpib_value.set(18)
        tk_setGPIB = tk.Spinbox(self, from_=1, to=30, textvariable=self.gpib_value, width=5, font=tkFont.Font(size=10))
        tk_setGPIB.config(validate = 'key', validatecommand = parent.vint)
        tk_setGPIB.pack(fill=tk.BOTH, side=tk.LEFT, expand=True)
        tk_connectGPIB = tk.Button(self, text="Connect", command=self.set_gpib,padx=20, pady=2)
        tk_connectGPIB.pack(side=tk.LEFT)
        # and finally add a close button
        tk_close = tk.Button(self, text="Close", command=self.close_clicked,padx=20, pady=2)
        tk_close.pack(side=tk.RIGHT)

    def close_clicked(self):
        self.parent.data.clear()
        if self.parent.ky.connected:
            self.parent.ramp_down()
            #leave program running until enter is pressed
            self.parent.ky.write("trace:clear; feed:control next")
        self.parent.parent.quit()

    def set_gpib(self):
        #initialize and identify
        #print(tk_setGPIB.get())
        currentlimit = float(self.parent.currentframe.tk_setCR.get())
        self.parent.ky.connect(int(self.gpib_value.get()),currentlimit)
        if self.parent.ky.connected:
            self.parent.statusframe.set_status("connected to GPIB::%i" % int(self.gpib_value.get()))
            self.parent.currentframe.tk_setCR.config(state=tk.DISABLED)
            self.parent.currentframe.tk_setCL.config(to=self.parent.currentframe.tk_setCR.get())
            self.parent.rampframe.tk_setvolt.config(state=tk.NORMAL)
        else:
            self.parent.statusframe.set_status("connection failed")

class KeithleyGUI(tk.Frame):
    verbose=True
    #verbose=False

    abort=True
    data={}
    #here the data is stored
    data["data"]={}

    data={}
    #here the data is stored
    data["data"]={}
    #here are the options that are also written to file
    data["options"]={}

    #define temp arrays for averaging later on
    tempcurr = 0.0
    temptemp = 0.0
    temphumid = 0.0
    #Run gui

    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent

        # registering validation command
        self.vfloat = (self.register(self.validate_float),'%P', '%W')
        self.vint = (self.register(self.validate_int), '%P', '%W')

        self.ky = keithley()
        self.plot = None
        self.starttime = time.time()
        self.data["StartTime"]=time.time()
        self.data["CurrentTime"]=time.time()
        # now add the text field showing the status info. we use a Tk variable to keep
        # the status message so we can update it easily
        separator = tk.Frame(self.parent, height=2, bd=1, relief=tk.SUNKEN)
        separator.pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5)

        self.statusframe = StatusFrame(self)
        self.statusframe.pack(side=tk.TOP, fill=tk.X)
        self.statusframe.set_status("disconnected")

        self.valueframe = ValueFrame(self)
        self.valueframe.pack(fill=tk.BOTH)

        separator = tk.Frame(self, height=2, bd=1, relief=tk.SUNKEN)
        separator.pack(fill=tk.X, padx=5, pady=5)

        self.currentframe = CurrentFrame(self)
        self.currentframe.pack(fill=tk.X)
        self.currentframe.set_currentlimit(10e-6)

        separator = tk.Frame(self, height=2, bd=1, relief=tk.SUNKEN)
        separator.pack(fill=tk.X, padx=5, pady=5)

        self.rampframe = RampFrame(self)

        separator = tk.Frame(self, height=2, bd=1, relief=tk.SUNKEN)
        separator.pack(fill=tk.X, padx=5, pady=5)

        self.saveframe = SaveFrame(self)
        self.saveframe.pack(fill=tk.X)

        separator = tk.Frame(self, height=2, bd=1, relief=tk.SUNKEN)
        separator.pack(fill=tk.X, padx=5, pady=5)

        self.bottomframe = BottomFrame(self)
        self.bottomframe.pack(side=tk.BOTTOM, fill=tk.X)

    def setplot(self, plot):
        self.plot = plot

    def ramp_down(self):
        self.ramp(float(self.valueframe.volt_value.get()),0.0,float(self.currentframe.tk_setCL.get()),float(self.rampframe.stepSizeDown_var.get()),0.1,True)

        self.ky.output_off()
        self.rampframe.tk_setvolt["text"]="Ramp\nVoltage"

    def ramp(self,start,stop,currentlimit,stepsize=1.,wait=0.,force=False):
        #does the actual ramping
        #first get the right array
        voltages=self.ky.get_ramparray(start,stop,stepsize)
        #then ram through the array
        for v in voltages:
            self.ky.set_voltage(v)
            self.valueframe.volt_value.set(v)
            if not force:
                #check for current limit unless ramping is forced
                if abs( self.ky.read()["current"]) > abs(currentlimit) or self.abort is True:
                    print("Current Limit while ramping!! Switching off!")
                    #force shutdown!
                    self.ramp(v,0.0,currentlimit,stepsize,wait,True)
                    #keithley switched off
                    #so return to caller
                    return
            time.sleep(wait)
        return

    def idle(self, file):

        current_limit = float(self.currentframe.tk_setCL.get())
        settle_time = float(self.rampframe.stepWait_var.get())

        try:
            nAverage = int(self.rampframe.nAverage_var.get())
        except ValueError:
            print("Cannot convert to int")
            return

        try:
            idletime = int(self.rampframe.idletime_var.get())
        except ValueError:
            print("Cannot convert to int")
            return

        idlestarttime=time.time()
        curidletime = time.time() - idlestarttime

        print("Starting idle measurement")
        while curidletime<idletime:
            print("Current time is:")
            print(curidletime)
            #define temp arrays for averaging later on
            tempvolt=[]
            tempcurrs=[]
            temptemps=[]
            temphumids=[]
            #wait for the currents to settle
            print("Waiting %.1f seconds..." % (settle_time))
            time.sleep(settle_time)
            print("measuring...")
            for i in range(nAverage):
                output=self.ky.read()
                #check everytime for current limit
                if abs(output["current"])>abs(current_limit):
                    print("CURRENT LIMIT! Ramping down!")
                    self.data["EndMessage"]="CURRENT LIMIT! Ramping down!"
                    abort=True
                    break
                #fill the temp values
                tempvolt.append(output["voltage"])
                tempcurrs.append(output["current"])
                temptemps.append(output["temperature"])
                temphumids.append(output["humid"])
            #if current limit is reached
            if self.abort:
                print("Run Stopped.")
                break

            curidletime = time.time()-idlestarttime
            curtime = time.time()-self.starttime
            #fill the real values
            self.data["data"]["time"].append(curtime)
            self.data["data"]["x"].append(mean(tempvolt))
            self.data["data"]["xdev"].append(std_dev(tempvolt))
            self.data["data"]["y1"].append(mean(tempcurrs))
            self.data["data"]["y1dev"].append(std_dev(tempcurrs))
            self.data["data"]["temp"].append(mean(temptemps))
            self.data["data"]["tempdev"].append(std_dev(temptemps))
            self.data["data"]["humid"].append(mean(temphumids))
            self.data["data"]["humiddev"].append(std_dev(temphumids))
            #for screen control
            print("Voltage %f, Mean: %.3e, StdDev: %.3e, Temp: %.1f, Humid: %.1f" %
                  (self.data["data"]["x"][-1],self.data["data"]["y1"][-1],self.data["data"]["y1dev"][-1],self.data["data"]["temp"][-1],self.data["data"]["humid"][-1]))
            self.valueframe.volt_value.set(self.data["data"]["x"][-1])
            self.valueframe.curr_value.set(self.data["data"]["y1"][-1])

            if file is not None:
                file.write("%e %e " % (self.data["data"]["x"][-1],self.data["data"]["xdev"][-1]))
                file.write("%e %e " % (self.data["data"]["y1"][-1],self.data["data"]["y1dev"][-1]))
                file.write("%e\n" % (self.data["data"]["time"][-1]))

            if curtime>idletime:
                self.data["EndMessage"]="Reached time limit without problems!"

            if self.plot is not None:
                self.plot.ax.set_title('I - T')
                self.plot.ax.errorbar(self.data["data"]["time"],self.data["data"]["y1"],xerr=self.data["data"]["xdev"],yerr=self.data["data"]["y1dev"])
                self.plot.canvas.draw()
                self.plot.ax.clear()

    def set_voltage(self):
        try:
            # if we cannot convert the value to float we don't do anything
            start_volt = float(self.rampframe.startV_var.get())
        except ValueError:
            print("Cannot convert to float")
            return
        # ramp to target start voltage 1
        try:
            currV = self.ky.read()["voltage"]
        except:
            print("Cannot read voltage")
            return
        if start_volt>0.0:
            print("WARNING: positive starting value")
            return

        try:
            # if we cannot convert the value to float we don't do anything
            volt = float(self.rampframe.volt_var.get())
        except ValueError:
            print("Cannot convert to float")
            return
            # ramp to target voltage 1
        try:
            currV = self.ky.read()["voltage"]
        except:
            print("Cannot read voltage")
            return
        if volt>0.0:
            print("WARNING: positive value")
            return

        if volt<currV:
            step = float(self.rampframe.stepSizeUp_var.get())
        else:
            step = float(self.rampframe.stepSizeDown_var.get())

        self.ky.output_on()

        self.ramp(currV,start_volt,float(self.currentframe.tk_setCL.get()),step,0.5,False)

        #here all the values are stored
        self.data["data"]["time"]=[]
        self.data["data"]["x"]=[]
        self.data["data"]["xdev"]=[]
        self.data["ycount"]=1
        self.data["data"]["y1"]=[]
        self.data["data"]["y1dev"]=[]
        self.data["data"]["temp"]=[]
        self.data["data"]["tempdev"]=[]
        self.data["data"]["humid"]=[]
        self.data["data"]["humiddev"]=[]

        #get the array of voltages for the measurements
        allvoltages=self.ky.get_ramparray(start_volt,volt,step)

        settle_time = float(self.rampframe.stepWait_var.get())
        current_limit = float(self.currentframe.tk_setCL.get())

        try:
            nAverage = int(self.rampframe.nAverage_var.get())
        except ValueError:
            print("Cannot convert to int")
            return

        fullfilename=self.saveframe.folder_path.get()
        file = None
        try:
            file=open(fullfilename,'w')
        except:
            print("WARNING: file name not valid. Data will not be saved.")

        self.starttime = time.time()

        for voltage in allvoltages :
            #power to the right voltage
            #ky.write(":SOUR:VOLT %.3f" % (voltage))
            self.ky.set_voltage(voltage)
            self.valueframe.volt_value.set(voltage)
            #define temp arrays for averaging later on
            tempcurrs=[]
            temptemps=[]
            temphumids=[]
            #wait for the currents to settle
            print("Waiting %.1f seconds..." % (settle_time))
            time.sleep(settle_time)
            print("measuring...")
            for i in range(nAverage):
                output=self.ky.read()
                #check everytime for current limit
                if abs(output["current"])>abs(current_limit):
                    print("CURRENT LIMIT! Ramping down!")
                    self.data["EndMessage"]="CURRENT LIMIT! Ramping down!"
                    abort=True
                    break
                #fill the temp values
                tempcurrs.append(output["current"])
                temptemps.append(output["temperature"])
                temphumids.append(output["humid"])
            #if current limit is reached
            if self.abort:
                print("Run Stopped.")
                break

            curtime = time.time()-self.starttime
            #fill the real values
            self.data["data"]["time"].append(curtime)
            self.data["data"]["x"].append(voltage)
            self.data["data"]["xdev"].append(0.0)
            self.data["data"]["y1"].append(mean(tempcurrs))
            self.data["data"]["y1dev"].append(std_dev(tempcurrs))
            self.data["data"]["temp"].append(mean(temptemps))
            self.data["data"]["tempdev"].append(std_dev(temptemps))
            self.data["data"]["humid"].append(mean(temphumids))
            self.data["data"]["humiddev"].append(std_dev(temphumids))
            #for screen control
            print("Voltage %f, Mean: %.3e, StdDev: %.3e, Temp: %.1f, Humid: %.1f" % (self.data["data"]["x"][-1],self.data["data"]["y1"][-1],self.data["data"]["y1dev"][-1],self.data["data"]["temp"][-1],self.data["data"]["humid"][-1]))
            self.valueframe.volt_value.set(self.data["data"]["x"][-1])
            self.valueframe.curr_value.set(self.data["data"]["y1"][-1])

            if file is not None:
                file.write("%e %e " % (self.data["data"]["x"][-1],self.data["data"]["xdev"][-1]))
                file.write("%e %e " % (self.data["data"]["y1"][-1],self.data["data"]["y1dev"][-1]))
                file.write("%e\n" % (self.data["data"]["time"][-1]))

            if voltage==allvoltages[-1]:
                self.data["EndMessage"]="Reached StopV without problems!"

            if self.plot is not None:
                self.plot.ax.set_title('I - V')
                self.plot.ax.errorbar(self.data["data"]["x"],self.data["data"]["y1"],xerr=self.data["data"]["xdev"],yerr=self.data["data"]["y1dev"])
                self.plot.canvas.draw()
                self.plot.ax.clear()

        if int(self.rampframe.idletime_var.get())>0 and not self.abort:
            self.idle(file)

        if file is not None:
            file.close()
        self.ramp_down()

    # Validating functions
    def validate_int(self,user_input, widget_name):
        # check if the input is numeric
        if isint(user_input):
            # Fetching minimum and maximum value of the spinbox
            minval = int(self.nametowidget(widget_name).config('from')[4])
            maxval = int(self.nametowidget(widget_name).config('to')[4])

            # check if the number is within the range
            if int(user_input)<minval or int(user_input)>maxval:
                if self.verbose:
                    print ("Out of range")
                return False

            # Printing the user input to the console
            if self.verbose:
                print(user_input)
            return True
        elif user_input == "" or user_input == "-":
            if self.verbose:
                print(user_input)
            return True
        # return false if input is not numeric
        else:
            if self.verbose:
                print("Not numeric")
            return False

    def validate_float(self, user_input, widget_name):
        # check if the input is numeric
        if isfloat(user_input):
            # Fetching minimum and maximum value of the spinbox
            minval = float(self.nametowidget(widget_name).config('from')[4])
            maxval = float(self.nametowidget(widget_name).config('to')[4])

            # check if the number is within the range
            if float(user_input)<minval or float(user_input)>maxval:
                if self.verbose:
                    print ("Out of range")
                return False

            # Printing the user input to the console
            if self.verbose:
                print(user_input)
            return True
        elif user_input == "" or user_input == "-":
            if self.verbose:
                print(user_input)
            return True
        # return false if input is not numeric
        else:
            if self.verbose:
                print("Not numeric")
            return False

    def write_header(self, file):
        #creating a time stamp
        mytime=time.strftime("%y%m%d%H%M%S", time.localtime())
        file.write("OPTIONS:")
        for key in self.data["options"].keys():
            file.write("<%s: %s> " % (key,self.data["options"][key]))
        file.write("\n")
        file.write("End message: " + self.data["EndMessage"] + "\n")
        file.write("Columns:%s %s_dev " % (self.data["options"]["xName"],self.data["options"]["xName"]))
        for j in range(1,self.data["ycount"]+1):
            file.write("%s %s_dev " % (self.data["options"]["y%dName" % j],self.data["options"]["y%dName" % j]))
        file.write("temp humid\n")

    # def read_option(filename,option):
    #     #this method reads always the last value which is defined in the steering file
    #     value=""
    #     file=open(filename,"r")
    #     for line in file.readlines():
    #         if line.startswith(option+":"):
    #             value=line.split(option+":")[1].split("#")[0].strip()
    #             print("Option: %s = %s" % (option, value))
    #     if value=="":
    #         print("Option: %s not found!" % option)
    #         sys.exit(1)
    #     return value
