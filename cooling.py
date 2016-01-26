# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin

from octoprint.events import eventManager, Events
import logging
import logging.handlers

from threading import Thread
from time import sleep
import re
import atexit
import random, string

__plugin_name__ = "Cooling off"
__plugin_version__ = "0.0.3"
__plugin_description__ = "Wait for the bed temperature to reach a value set by W parameter of M140 (M140 W35) then play a sound."


class CoolingThread (Thread):

	def __init__(self, printer, logger, temperature, myid):
		Thread.__init__(self)
		self._id = myid
		self._logger = logger
		self._printer = printer
		self.wait_for = temperature	
		self.running = True
		atexit.register(self.exit)
		self._logger.debug("CoolingThread-{0} initialized".format(self._id) )

	def exit(self):
		self._logger.debug("CoolingThread-{0} stop".format(self._id))
		self.running = False
		
	def run(self):		
		self._logger.debug("CoolingThread-{0} run...".format(self._id))
		while self.running:
			temperatures = self._printer.get_current_temperatures()
			self._logger.debug(temperatures)
			if temperatures:
				if float(temperatures.get("bed").get("target")) > 0:
					sleep(5)
				else:
					actual_bed = float(temperatures.get("bed").get("actual"))
					if actual_bed < self.wait_for:
						self._logger.info("{0}: printer bed has cooled off...".format(self._id))
						self._printer.commands("M300 @cooled")
						eventManager().fire(Events.POWER_OFF)
						self.running = False
					else:
						self._logger.debug("{0}: printer bed is still hot...".format(self._id))
						sleep(5)
			else:
				self._logger.debug("{0}: no temp yet...".format(self._id))
				sleep(5)
		self._logger.debug("CoolingThread-{0} ended...".format(self._id))
	
		

class CoolingPlugin(octoprint.plugin.EventHandlerPlugin):

	regex =  re.compile(ur'(W(\d*))', re.IGNORECASE)
	
	def initialize(self):
		#self._logger.setLevel(logging.DEBUG)
		self._logger.debug("Cooling Plugin initialized...")
		self._cooler = None
	
	def on_event(self, event, payload):
		if event == Events.PRINT_STARTED:
			if self._cooler:
				self._logger.info("Stopping cooling thread ...")
				self._cooler.running = False
	
	def start_cooler(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
		if gcode and gcode == "M140":
			self._logger.debug("received 140... %s"%cmd)
			found = re.search(self.regex, cmd)			
			if found:
				self._logger.debug("'W' parameter... %s"%found.group(2) )
				value = float( found.group(2) )
				t = value
				if value < 35.0: #will never cool below ambient temperature
					t = 35.0

				temperatures = self._printer.get_current_temperatures()
				if temperatures:
					if float(temperatures.get("bed").get("actual")) > t:
						comm_instance._log("Waiting to cool off to %s˚C..."%t)
						if self._cooler:
							self._cooler.running = False
						self._cooler = CoolingThread(self._printer, self._logger, t, ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10)) )
						self._cooler.start()
			
			 	return re.sub(self.regex, "", cmd) 
	


def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = CoolingPlugin()

	global __plugin_hooks__
	__plugin_hooks__ = {
		"octoprint.comm.protocol.gcode.queuing": __plugin_implementation__.start_cooler
	}
