# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin
import re

__plugin_name__ = "Half speed fan"
__plugin_version__ = "0.0.1"
__plugin_description__ = "Rewrite M106 to half speed"


class RewriteM106Plugin(octoprint.plugin.OctoPrintPlugin):

	regex = re.compile(ur'S(.*)')
	
	def rewrite_m106(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
		if gcode and gcode == "M106":
			found = re.search(self.regex, cmd)
			if found:
				value = int( found.group(1) )
				cmd = "M106 S%s"%int(value/2)
				return cmd,

def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = RewriteM106Plugin()

	global __plugin_hooks__
	__plugin_hooks__ = {
		"octoprint.comm.protocol.gcode.queuing": __plugin_implementation__.rewrite_m106
	}
