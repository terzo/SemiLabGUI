import Tkinter
import sys
import os
import math
import time
import random
import ROOT
import array
import visa
import pyrootstyle

dryrun=True
dryrun=False

verbose=True
verbose=False

rm = visa.ResourceManager()

def mean(array):
  #straight foward!
  return 1.0*sum(array)/len(array)

def std_dev(array):
  #also quite easy
  return math.sqrt(1.0*(sum([(x-mean(array))**2 for x in array])/len(array)))

def report(message):
  #just print in verbose mode
  if verbose:
    print(message)

def write(instrument,command):
  #if real: send to instrument
  #otherwise report
  if not dryrun:
    instrument.write(command)
  else:
    report(command)


def read(instrument):
  id=""
  write(instrument,"*IDN?")
  if not dryrun:
    id=instrument.read()
  #define the reading variable
  reading={}
  #read the keithley or generate random output
  if id.find("E4980A")!=-1:
    if not dryrun:
      instrument.write("FETCH?")
      output=instrument.read()
    else:
      report("FETCH?")
      output="%e, %e, +0" %(random.random()*1.e-5,random.random())
    #parse the values
    reading["first"]=float(output.split(",")[0])
    reading["second"]=float(output.split(",")[1])
  elif id.find("2410")!=-1:
    if not dryrun:
      instrument.write("READ?")
      output=instrument.read()
    else:
      report("READ?")
      output="%e ADC, %fCext, %f hum" %(random.random()*1.e-9,random.random(),random.random())
    #parse the values
    #print(output)
    reading["voltage"]=float(output.split(",")[0])
    reading["current"]=float(output.split(",")[1].split(",")[0])
    reading["temperature"]=float(output.split(",")[2].split(",")[0])
    reading["humid"]=float(output.split(",")[3].split(",")[0])
  return reading


def get_ramparray(start,stop,stepsize=1.):
  #this one returns an array from start to stop in steps of stepsize
  #the last step to stop might be smaller
  #make sure stepsize is defined positive
  stepsize=abs(stepsize)
  #find out step direction
  direction=1.
  if stop-start<0.:
    direction=-1.
  #begin from the first value
  temp=start
  values=[]
  values.append(temp)
  #step in the right direction
  #until the second to last
  while abs(temp-stop)>stepsize:
    temp+=direction*stepsize
    values.append(temp)
  #fill in the last one  
  values.append(stop)
  return values


def ramp(instrument,start,stop,currentlimit,stepsize=1.,wait=1.,force=True):
  #does the actual ramping
  #first get the right array
  voltages=get_ramparray(start,stop,stepsize)
  #then ram through the array
  for v in voltages:
    write(instrument,":SOUR:VOLT %f" % (v))
    volt_value.set(v)
    if not force:
      #check for current limit unless ramping is forced
      if abs( read(instrument)["current"]) > abs(currentlimit):
        print("Current Limit while ramping!! Switching off!")
        #force shutdown!
        ramp(instrument,v,0.0,currentlimit,stepsize,wait,True)
        #keithley switched off
        #so return to caller
        return
    time.sleep(wait)
  return

def set_voltage():
    """Set the target voltage"""
    try:
        # if we cannot convert the value to float we don't do anything
        volt = float(tk_setV.get())
    except ValueError:
        return
    # ramp to target voltage 1
    currV = 0.0
    try:
      currV = read(k)["voltage"]
    except:
      return
    if volt>0.0:
      print("WARNING: positive value")
      return
    ramp(k,currV,volt,data["options"]["CurrentLimit"],data["options"]["StepSize"],data["options"]["StepWait"],True)

    
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


