# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin

from octoprint.events import eventManager, Events
import logging
import logging.handlers

from time import sleep
import re
from pyrowl import notify as prowl


__plugin_name__ = "Prowl alerts"
__plugin_version__ = "0.0.1"
__plugin_description__ = "Send prowl alerts on elected events."

intervals = (
	('weeks', 604800),  # 60 * 60 * 24 * 7
	('days', 86400),	# 60 * 60 * 24
	('hours', 3600),	# 60 * 60
	('minutes', 60),
	('seconds', 1),
	)

def display_time(seconds, granularity=2):
	result = []

	for name, count in intervals:
		value = seconds // count
		if value:
			seconds -= value * count
			if value == 1:
				name = name.rstrip('s')
			result.append("{} {}".format(value, name))
	return ' and '.join(result[:granularity])


class ProwlPlugin(octoprint.plugin.EventHandlerPlugin, octoprint.plugin.SettingsPlugin):

	def initialize(self):
		#self._logger.setLevel(logging.DEBUG)
		self._logger.debug("ProwlPlugin initialized...")
	
	def on_event(self, event, payload):		
		if event == Events.PRINT_DONE:
			message="Printed '{0}' in {1}... ".format( payload.get("file"), display_time(payload.get("time")) )
			title = "Print Done"
			self.send_prowl(title, message)
		elif event == Events.PRINT_FAILED:			
			message="{0} failed to print.".format( payload.get("file") )
			title = "Print Failed"
			self.send_prowl(title, message)
		elif event == Events.MOVIE_DONE:
			message = "Created {0}/downloads/timelapse/{1}".format(self._settings.get(["url"]), payload.get("movie_basename"))
			title = "Timelapse Movie"
			self.send_prowl(title, message)
		elif event == Events.MOVIE_FAILED:
			message = "Failed to create movie for '{0}'...".format(payload.get("gcode"))
			title = "Timelapse Movie"
			self.send_prowl(title, message)
		
			
	def send_prowl(self, title, message):
		self._logger.info("Sending message '{0}':'{1}'".format(title, message))
		prowl(self._settings.get(["name"]), title , message)


	def get_settings_defaults(self):
		return dict(
			name = "Octoprint",
			url  = "vlc://octoprint.local"
		)

	def testme(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
		if gcode == "G888":
			payload = {'origin': 'local', 'time': 1391.564973115921, 'file': u'm4-nuts.gcode'}
			eventManager().fire(Events.PRINT_DONE, payload)
			sleep(2)
			payload = {'origin': 'local', 'file': u'm4-nuts.gcode'}
			eventManager().fire(Events.PRINT_FAILED, payload)
			sleep(2)
			payload = {'gcode': u'm4-nuts.gcode', 'movie_basename': u'm4-nuts_20151215110007.mpg', 'movie': u'/home/pi/.octoprint/timelapse/m4-nuts_20151215110007.mpg'}
			eventManager().fire(Events.MOVIE_DONE, payload)
			sleep(2)
			payload = {'gcode': u'm4-nuts.gcode', 'movie_basename': u'm4-nuts_20151215110007.mpg', 'movie': u'/home/pi/.octoprint/timelapse/m4-nuts_20151215110007.mpg',  "returncode": 255, "error": "Unknown error"}
			eventManager().fire(Events.MOVIE_FAILED, payload)
			return None,
			
			
			
def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = ProwlPlugin()


#	global __plugin_hooks__
#	__plugin_hooks__ = {
#		"octoprint.comm.protocol.gcode.queuing": __plugin_implementation__.testme
#	}
