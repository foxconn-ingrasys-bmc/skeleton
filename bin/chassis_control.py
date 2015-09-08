#!/usr/bin/env python

import sys
from gi.repository import GObject
import dbus
import dbus.service
import dbus.mainloop.glib

DBUS_NAME = 'org.openbmc.control.Chassis'
OBJ_NAME = '/org/openbmc/control/Chassis/'+sys.argv[1]

POWER_OFF = 0
POWER_ON = 1

BOOTED = 100

class ChassisControlObject(dbus.service.Object):
	def __init__(self,bus,name):
		self.dbus_objects = { }

		dbus.service.Object.__init__(self,bus,name)
		## load utilized objects
		self.dbus_busses = {
			'org.openbmc.control.Power' : 
				[ { 'name' : 'PowerControl1' ,   'intf' : 'org.openbmc.control.Power' } ],
			'org.openbmc.leds.ChassisIdentify' :
				[ { 'name' : 'ChassisIdentify1', 'intf' : 'org.openbmc.control.Chassis' } ],
			'org.openbmc.control.Host' :
				[ { 'name' : 'HostControl1',     'intf' : 'org.openbmc.control.Host' } ]
		}
		self.power_sequence = 0
		self.reboot = 0	
		self.last_power_state = 0

		bus = dbus.SessionBus()

		## add signal handler to detect when new objects show up on dbus
		bus.add_signal_receiver(self.request_name,
				dbus_interface = 'org.freedesktop.DBus', 
				signal_name = "NameOwnerChanged")

		bus.add_signal_receiver(self.power_button_signal_handler, 
					dbus_interface = "org.openbmc.Button", signal_name = "ButtonPressed", 
					path="/org/openbmc/buttons/ButtonPower/PowerButton1" )
    		bus.add_signal_receiver(self.power_good_signal_handler, 
					dbus_interface = "org.openbmc.control.Power", signal_name = "PowerGood")
   		bus.add_signal_receiver(self.power_lost_signal_handler, 
					dbus_interface = "org.openbmc.control.Power", signal_name = "PowerLost")
    		bus.add_signal_receiver(self.host_watchdog_signal_handler, 
					dbus_interface = "org.openbmc.Watchdog", signal_name = "WatchdogError")
   		bus.add_signal_receiver(self.host_status_signal_handler, 
					dbus_interface = "org.openbmc.SensorMatch", signal_name = "SensorMatch",
					path="/org/openbmc/sensors/HostStatus/HostStatus1")

		try: 
			for bus_name in self.dbus_busses.keys():
				self.request_name(bus_name,"",bus_name)

		except:
			## its ok if this fails.  hotplug will detect too
			print "Warning: One of processes not started yet."
			pass

	
	def request_name(self, bus_name, a, b):
		# bus added
		if (len(b) > 0 ):
			## if bus in required list for this object, then save a pointer to interface
			## for method calls
			if (self.dbus_busses.has_key(bus_name)):
				obj_path = "/"+bus_name.replace('.','/')
				for objs in self.dbus_busses[bus_name]:
					inst_name = objs['name']
					print "Chassis control: "+inst_name
					obj =  bus.get_object(bus_name,obj_path+"/"+inst_name)
					self.dbus_objects[inst_name] = dbus.Interface(obj, objs['intf'])
	

	@dbus.service.method(DBUS_NAME,
		in_signature='', out_signature='s')
	def getID(self):
		return id

	@dbus.service.method(DBUS_NAME,
		in_signature='', out_signature='')
	def setIdentify(self):
		print "Turn on identify"
		self.dbus_objects['ChassisIdentify1'].setOn()
		return None

	@dbus.service.method(DBUS_NAME,
		in_signature='', out_signature='')
	def clearIdentify(self):
		print "Turn off identify"
		r=self.dbus_objects['ChassisIdentify1'].setOff()
		return None

	@dbus.service.method(DBUS_NAME,
		in_signature='', out_signature='')
	def setPowerOn(self):
		print "Turn on power and boot"
		self.power_sequence = 0
		self.reboot = 0
		if (self.getPowerState()==0):
			self.dbus_objects['PowerControl1'].setPowerState(POWER_ON)
			self.power_sequence = 1
		return None

	@dbus.service.method(DBUS_NAME,
		in_signature='', out_signature='')
	def setPowerOff(self):
		self.power_sequence = 0
		print "Turn off power"
		self.dbus_objects['PowerControl1'].setPowerState(POWER_OFF);
		return None

	@dbus.service.method(DBUS_NAME,
		in_signature='', out_signature='i')
	def getPowerState(self):
		state = self.dbus_objects['PowerControl1'].getPowerState();
		return state

	@dbus.service.method(DBUS_NAME,
		in_signature='', out_signature='')
	def setDebugMode(self):
		return None

	@dbus.service.method(DBUS_NAME,
		in_signature='i', out_signature='')
	def setPowerPolicy(self,policy):
		return None


	## Signal handler
	def power_button_signal_handler(self):
		# toggle power
		state = self.getPowerState()
		if state == POWER_OFF:
			self.setPowerOn()
		elif state == POWER_ON:
			self.setPowerOff();
		
		# TODO: handle long press and reset

	## Signal handlers
	def power_good_signal_handler(self):
		if (self.power_sequence==1):
			self.dbus_objects['HostControl1'].boot()
			self.power_sequence = 2

	def host_status_signal_handler(self,value):
		if (value == BOOTED and self.power_sequence==2):
			self.power_sequence=0
			print "Host booted"

	def power_lost_signal_handler(self):
		## Reboot if power is lost but reboot requested
		if (self.reboot == 1):
			self.setPowerOn()

	def host_watchdog_signal_handler(self):
		print "Watchdog Error, Rebooting"
		self.reboot = 1
		self.setPowerOff()
		

if __name__ == '__main__':
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    bus = dbus.SessionBus()
    name = dbus.service.BusName(DBUS_NAME, bus)
    obj = ChassisControlObject(bus, OBJ_NAME)
    mainloop = GObject.MainLoop()
    
    print "Running ChassisControlService"
    mainloop.run()

