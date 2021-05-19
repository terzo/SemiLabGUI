import tkinter as Tkinter
import threading
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import sys
import os
import math
import time
import ROOT
import random
import array
import tkinter.font as tkFont
from keithley import *

verbose=True
#verbose=False

abort=True
data={}
#here the data is stored
data["data"]={}

def mean(array):
  #straight foward!
  return 1.0*sum(array)/len(array)

def std_dev(array):
  #also quite easy
  return math.sqrt(1.0*(sum([(x-mean(array))**2 for x in array])/len(array)))

def ramp(start,stop,currentlimit,stepsize=1.,wait=0.,force=False):
    #does the actual ramping
    #first get the right array
    voltages=ky.get_ramparray(start,stop,stepsize)
    #then ram through the array
    for v in voltages:
        ky.set_voltage(v)
        volt_value.set(v)
        if not force:
            #check for current limit unless ramping is forced
            if abs( ky.read()["current"]) > abs(currentlimit) or abort is True:
                print("Current Limit while ramping!! Switching off!")
                #force shutdown!
                ramp(v,0.0,currentlimit,stepsize,wait,True)
                #keithley switched off
                #so return to caller
                return
        time.sleep(wait)
    return

def ramp_down():
  # try:
  #   currV = ky.read()["voltage"]
  # except:
  #   currV = ky.lastV
  #   print("WARNING: cannot read voltage")

  ramp(float(volt_value.get()),0.0,float(tk_setCL.get()),float(tk_setStepSizeDown.get()),0.1,True)

  ky.output_off()
  tk_setvolt["text"]="Ramp\nVoltage"

def save_data():
    # #creating a time stamp
    # mytime=time.strftime("%y%m%d%H%M%S", time.localtime())
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
    fullfilename=folder_path.get()
    #fullfilename=data["OutputFolder"]+os.sep+data["options"]["Measurement"]+"_"+data["StructureName"]+"_"+mytime
    #save png image
    #data["canvas"].SaveAs(fullfilename+".png")
    #writing to file
    file=open(fullfilename,'w')
    # file.write("OPTIONS:")
    # for key in data["options"].keys():
    #     file.write("<%s: %s> " % (key,data["options"][key]))
    # file.write("\n")
    # file.write("End message: "+data["EndMessage"]+"\n")
    # file.write("Columns:%s %s_dev " % (data["options"]["xName"],data["options"]["xName"]))
    # for j in range(1,data["ycount"]+1):
    #     file.write("%s %s_dev " % (data["options"]["y%dName" % j],data["options"]["y%dName" % j]))
    # file.write("temp humid\n")
    for i in range(len(data["data"]["x"])):
        file.write("%e %e " % (data["data"]["x"][i],data["data"]["xdev"][i]))
        for j in range(1,data["ycount"]+1):
            file.write("%e %e " % (data["data"]["y%d" % j][i],data["data"]["y%ddev" % j][i]))
        #file.write("%.1f %.1f\n" % (data["data"]["temp"][i],data["data"]["humid"][i]))
        file.write("%.1f\n" % (data["data"]["time"][i]))
    file.close()
    return