def save_data(data):
  #creating a time stamp
  mytime=time.strftime("%y%m%d%H%M%S", time.localtime())
  #create directory
  data["OutputFolder"]+=os.sep+data["StructureName"]
  items=data["OutputFolder"].split(os.sep)
  growing=""
  for item in items:
    growing+=item+os.sep
    if not os.path.isdir(growing):
      os.mkdir(growing)
  #create full filename
  fullfilename=data["OutputFolder"]+os.sep+data["options"]["Measurement"]+"_"+data["StructureName"]+"_"+mytime
  print(fullfilename)
  #save png image
  data["canvas"].SaveAs(fullfilename+".png")
  #writing to file  
  file=open(fullfilename+".dat",'w')
  file.write("OPTIONS:")
  for key in data["options"].keys():
    file.write("<%s: %s> " % (key,data["options"][key]))
  file.write("\n")
  file.write("End message: "+data["EndMessage"]+"\n")
  file.write("Columns:%s %s_dev " % (data["options"]["xName"],data["options"]["xName"]))
  for j in range(1,data["ycount"]+1):
    file.write("%s %s_dev " % (data["options"]["y%dName" % j],data["options"]["y%dName" % j]))
  file.write("temp humid\n")
  for i in range(len(data["data"]["x"])):
    file.write("%e %e " % (data["data"]["x"][i],data["data"]["xdev"][i]))
    for j in range(1,data["ycount"]+1):
      file.write("%e %e " % (data["data"]["y%d" % j][i],data["data"]["y%ddev" % j][i]))
    file.write("%.1f %.1f\n" % (data["data"]["temp"][i],data["data"]["humid"][i]))
  file.close()
  return

def ramp_down():
  currV = 0.0
  try:
    currV = read(k)["voltage"]
  except:
    currV = 0.0
  ramp(k,currV,0.0,data["options"]["CurrentLimit"],data["options"]["StepSize"],data["options"]["StepWait"],True)

def close_app():
  ramp_down()
  write(k,":OUTP 0")
  write(k,":SYST:ZCH 1")
    
  #leave program running until enter is pressed  
  k.write("trace:clear; feed:control next")
  tk_top.quit()

def set_gpib():
  #initialize and identify
  k = rm.open_resource("GPIB::%i" % data["options"]["GPIBAddress"])
  k.write("*IDN?")

  #put the keithley in the right operating mode
  write(k,":CONF:CURR")
  write(k,":SENS:CURR:RANG %.2e" % data["options"]["CurrentRange"])
  write(k,":SOUR:VOLT:RANG 1000")
  write(k,":OUTP 1")
  write(k,":SYST:ZCH 0")
  write(k,":FORM:ELEM READ,UNIT,ETEM,HUM")
  write(k,":UNIT:TEMP C")

def update_periodically():
    """Update the information from the cooling system"""
    global starttime
    # we want to do this every second so register a callback after one second
    # with Tk
    tk_top.after(2000, update_periodically)

    # get the relative time
    curtime = time.time()
    if starttime is None:
        starttime = curtime
    curtime -= starttime

    output=read(k)
    #parse the values
    #check everytime for current limit
    if abs(output["current"])>abs(data["options"]["CurrentLimit"]):
       abort=True
       ramp_down()
    #fill the temp values
    
    tempcurr = output["current"]
    curr_value.set(tempcurr)
    temptemp = output["temperature"]
    temp_value.set(temptemp)
    temphumid = output["humid"]
    humid_value.set(temphumid)
    tempV = output["voltage"]
    volt_value.set(tempV)

    # update the status variable
    #var_status.set("{1} ({0})".format(*status))
    #Update color to indicate error condition
    #tk_status.config(fg=(status[0] < 0) and "red" or "black")
    #tk_status.update()

    # update the active flag
    #var_running.set(active and 1 or 0)
    #var_extern.set(extern and 1 or 0)

    # update the temperature values and store the data into the ringbuffer
    #row = [curtime]
    #for label, name, formatter, plotit, var in values:
        #value = k.read()
        #if plotit:
            #row.append(value)
        #value = formatter(value)
        #var.set(value)

    #datapoints.add(row)
    # and finally update the plot
    #update_plot()
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
data["options"]["Measurement"]=read_option(sys.argv[1],"Measurement")

