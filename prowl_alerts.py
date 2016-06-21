# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin

from octoprint.events import eventManager, Events
import logging
import logging.handlers
import os
from time import sleep
import re
import pyrowl


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
			result.append("{} {}".format(int(value), name))
	return ' and '.join(result[:granularity])


class ProwlPlugin(octoprint.plugin.EventHandlerPlugin, octoprint.plugin.SettingsPlugin):

	def initialize(self):
		#self._logger.setLevel(logging.DEBUG)
		self._logger.debug("ProwlPlugin initialized...")
		self.canceled = False
	
	def on_event(self, event, payload):		
		if event == Events.PRINT_STARTED:
			self.canceled = False
		elif event == Events.PRINT_CANCELLED:
			self.canceled = True
		elif event == Events.PRINT_FAILED:
			if not self.canceled:
				message="{0} failed to print.".format( os.path.basename(payload.get("file")) )
				title = "Print Failed"
				self.send_prowl(title, message)
		elif event == Events.MOVIE_DONE:
			if self.canceled:
				os.remove(payload.get("movie"))
			else:
				message = "Created {0}/downloads/timelapse/{1}".format(self._settings.get(["url"]), payload.get("movie_basename"))
				title = "Timelapse Movie"
				self.send_prowl(title, message)
		elif event == Events.MOVIE_FAILED:
			if not self.canceled:
				message = "Failed to create movie for '{0}'...".format(payload.get("gcode"))
				title = "Timelapse Movie"
				self.send_prowl(title, message)
		
			
	def send_prowl(self, title, message):
		prowl_key = self._settings.get(["prowl_key"])
		self._logger.info("Sending message '{0}':'{1}'".format(title, message))
		if prowl_key:
			try:
				service = pyrowl.Pyrowl(prowl_key)
				res = service.push("Octoprint Mobile", title, message).get(prowl_key)
				if res.get('code') == '200':
					self._logger.info( "Notification sent. %s remaining."%res.get('remaining') )
				else:
					self._logger.error( res.get('message') )
			except Exception as e:
				self._logger.error("Prowl notification failed. [%s]"%e)
		else:
			self._logger.info("Prowl not yet setup. Add your prowl_key in the config file.")	

	def get_settings_defaults(self):
		return dict(
			name = "OctoPrint",
			url  = "vlc://octoprint.local",
			prowl_key = None
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