def idle(file):
    global abort
    global data
    global nAverage_var
    global starttime

    current_limit = float(tk_setCL.get())
    settle_time = float(tk_setStepWait.get())

    try:
        nAverage = int(nAverage_var.get())
    except ValueError:
        print("Cannot convert to int")
        return

    try:
        idletime = int(idletime_var.get())
    except ValueError:
        print("Cannot convert to int")
        return

    idlestarttime=time.time()
    curidletime = time.time() - idlestarttime

    print("Starting idle measurement")
    try :
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
                output=ky.read()
                #check everytime for current limit
                if abs(output["current"])>abs(current_limit):
                    print("CURRENT LIMIT! Ramping down!")
                    data["EndMessage"]="CURRENT LIMIT! Ramping down!"
                    abort=True
                    break
                #fill the temp values
                tempvolt.append(output["voltage"])
                tempcurrs.append(output["current"])
                temptemps.append(output["temperature"])
                temphumids.append(output["humid"])
            #if current limit is reached
            if abort:
                print("Run Stopped.")
                break

            curidletime = time.time()-idlestarttime
            curtime = time.time()-starttime
            #fill the real values
            data["data"]["time"].append(curtime)
            data["data"]["x"].append(mean(tempvolt))
            data["data"]["xdev"].append(std_dev(tempvolt))
            data["data"]["y1"].append(mean(tempcurrs))
            data["data"]["y1dev"].append(std_dev(tempcurrs))
            data["data"]["temp"].append(mean(temptemps))
            data["data"]["tempdev"].append(std_dev(temptemps))
            data["data"]["humid"].append(mean(temphumids))
            data["data"]["humiddev"].append(std_dev(temphumids))
            #for screen control
            print("Voltage %f, Mean: %.3e, StdDev: %.3e, Temp: %.1f, Humid: %.1f" % (data["data"]["x"][-1],data["data"]["y1"][-1],data["data"]["y1dev"][-1],data["data"]["temp"][-1],data["data"]["humid"][-1]))
            volt_value.set(data["data"]["x"][-1])
            curr_value.set(data["data"]["y1"][-1])

            if file is not None:
                file.write("%e %e " % (data["data"]["x"][-1],data["data"]["xdev"][-1]))
                file.write("%e %e " % (data["data"]["y1"][-1],data["data"]["y1dev"][-1]))
                file.write("%e\n" % (data["data"]["time"][-1]))

            if curtime>idletime:
                data["EndMessage"]="Reached time limit without problems!"
            #do some graphics output
            # data["canvas"].cd()
            # ROOT.TGraphErrors.Delete(data["currgraph"])
            # data["currgraph"]=ROOT.TGraphErrors(len(data["data"]["x"]),array.array("f",data["data"]["x"]),array.array("f",data["data"]["y1"]),array.array("f",data["data"]["xdev"]),array.array("f",data["data"]["y1dev"]))
            # #data["currgraph"].SetTitle("I-V curve: %s" % data["StructureName"])
            # data["currgraph"].GetXaxis().SetTitle("Voltage [V]")
            # data["currgraph"].GetYaxis().SetTitle("current [A]")
            # data["currgraph"].Draw("APL")
            # threading.Thread(target=data["canvas"].Update,args=()).start()

            ax.set_title('I - T')
            ax.errorbar(data["data"]["time"],data["data"]["y1"],xerr=data["data"]["xdev"],yerr=data["data"]["y1dev"])
            canvas.draw()
            ax.clear()

    except KeyboardInterrupt:
        #cought the keyboard abort signal
        print("You pressed Ctrl-C")
        endmessage="You pressed Ctrl-C"
        print("Powering down...")

