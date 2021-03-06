import Tkinter
import sys
import os
import math
import time
import random
import array
import tkFont
from keithley import *

dryrun=True
dryrun=False

verbose=True
verbose=False

def mean(array):
  #straight foward!
  return 1.0*sum(array)/len(array)

def std_dev(array):
  #also quite easy
  return math.sqrt(1.0*(sum([(x-mean(array))**2 for x in array])/len(array)))

def ramp_down():
  try:
    currV = ky.read()["voltage"]
  except:
    currV = ky.lastV
    print("WARNING: cannot read voltage")
  ky.ramp(currV,0.0,float(tk_setCL.get()),float(tk_setStepSizeDown.get()),float(tk_setStepWait.get()),True)

def set_voltage():
    """Set the target voltage"""
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
      currV = ky.lastV
      print("Cannot read voltage")
      return
    if volt>0.0:
      print("WARNING: positive value")
      return
    ky.ramp(currV,volt,float(tk_setCL.get()),float(tk_setStepSizeUp.get()),float(tk_setStepWait.get()),False)

def set_voltage2():
    """Set the target voltage"""
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
      currV = ky.lastV
      print("Cannot read voltage")
      return
    if volt>0.0:
      print("WARNING: positive value")
      return
    step = float()
    if volt<currV:
      step = float(tk_setStepSizeUp.get())
      volt_tmp = currV-step
      if volt_tmp<volt:
        volt_tmp = volt
    else:
      step = float(tk_setStepSizeDown.get())
      volt_tmp = currV+step
      if volt_tmp>volt:
         volt_tmp = volt

    #print(step)
    #ky.lastV = volt_tmp
    #ky.set_voltage(volt_tmp)
    ky.ramp(currV,volt_tmp,float(tk_setCL.get()),step,0,False)
    if volt_tmp!=volt:
      tk_top.update()
      time.sleep(float(tk_setStepWait.get()))
      set_voltage2()
    
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
  if ky.connected:
    ramp_down()
    ky.write(":OUTP 0")
    ky.write(":SYST:ZCH 1")
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
      update_periodically()
    else: 
      var_status.set("connection failed")

def update_periodically():
    """Update the information from the Keathley system"""
    global starttime
    # we want to do this every second so register a callback after one second
    # with Tk
    tk_top.after(2000, update_periodically)

    # get the relative time
    curtime = time.time()
    if starttime is None:
        starttime = curtime
    curtime -= starttime
    #try:
    output= ky.read()
    #parse the values
    #check everytime for current limit
    if abs(output["current"])>abs(float(tk_setCL.get())):
      abort=True
      ramp_down()
    #fill the temp values
    tempcurr = output["current"]
    curr_value.set(tempcurr)
    #temptemp = output["temperature"]
    #temp_value.set(temptemp)
    #temphumid = output["humid"]
    #humid_value.set(temphumid)
    tempV = output["voltage"]
    volt_value.set(tempV)

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
var_status = Tkinter.StringVar()
tk_statuslabel = Tkinter.Label(tk_top, text="Status:", anchor=Tkinter.NW)
tk_statuslabel.pack(side=Tkinter.TOP, fill=Tkinter.X)
tk_status = Tkinter.Label(tk_top, textvariable=var_status,
                          relief=Tkinter.SUNKEN)
tk_status.pack(side=Tkinter.TOP, fill=Tkinter.X)

# now we show the temperature values in their own frame using grid layout
tk_values = Tkinter.Frame(tk_top)

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

separator = Tkinter.Frame(height=2, bd=1, relief=Tkinter.SUNKEN)
separator.pack(fill=Tkinter.X, padx=5, pady=5)