data["StartTime"]=time.time()
data["CurrentTime"]=time.time()

#here all the values are stored
data["data"]["x"]=[]
data["data"]["xdev"]=[]
data["ycount"]=1
data["data"]["y1"]=[]
data["data"]["y1dev"]=[]
data["data"]["temp"]=[]
data["data"]["tempdev"]=[]
data["data"]["humid"]=[]
data["data"]["humiddev"]=[]

#define temp arrays for averaging later on  
tempcurr = 0.0
temptemp = 0.0
temphumid = 0.0

#options
#define the most important variables for runing
#data["options"]["GPIBAddress"]=int(read_option(sys.argv[1],"GPIB"))
data["options"]["GPIBAddress"]= 24
data["options"]["Instrument"]=read_option(sys.argv[1],"Instrument")
data["options"]["StepSize"]=float(read_option(sys.argv[1],"StepSize"))
data["options"]["StepWait"]=float(read_option(sys.argv[1],"StepWait"))
data["options"]["nAverage"]=int(read_option(sys.argv[1],"nAverage"))
data["options"]["StepSizeDown"]=float(read_option(sys.argv[1],"StepSizeDown"))
#current limit
data["options"]["CurrentLimit"]=float(read_option(sys.argv[1],"CurrentLimit"))
#data["options"]["CurrentLimit"] = 1e-9
data["options"]["CurrentRange"]=float(read_option(sys.argv[1],"CurrentRange"))
data["options"]["xName"]=read_option(sys.argv[1],"xName")
data["options"]["y1Name"]=read_option(sys.argv[1],"y1Name")
#output 
data["OutputFolder"]=read_option(sys.argv[1],"OutputFolder")
data["StructureName"]=read_option(sys.argv[1],"StructureName")
#end message
data["EndMessage"]="End not defined!"

#initialize and identify
k = rm.open_resource("GPIB::%i" % data["options"]["GPIBAddress"])
k.write("*IDN?")

#put the keithley in the right operating mode
write(k,":CONF:CURR")
write(k,":SENS:CURR:RANG %.2e" % data["options"]["CurrentRange"])
write(k,":SOUR:VOLT:RANG 1000")
write(k,":OUTP 1")
write(k,":SYST:ZCH 0")
write(k,":FORM:ELEM READ,UNIT,ETEM,HUM")
write(k,":UNIT:TEMP C")

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
tk_value = Tkinter.Label(tk_values, textvariable=volt_value, anchor=Tkinter.E, relief=Tkinter.SUNKEN, width=10)
tk_value.grid(row=0, column=1, sticky=(Tkinter.E, Tkinter.W))

tk_label = Tkinter.Label(tk_values, text="Current: ")
tk_label.grid(row=1, column=0, sticky=Tkinter.W)
curr_value = Tkinter.StringVar()
tk_value = Tkinter.Label(tk_values, textvariable=curr_value, anchor=Tkinter.E, relief=Tkinter.SUNKEN, width=10)
tk_value.grid(row=1, column=1, sticky=(Tkinter.E, Tkinter.W))

tk_label = Tkinter.Label(tk_values, text="Temp: ")
tk_label.grid(row=2, column=0, sticky=Tkinter.W)
temp_value = Tkinter.StringVar()
tk_value = Tkinter.Label(tk_values, textvariable=temp_value, anchor=Tkinter.E, relief=Tkinter.SUNKEN, width=10)
tk_value.grid(row=2, column=1, sticky=(Tkinter.E, Tkinter.W))

tk_label = Tkinter.Label(tk_values, text="Humid: ")
tk_label.grid(row=3, column=0, sticky=Tkinter.W)
humid_value = Tkinter.StringVar()
tk_value = Tkinter.Label(tk_values, textvariable=humid_value, anchor=Tkinter.E, relief=Tkinter.SUNKEN, width=10)
tk_value.grid(row=3, column=1, sticky=(Tkinter.E, Tkinter.W))