def set_voltage3():
    global abort
    global data
    global nAverage_var
    global starttime

    try:
        # if we cannot convert the value to float we don't do anything
        start_volt = float(tk_startV.get())
    except ValueError:
        print("Cannot convert to float")
        return
    # ramp to target start voltage 1
    try:
        currV = ky.read()["voltage"]
    except:
        print("Cannot read voltage")
        return
    if start_volt>0.0:
        print("WARNING: positive starting value")
        return

    try:
        # if we cannot convert the value to float we don't do anything
        volt = float(tk_setV.get())
    except ValueError:
        print("Cannot convert to float")
        return
        # ramp to target voltage 1
    try:
        currV = ky.read()["voltage"]
    except:
        print("Cannot read voltage")
        return
    if volt>0.0:
        print("WARNING: positive value")
        return

    if volt<currV:
        step = float(tk_setStepSizeUp.get())
    else:
        step = float(tk_setStepSizeDown.get())

    ky.output_on()

    ramp(currV,start_volt,float(tk_setCL.get()),float(tk_setStepSizeUp.get()),0.5,False)

    #here all the values are stored
    data["data"]["time"]=[]
    data["data"]["x"]=[]
    data["data"]["xdev"]=[]
    data["ycount"]=1
    data["data"]["y1"]=[]
    data["data"]["y1dev"]=[]
    data["data"]["temp"]=[]
    data["data"]["tempdev"]=[]
    data["data"]["humid"]=[]
    data["data"]["humiddev"]=[]

    #data["canvas"]=ROOT.TCanvas("IV","IV",300,300)
    # #data["currgraph"]=ROOT.TGraphErrors("IV-Graph, %s" % (data["StructureName"]))
    # data["currgraph"]=ROOT.TGraphErrors()
    # data["currgraph"].Draw("APL")

    #get the array of voltages for the measurements
    allvoltages=ky.get_ramparray(start_volt,volt,step)

    settle_time = float(tk_setStepWait.get())
    current_limit = float(tk_setCL.get())

    try:
        nAverage = int(nAverage_var.get())
    except ValueError:
        print("Cannot convert to int")
        return

    fullfilename=folder_path.get()
    file = None
    try:
        file=open(fullfilename,'w')
    except:
        print("WARNING: file name not valid. Data will not be saved.")

    starttime = time.time()

    try :
        for voltage in allvoltages :
            #power to the right voltage
            #ky.write(":SOUR:VOLT %.3f" % (voltage))
            ky.set_voltage(voltage)
            volt_value.set(voltage)
            #define temp arrays for averaging later on
            tempcurrs=[]
            temptemps=[]
            temphumids=[]
            #wait for the currents to settle
            print("Waiting %.1f seconds..." % (settle_time))
            time.sleep(settle_time)
            print("measuring...")
            for i in range(nAverage):
                output=ky.read()
                #check everytime for current limit
                if abs(output["current"])>abs(current_limit):
                    print("CURRENT LIMIT! Ramping down!")
                    data["EndMessage"]="CURRENT LIMIT! Ramping down!"
                    abort=True
                    break
                #fill the temp values
                tempcurrs.append(output["current"])
                temptemps.append(output["temperature"])
                temphumids.append(output["humid"])
            #if current limit is reached
            if abort:
                print("Run Stopped.")
                break

            curtime = time.time()-starttime
            #fill the real values
            data["data"]["time"].append(curtime)
            data["data"]["x"].append(voltage)
            data["data"]["xdev"].append(0.0)
            data["data"]["y1"].append(mean(tempcurrs))
            data["data"]["y1dev"].append(std_dev(tempcurrs))
            data["data"]["temp"].append(mean(temptemps))
            data["data"]["tempdev"].append(std_dev(temptemps))
            data["data"]["humid"].append(mean(temphumids))
            data["data"]["humiddev"].append(std_dev(temphumids))
            #for screen control
            print("Voltage %f, Mean: %.3e, StdDev: %.3e, Temp: %.1f, Humid: %.1f" % (data["data"]["x"][-1],data["data"]["y1"][-1],data["data"]["y1dev"][-1],data["data"]["temp"][-1],data["data"]["humid"][-1]))
            volt_value.set(data["data"]["x"][-1])
            curr_value.set(data["data"]["y1"][-1])

            if file is not None:
                file.write("%e %e " % (data["data"]["x"][-1],data["data"]["xdev"][-1]))
                file.write("%e %e " % (data["data"]["y1"][-1],data["data"]["y1dev"][-1]))
                file.write("%e\n" % (data["data"]["time"][-1]))

            if voltage==allvoltages[-1]:
                data["EndMessage"]="Reached StopV without problems!"
            #do some graphics output
            # data["canvas"].cd()
            # ROOT.TGraphErrors.Delete(data["currgraph"])
            # data["currgraph"]=ROOT.TGraphErrors(len(data["data"]["x"]),array.array("f",data["data"]["x"]),array.array("f",data["data"]["y1"]),array.array("f",data["data"]["xdev"]),array.array("f",data["data"]["y1dev"]))
            # #data["currgraph"].SetTitle("I-V curve: %s" % data["StructureName"])
            # data["currgraph"].GetXaxis().SetTitle("Voltage [V]")
            # data["currgraph"].GetYaxis().SetTitle("current [A]")
            # data["currgraph"].Draw("APL")
            # threading.Thread(target=data["canvas"].Update,args=()).start()

            ax.set_title('I - V')
            ax.errorbar(data["data"]["x"],data["data"]["y1"],xerr=data["data"]["xdev"],yerr=data["data"]["y1dev"])
            canvas.draw()
            ax.clear()

    except KeyboardInterrupt:
        #cought the keyboard abort signal
        print("You pressed Ctrl-C")
        endmessage="You pressed Ctrl-C"
        print("Powering down...")

    if int(idletime_var.get())>0 and not abort:
        idle(file)

    if file is not None:
        file.close()
    ramp_down()