# add setting for the current limit
tk_currlim = Tkinter.Frame()
tk_label_up = Tkinter.Label(tk_currlim, text="Limit")
tk_label_up.grid(row = 0, column = 1, sticky=(Tkinter.E,Tkinter.W))
tk_label_up = Tkinter.Label(tk_currlim, text="Range")
tk_label_up.grid(row = 0, column = 2, sticky=(Tkinter.E,Tkinter.W))
tk_labelcurrlim = Tkinter.Label(tk_currlim, text="Set\nCurrent: ")
tk_labelcurrlim.grid(row = 0, column = 0, rowspan = 2, sticky=(Tkinter.E,Tkinter.W))
currentLimit_var = Tkinter.StringVar()
currentLimit_var.set(10e-6)
tk_setCL = Tkinter.Spinbox(tk_currlim, from_=1e-9, to=1e-3, textvariable=currentLimit_var, increment=10e-6, width=15)
tk_setCL.grid(row = 1, column = 1, sticky=(Tkinter.E,Tkinter.W))
currentRange_var = Tkinter.StringVar()
currentRange_var.set(20e-6)
tk_setCR = Tkinter.Spinbox(tk_currlim, values=(20e-5,20e-6,20e-7,20e-8,20e-9), textvariable=currentRange_var, width=15)
tk_setCR.grid(row = 1, column = 2, sticky=(Tkinter.E,Tkinter.W))
tk_setlimit = Tkinter.Button(tk_currlim, text="Set", command=set_CurrentLimit,padx=20, pady=10)
tk_setlimit.grid(row = 0, column = 3, rowspan =2, sticky=(Tkinter.E,Tkinter.W))
tk_currlim.pack(fill=Tkinter.X)

separator = Tkinter.Frame(height=2, bd=1, relief=Tkinter.SUNKEN)
separator.pack(fill=Tkinter.X, padx=5, pady=5)

# add setting for the ramping
tk_ramp = Tkinter.Frame()
tk_label_up = Tkinter.Label(tk_ramp, text="Step up")
tk_label_up.grid(row = 0, column = 1, sticky=(Tkinter.E,Tkinter.W))
tk_label_up = Tkinter.Label(tk_ramp, text="Step down")
tk_label_up.grid(row = 0, column = 2, sticky=(Tkinter.E,Tkinter.W))
tk_label_up = Tkinter.Label(tk_ramp, text="Step wait")
tk_label_up.grid(row = 0, column = 3, sticky=(Tkinter.E,Tkinter.W))
tk_labelramp = Tkinter.Label(tk_ramp, text="Ramping options: ")
tk_labelramp.grid(row = 1, column = 0, sticky=(Tkinter.E,Tkinter.W))
stepSizeUp_var = Tkinter.StringVar()
stepSizeUp_var.set(1.0)
stepSizeDown_var = Tkinter.StringVar()
stepSizeDown_var.set(5.0)
stepWait_var = Tkinter.StringVar()
stepWait_var.set(0.5)
tk_setStepSizeUp = Tkinter.Spinbox(tk_ramp, from_=1, to=10, textvariable=stepSizeUp_var, increment=1, width=10)
tk_setStepSizeUp.grid(row = 1, column = 1, sticky=(Tkinter.E,Tkinter.W))
tk_setStepSizeDown = Tkinter.Spinbox(tk_ramp, from_=1, to=10, textvariable=stepSizeDown_var, increment=1, width=10)
tk_setStepSizeDown.grid(row = 1, column = 2, sticky=(Tkinter.E,Tkinter.W))
tk_setStepWait = Tkinter.Spinbox(tk_ramp, from_=0.1, to=10.0, textvariable=stepWait_var, increment=0.1,width=10)
tk_setStepWait.grid(row = 1, column = 3, sticky=(Tkinter.E,Tkinter.W))
# add setting for voltage
tk_labelvolt = Tkinter.Label(tk_ramp, text="Set voltage: ")
tk_labelvolt.grid(row = 2, column = 0,sticky=(Tkinter.E,Tkinter.W))
volt_var = Tkinter.StringVar()
volt_var.set(0.0)
tk_setV = Tkinter.Spinbox(tk_ramp, from_=-1100, to=0.0, textvariable=volt_var, width=1)
tk_setV.grid(row = 2, column = 1, columnspan = 3,  sticky=(Tkinter.E,Tkinter.W))
tk_setvolt = Tkinter.Button(tk_ramp, text="Ramp\nVoltage", command=set_voltage2, padx=20, pady=15, state=Tkinter.DISABLED)
tk_setvolt.grid(row = 0, column = 4, rowspan =3, sticky=(Tkinter.E,Tkinter.W))
tk_ramp.pack(fill=Tkinter.X)

separator = Tkinter.Frame(height=2, bd=1, relief=Tkinter.SUNKEN)
separator.pack(fill=Tkinter.X, padx=5, pady=5)

# add setting for the gpib
tk_bottom = Tkinter.Frame(tk_top)
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

volt_value.set("0.0")
set_CurrentLimit()
var_status.set("disconnected")

ky = keithley()

#Run gui
tk_top.mainloop()
