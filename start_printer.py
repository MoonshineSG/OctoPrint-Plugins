# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin
import re

from octoprint.events import eventManager, Events

__plugin_name__ = "Power up printer"
__plugin_version__ = "0.0.1"
__plugin_description__ = "Make sure power is on when starting the heaters"


class PowerUpPlugin(octoprint.plugin.OctoPrintPlugin):

	regex = re.compile(ur'S(\d*)', re.IGNORECASE)
	
	def turn_on_printer(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
		if gcode in ["M104", "M109", "M140", "M190", "M303"]:
			found = re.search(self.regex, cmd)
			if found:
				value = float( found.group(1) )
				if value > 0:
					eventManager().fire(Events.POWER_ON)


def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = PowerUpPlugin()

	global __plugin_hooks__
	__plugin_hooks__ = {
		"octoprint.comm.protocol.gcode.sending": __plugin_implementation__.turn_on_printer
	}