def set_voltage4():
    global data
    # data["canvas"]=ROOT.TCanvas("IV","IV")
    # #data["currgraph"]=ROOT.TGraphErrors("IV-Graph, %s" % (data["StructureName"]))
    # data["currgraph"]=ROOT.TGraphErrors()
    # data["currgraph"].Draw("APL")

    global abort
    if tk_setvolt["text"]=="Stop":
        abort=True
        return
    else:
        abort=False
        tk_setvolt["text"]="Stop"

    threading.Thread(target=set_voltage3,args=()).start()
    #update_periodically()

def read_option(filename,option):
  #this method reads always the last value which is defined in the steering file
  value=""
  file=open(filename,"r")
  for line in file.readlines():
    if line.startswith(option+":"):
      value=line.split(option+":")[1].split("#")[0].strip()
      print("Option: %s = %s" % (option, value))
  if value=="":
    print("Option: %s not found!" % option)
    sys.exit(1)
  return value

def close_app():
  data.clear()
  ROOT.gROOT.EndOfProcessCleanups()
  if ky.connected:
    ramp_down()
    #leave program running until enter is pressed
    ky.write("trace:clear; feed:control next")
  tk_top.quit()

def set_CurrentLimit():
  """Set the target voltage"""
  try:
    # if we cannot convert the value to float we don't do anything
    curr   = float(tk_setCL.get())
    currLimit_value.set(curr)
  except ValueError:
    return  

def set_gpib():
    #initialize and identify
    #print(tk_setGPIB.get())
    ky.connect(int(tk_setGPIB.get()),float(tk_setCR.get()))
    if ky.connected:
      var_status.set("connected to GPIB::%i" % int(tk_setGPIB.get()))
      tk_setCR.config(state=Tkinter.DISABLED)
      tk_setCL.config(to=tk_setCR.get())
      tk_setvolt.config(state=Tkinter.NORMAL)
      #update_periodically()
    else: 
      var_status.set("connection failed")

def browse():
    # Allow user to select a directory and store it in global var
    # called folder_path
    global folder_path
    filename = Tkinter.filedialog.asksaveasfilename(initialfile=folder_path.get(), defaultextension=".txt")
    folder_path.set(filename)

def update_periodically():
    """Update the information from the Keathley system"""
    # we want to do this every second so register a callback after one second
    # with Tk
    tk_top.after(2000, update_periodically)
    #tk_top.after(float(tk_setStepWait.get())*1000, update_periodically)

    # get the relative time
    curtime = time.time()
    if starttime is None:
        starttime = curtime
    curtime -= starttime
    # data["canvas"].Modified()
    # data["canvas"].Update()
    # try:
    #     output= ky.read()
    #     #parse the values
    #     #check everytime for current limit
    #     if abs(output["current"])>abs(float(tk_setCL.get())):
    #         abort=True
    #         ramp_down()
    #     #fill the temp values
    #     tempcurr = output["current"]
    #     curr_value.set(tempcurr)
    #     tempV = output["voltage"]
    #     volt_value.set(tempV)
    # except:
    #     print("Failed to read device")

    data["CurrentTime"]=time.time()


# now create gui. First, create the top level frame
#currentV = read(instrument)["voltage"]
starttime = None

tk_top = Tkinter.Tk()
tk_top.title("Kiethley")

data={}
#here the data is stored
data["data"]={}
#here are the options that are also written to file
data["options"]={}

data["StartTime"]=time.time()
data["CurrentTime"]=time.time()

#define temp arrays for averaging later on  
tempcurr = 0.0
temptemp = 0.0
temphumid = 0.0

# now add the text field showing the status info. we use a Tk variable to keep
# the status message so we can update it easily
separator = Tkinter.Frame(tk_top, height=2, bd=1, relief=Tkinter.SUNKEN)
separator.pack(side=Tkinter.LEFT, fill=Tkinter.BOTH, padx=5, pady=5)

