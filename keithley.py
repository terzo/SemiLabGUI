import sys
import os
import math
import time
import random
import array
#import visa
import pyvisa as visa

__author__ = "Michael Beimforde, Stefano Terzo"
#__copyright__ = "Copyright 2015"
__credits__ = ["Stefano Terzo"]
#__license__ = "GPL"
__version__ = "1.0.0"
__maintainer__ = "Stefano Terzo"
__email__ = "stefano.terzo@cern.ch"
__status__ = "Production"

class keithley(object):
    connected = False
    dryrun=True
    verbose=True
    lastV = 0.0
    id="2400"

    def report(self,message):
      #just print in verbose mode
      if self.verbose:
        print(message)  

    def write(self,command):
      #if real: send to instrument
      #otherwise report
      if not self.dryrun:
        self._inst.write(command)
      else:
        self.report(command)

    def read(self):
      self.write("*IDN?")
      if not self.dryrun:
        self.id=self._inst.read()
      #define the reading variable
      reading={}
      #read the keithley or generate random output
      self.report(self.id)
      if self.id.find("E4980A")!=-1:
        if not self.dryrun:
          self.write("FETCH?")
          output=self._inst.read()
        else:
          self.report("FETCH?")
          output="%e, %e, +0" %(random.random()*1.e-5,random.random())
        #parse the values
        reading["first"]=float(output.split(",")[0])
        reading["second"]=float(output.split(",")[1])
      elif self.id.find("2410")!=-1:
        if not self.dryrun:
          self.write("READ?")
          output=self._inst.read()
        else:
          self.report("READ?")
          output="%f, %f, %f, %f" %(random.random()*1.e-9,random.random(),random.random(),random.random())
        #parse the values
        self.report(output)
        reading["voltage"]=float(output.split(",")[0])
        reading["current"]=float(output.split(",")[1].split(",")[0])
        reading["temperature"]=float(output.split(",")[2].split(",")[0])
        reading["humid"]=float(output.split(",")[3].split(",")[0])
      elif self.id.find("2400")!=-1:
        if not self.dryrun:
          self.write("READ?")
          output=self._inst.read()
        else:
          self.report("READ?")
          output="%f, %f, %f, %f, %f" %(0,random.random()*1e-6,random.random(),random.random(),random.random())
        #parse the values
        self.report(output)
        reading["voltage"]=float(output.split(",")[0])
        reading["current"]=float(output.split(",")[1].split(",")[0])
        reading["temperature"]=0
        reading["humid"]=0
        #reading["resistance"]=float(output.split(",")[2])
        #reading["timestamp"]=float(output.split(",")[3])
        #reading["status"]=float(output.split(",")[4])
        print(reading)
      elif self.id.find("6517")!=-1:
        if not self.dryrun:
          self.write("READ?")
          output=self._inst.read()
        else:
          self.report("READ?")
          output="%e ADC, %fCext, %f hum" %(random.random()*1.e-9,random.random(),random.random())
        #parse the values
        self.report(output)
        reading["voltage"]=self.lastV
        reading["current"]=float(output.split("ADC")[0])
        reading["temperature"]=float(output.split(",")[1].split("Cext")[0])
        reading["humid"]=float(output.split(",")[2].split("hum")[0])
      return reading

    def get_ramparray(self,start,stop,stepsize=1.):
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

    def ramp(self,start,stop,currentlimit,stepsize=1.,wait=0.,force=False):
      #does the actual ramping
      #first get the right array
      voltages=self.get_ramparray(start,stop,stepsize)
      #then ram through the array
      for v in voltages:
        self.write(":SOUR:VOLT %f" % (v))
        self.lastV = v
        if not force:
          #check for current limit unless ramping is forced
          if abs( self.read()["current"]) > abs(currentlimit):
            print("Current Limit while ramping!! Switching off!")
            #force shutdown!
            self.ramp(v,0.0,currentlimit,stepsize,wait,True)
            #keithley switched off
            #so return to caller
            return
        time.sleep(wait)
      return

    def set_voltage(self,voltage):
        self.write(":SOUR:VOLT %f" % (voltage))
        self.lastV = voltage
        return self.lastV

    def set_limits(self,current,currentRange):
        self.write(":SENS:CURR:RANG %.2e" % currentRange)

    def output_on(self):
        self.write(":OUTP 1")

    def output_off(self):
        self.write(":OUTP 0")

    def connect(self, GPIB_address, currLim, currentRange):
      try:
        #initialize and identify
        rm = visa.ResourceManager()
        self.report("connecting to GPIB address:%i" % GPIB_address)
        if not self.dryrun:
          self._inst = rm.open_resource("GPIB1::%i" % int(GPIB_address))
          #"TCPIP::192.168.1.221::INSTR"
        self.write("*RST")
        self.write("*IDN?")
        if not self.dryrun:
          self.id=self._inst.read()
        #put the keithley in the right operating mode
        self.write(":SOUR:FUNC VOLT")
        self.set_limits(currLim, currentRange)
        if self.id.find("2400")!=-1:
          self.write(":SOUR:VOLT:RANG 200")
          self.write(":FORM:ELEM VOLT,CURR")
        else:
          self.write(":SOUR:VOLT:RANG 1000")
          self.write(":SYST:ZCH 0")
          self.write(":UNIT:TEMP C")
          self.write(":FORM:ELEM READ,UNIT,ETEM,HUM")
        self.connected = True
        print("successfully connected")
      except:
        self.connected = False
        print("connection failed")
