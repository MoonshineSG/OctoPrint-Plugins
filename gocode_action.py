# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin
import re
import logging

from octoprint.events import eventManager, Events
from octoprint.settings import settings

__plugin_name__ = "Gcode Action"
__plugin_version__ = "0.0.1"
__plugin_description__ = "Trigger '//action:keyword' from gcode 'M808 keyword'"


class GcodeActionPlugin(octoprint.plugin.OctoPrintPlugin):

	regex = re.compile(ur'S(\d*)', re.IGNORECASE)
	
	def initialize(self):
		#self._logger.setLevel(logging.DEBUG)
		pass
	
	def custom_action_handler(self, comm, line, action, *args, **kwargs):
		#self._logger.debug(action)
		if action == "serial_log_on":
			self.change_serial_log(True)
			
		elif action == "serial_log_off":
			self.change_serial_log(False)

		elif action == "baby_up":
			self._printer.commands("M300 @baby_up")

		elif action == "baby_down":
			self._printer.commands("M300 @baby_down")

		elif action == "cooled":
			self._logger.info("printer has cooled off...")
			self._printer.commands("M300 @cooled")
			eventManager().fire(Events.POWER_OFF)
			
	def change_serial_log(self, status):
		s = settings()
		oldLog = s.getBoolean(["serial", "log"])
		
		s.setBoolean(["serial", "log"], status)
		
		if oldLog and not s.getBoolean(["serial", "log"]):
			# disable debug logging to serial.log
			logging.getLogger("SERIAL").debug("Disabling serial logging")
			logging.getLogger("SERIAL").setLevel(logging.CRITICAL)
		elif not oldLog and s.getBoolean(["serial", "log"]):
			# enable debug logging to serial.log
			logging.getLogger("SERIAL").setLevel(logging.DEBUG)
			logging.getLogger("SERIAL").debug("Enabling serial logging")
		
		if s.save():
			payload = dict(
				config_hash=s.config_hash,
				effective_hash=s.effective_hash
			)
			eventManager().fire(Events.SETTINGS_UPDATED, payload=payload)
		

def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = GcodeActionPlugin()

	global __plugin_hooks__
	__plugin_hooks__ = {"octoprint.comm.protocol.action": __plugin_implementation__.custom_action_handler}