tk_left = Tkinter.Frame(tk_top)
var_status = Tkinter.StringVar()
tk_statuslabel = Tkinter.Label(tk_left, text="Status:", anchor=Tkinter.NW)
tk_statuslabel.pack(side=Tkinter.TOP, fill=Tkinter.X)
tk_status = Tkinter.Label(tk_left, textvariable=var_status,
                          relief=Tkinter.SUNKEN)
tk_status.pack(side=Tkinter.TOP, fill=Tkinter.X)

tk_left.pack(side=Tkinter.LEFT, fill=Tkinter.BOTH)

# now we show the temperature values in their own frame using grid layout
tk_values = Tkinter.Frame(tk_left)

tk_label = Tkinter.Label(tk_values, text="Voltage: ")
tk_label.grid(row=0, column=0, sticky=Tkinter.W)
volt_value = Tkinter.StringVar()
tk_value = Tkinter.Label(tk_values, textvariable=volt_value, anchor=Tkinter.E, relief=Tkinter.SUNKEN, width=10, font=tkFont.Font(size=18))
tk_value.grid(row=0, column=1, sticky=(Tkinter.E, Tkinter.W))

tk_label = Tkinter.Label(tk_values, text="Current: ")
tk_label.grid(row=1, column=0, sticky=Tkinter.W)
curr_value = Tkinter.StringVar()
tk_value = Tkinter.Label(tk_values, textvariable=curr_value, anchor=Tkinter.E, relief=Tkinter.SUNKEN, width=10,font=tkFont.Font(size=18))
tk_value.grid(row=1, column=1, sticky=(Tkinter.E, Tkinter.W))

tk_label = Tkinter.Label(tk_values, text="Current Limit: ")
tk_label.grid(row=2, column=0, sticky=Tkinter.W)
currLimit_value = Tkinter.StringVar()
tk_value = Tkinter.Label(tk_values, textvariable=currLimit_value, anchor=Tkinter.E, relief=Tkinter.SUNKEN, width=10,font=tkFont.Font(size=18) )
tk_value.grid(row=2, column=1, sticky=(Tkinter.E, Tkinter.W))

#tk_label = Tkinter.Label(tk_values, text="Temp: ")
#tk_label.grid(row=3, column=0, sticky=Tkinter.W)
#temp_value = Tkinter.StringVar()
#tk_value = Tkinter.Label(tk_values, textvariable=temp_value, anchor=Tkinter.E, relief=Tkinter.SUNKEN, width=10)
#tk_value.grid(row=3, column=1, sticky=(Tkinter.E, Tkinter.W))

#tk_label = Tkinter.Label(tk_values, text="Humid: ")
#tk_label.grid(row=4, column=0, sticky=Tkinter.W)
#humid_value = Tkinter.StringVar()
#tk_value = Tkinter.Label(tk_values, textvariable=humid_value, anchor=Tkinter.E, relief=Tkinter.SUNKEN, width=10)
#tk_value.grid(row=4, column=1, sticky=(Tkinter.E, Tkinter.W))

# we want the second column to expand to fill the frame
tk_values.columnconfigure(1, weight=1)
# and add the frame to the top frame
tk_values.pack(fill=Tkinter.BOTH)

separator = Tkinter.Frame(tk_left, height=2, bd=1, relief=Tkinter.SUNKEN)
separator.pack(fill=Tkinter.X, padx=5, pady=5)

# add setting for the current limit
tk_currlim = Tkinter.Frame(tk_left)
tk_label_up = Tkinter.Label(tk_currlim, text="Limit")
tk_label_up.grid(row = 0, column = 1, sticky=(Tkinter.W))
tk_label_up = Tkinter.Label(tk_currlim, text="Range")
tk_label_up.grid(row = 0, column = 3, sticky=(Tkinter.W))
tk_labelcurrlim = Tkinter.Label(tk_currlim, text="Set Current: ", width=12)
tk_labelcurrlim.grid(row =1, column = 0, rowspan = 1, sticky=(Tkinter.E,Tkinter.W))
currentLimit_var = Tkinter.StringVar()
currentLimit_var.set(10e-6)
tk_setCL = Tkinter.Spinbox(tk_currlim, from_=1e-9, to=1e-3, textvariable=currentLimit_var, increment=10e-6, width=17)
tk_setCL.grid(row = 1, column = 1, columnspan=2, sticky=(Tkinter.E,Tkinter.W))
currentRange_var = Tkinter.StringVar()
currentRange_var.set(10e-6)
tk_setCR = Tkinter.Spinbox(tk_currlim, values=(10e-5,10e-6,10e-7,10e-8,10e-9), textvariable=currentRange_var, width=17)
tk_setCR.grid(row = 1, column = 3, columnspan=2, sticky=(Tkinter.E,Tkinter.W))
tk_setlimit = Tkinter.Button(tk_currlim, text="Set", command=set_CurrentLimit,padx=20, pady=10)
tk_setlimit.grid(row = 0, column = 5, rowspan=2, sticky=(Tkinter.E))
tk_currlim.pack(fill=Tkinter.X)