# we want the second column to expand to fill the frame
tk_values.columnconfigure(1, weight=1)
# and add the frame to the top frame
tk_values.pack(fill=Tkinter.BOTH)

# add the plot showing the temperature developement
#canvas = FigureCanvasTkAgg(figure, master=tk_top)
#canvas.show()
#canvas.get_tk_widget().pack(fill=Tkinter.BOTH, expand=True)

# add setting for voltage
tk_volt = Tkinter.Frame()
tk_labelvolt = Tkinter.Label(tk_volt, text="Set voltage: ")
tk_labelvolt.pack(side=Tkinter.LEFT)
volt = 0.0
tk_setV = Tkinter.Spinbox(tk_volt, from_=-2000, to=0.0, value=volt)
tk_setV.pack(fill=Tkinter.BOTH, side=Tkinter.LEFT, expand=True)
tk_setvolt = Tkinter.Button(tk_volt, text="Set", command=set_voltage,
                            padx=2, pady=2)
tk_setvolt.pack(side=Tkinter.RIGHT)
tk_volt.pack(fill=Tkinter.X)

# add setting for the current limit
tk_currlim = Tkinter.Frame()
tk_labelcurrlim = Tkinter.Label(tk_currlim, text="Current Limit: ")
tk_labelcurrlim.pack(side=Tkinter.LEFT)
tk_setCL = Tkinter.Spinbox(tk_currlim, from_=1e-9, to=1e-6, value=data["options"]["CurrentLimit"])
tk_setCL.pack(fill=Tkinter.BOTH, side=Tkinter.LEFT, expand=True)
tk_currlim.pack(fill=Tkinter.X)

# add setting for the gpib
tk_gpib = Tkinter.Frame()
tk_labelgpib = Tkinter.Label(tk_gpib, text="GPIB address: ")
tk_labelgpib.pack(side=Tkinter.LEFT)
tk_setGPIB = Tkinter.Spinbox(tk_gpib, from_=1, to=30, value=data["options"]["GPIBAddress"])
tk_setGPIB.pack(fill=Tkinter.BOTH, side=Tkinter.LEFT, expand=True)
tk_updateGPIB = Tkinter.Button(tk_gpib, text="Update", command=set_gpib,padx=2, pady=2)
tk_updateGPIB.pack(side=Tkinter.RIGHT)
tk_gpib.pack(fill=Tkinter.X)

# and finally add a close button
var_running = Tkinter.IntVar()
var_extern = Tkinter.IntVar()
tk_bottom = Tkinter.Frame(tk_top)
tk_close = Tkinter.Button(tk_bottom, text="Close", command=close_app,
                          padx=2, pady=2)
tk_close.pack(side=Tkinter.RIGHT)
# and a button to clear the plot
#tk_clear = Tkinter.Button(tk_bottom, text="Clear Plot",
#                          command=datapoints.clear, padx=2, pady=2)
#tk_clear.pack(side=Tkinter.RIGHT)
# the activate button should be a toggle button so we use a Checkbutton but
# disable the checkbox indicator
#tk_active = Tkinter.Checkbutton(tk_bottom, text="Active", variable=var_running,
#                                command=set_active, indicatoron=False,
#                                padx=3, pady=3)
#tk_active.pack(side=Tkinter.LEFT)
# and we want a checkbox to switch between internal and external temperature
# control
#tk_extern = Tkinter.Checkbutton(tk_bottom, text="Extern", variable=var_extern,
#                                command=set_extern)
#tk_extern.pack(side=Tkinter.LEFT)
tk_bottom.pack(side=Tkinter.BOTTOM, fill=Tkinter.X)

update_periodically()   

#Run gui
tk_top.mainloop()