separator = Tkinter.Frame(tk_left, height=2, bd=1, relief=Tkinter.SUNKEN)
separator.pack(fill=Tkinter.X, padx=5, pady=5)

# add setting for the ramping
tk_ramp = Tkinter.Frame(tk_left)
tk_label_up = Tkinter.Label(tk_ramp, text="Step up")
tk_label_up.grid(row = 0, column = 1, sticky=(Tkinter.W))
tk_label_up = Tkinter.Label(tk_ramp, text="Step down")
tk_label_up.grid(row = 0, column = 2, sticky=(Tkinter.W))
tk_label_up = Tkinter.Label(tk_ramp, text="Step wait")
tk_label_up.grid(row = 0, column = 3, sticky=(Tkinter.W))
tk_label_up = Tkinter.Label(tk_ramp, text="nAverage")
tk_label_up.grid(row = 0, column = 4, sticky=(Tkinter.W))
tk_labelramp = Tkinter.Label(tk_ramp, text="Ramping options: ")
tk_labelramp.grid(row = 1, column = 0, sticky=(Tkinter.W))
stepSizeUp_var = Tkinter.StringVar()
stepSizeUp_var.set(1.0)
stepSizeDown_var = Tkinter.StringVar()
stepSizeDown_var.set(5.0)
stepWait_var = Tkinter.StringVar()
stepWait_var.set(0.5)
nAverage_var = Tkinter.StringVar()
nAverage_var.set(10)
tk_setStepSizeUp = Tkinter.Spinbox(tk_ramp, from_=1, to=10, textvariable=stepSizeUp_var, increment=1, width=7)
tk_setStepSizeUp.grid(row = 1, column = 1, sticky=(Tkinter.E,Tkinter.W))
tk_setStepSizeDown = Tkinter.Spinbox(tk_ramp, from_=1, to=10, textvariable=stepSizeDown_var, increment=1, width=7)
tk_setStepSizeDown.grid(row = 1, column = 2, sticky=(Tkinter.E,Tkinter.W))
tk_setStepWait = Tkinter.Spinbox(tk_ramp, from_=0.1, to=10.0, textvariable=stepWait_var, increment=0.1,width=7)
tk_setStepWait.grid(row = 1, column = 3, sticky=(Tkinter.E,Tkinter.W))
tk_setnAverage = Tkinter.Spinbox(tk_ramp, from_=1, to=1000.0, textvariable=nAverage_var, increment=1,width=7)
tk_setnAverage.grid(row = 1, column = 4, sticky=(Tkinter.E,Tkinter.W))
# add setting for voltage
tk_labelvolt = Tkinter.Label(tk_ramp, text="Set voltage: ")
tk_labelvolt.grid(row = 3, column = 0,sticky=(Tkinter.E,Tkinter.W))
startV_var = Tkinter.StringVar()
startV_var.set(0.0)
volt_var = Tkinter.StringVar()
volt_var.set(0.0)
idletime_var = Tkinter.StringVar()
idletime_var.set(0.0)
tk_label_vstart = Tkinter.Label(tk_ramp, text="Start")
tk_label_vstart.grid(row = 2, column = 1, sticky=(Tkinter.W))
tk_label_vstop = Tkinter.Label(tk_ramp, text="Stop")
tk_label_vstop.grid(row = 2, column = 2, sticky=(Tkinter.W))
tk_label_vstop = Tkinter.Label(tk_ramp, text="Idle")
tk_label_vstop.grid(row = 2, column = 4, sticky=(Tkinter.W))
tk_startV = Tkinter.Spinbox(tk_ramp, from_=-1100, to=0.0, textvariable=startV_var, width=1)
tk_startV.grid(row = 3, column = 1, columnspan = 1,  sticky=(Tkinter.E,Tkinter.W))
tk_setV = Tkinter.Spinbox(tk_ramp, from_=-1100, to=0.0, textvariable=volt_var, width=1)
tk_setV.grid(row = 3, column = 2, columnspan = 2,  sticky=(Tkinter.E,Tkinter.W))
tk_idle = Tkinter.Spinbox(tk_ramp, from_=0, to=1e6, textvariable=idletime_var, width=1)
tk_idle.grid(row = 3, column = 4, columnspan = 1,  sticky=(Tkinter.E,Tkinter.W))
tk_setvolt = Tkinter.Button(tk_ramp, text="Ramp\nVoltage", command=set_voltage4, padx=12, pady=15, height = 3, width = 5, state=Tkinter.DISABLED)
tk_setvolt.grid(row = 0, column = 5, rowspan =4, sticky=(Tkinter.E,Tkinter.W,Tkinter.S))
tk_ramp.pack(fill=Tkinter.X)

separator = Tkinter.Frame(tk_left, height=2, bd=1, relief=Tkinter.SUNKEN)
separator.pack(fill=Tkinter.X, padx=5, pady=5)

tk_browse = Tkinter.Frame(tk_left)
folder_path = Tkinter.StringVar()
path_entry = Tkinter.Entry(master=tk_browse,textvariable=folder_path)
path_entry.pack(side=Tkinter.LEFT, fill=Tkinter.X, expand=True)
browse_button = Tkinter.Button(tk_browse, text="Browse", command=browse)
browse_button.pack(side=Tkinter.RIGHT, fill=Tkinter.X)
save_button = Tkinter.Button(tk_browse, text="Save", command=save_data)
save_button.pack(side=Tkinter.RIGHT, fill=Tkinter.X)
tk_browse.pack(fill=Tkinter.X)

separator = Tkinter.Frame(tk_left, height=2, bd=1, relief=Tkinter.SUNKEN)
separator.pack(fill=Tkinter.X, padx=5, pady=5)

# add setting for the gpib
tk_bottom = Tkinter.Frame(tk_left)
tk_labelgpib = Tkinter.Label(tk_bottom, text="GPIB address: ")
tk_labelgpib.pack(side=Tkinter.LEFT)
gpib_value = Tkinter.StringVar()
gpib_value.set(27)
tk_setGPIB = Tkinter.Spinbox(tk_bottom, from_=1, to=30, textvariable=gpib_value, width=5, font=tkFont.Font(size=10))
tk_setGPIB.pack(fill=Tkinter.BOTH, side=Tkinter.LEFT, expand=True)
tk_connectGPIB = Tkinter.Button(tk_bottom, text="Connect", command=set_gpib,padx=20, pady=2)
tk_connectGPIB.pack(side=Tkinter.LEFT)
# and finally add a close button
tk_close = Tkinter.Button(tk_bottom, text="Close", command=close_app,padx=20, pady=2)
tk_close.pack(side=Tkinter.RIGHT)
tk_bottom.pack(side=Tkinter.BOTTOM, fill=Tkinter.X)

separator = Tkinter.Frame(tk_top, height=2, bd=1, relief=Tkinter.SUNKEN)
separator.pack(side=Tkinter.LEFT, fill=Tkinter.BOTH, padx=5, pady=5)

tk_rightside = Tkinter.Frame(tk_top)
figure = plt.Figure(figsize=(6,5), dpi=100)
ax = figure.add_subplot(111)
canvas = FigureCanvasTkAgg(figure, tk_rightside)
canvas.get_tk_widget().pack(fill=Tkinter.Y, side=Tkinter.LEFT)
tk_rightside.pack(side=Tkinter.LEFT, fill=Tkinter.BOTH)

volt_value.set("0.0")
set_CurrentLimit()
var_status.set("disconnected")

ky = keithley()

#Run gui
tk_top.mainloop()
