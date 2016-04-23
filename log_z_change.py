# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin

from octoprint.events import eventManager, Events
import logging
import logging.handlers
import os


__plugin_name__ = "Log Z Change"
__plugin_version__ = "0.0.1"
__plugin_description__ = "Log Z change in case print fails and need to resume"


class LogZChangePlugin(octoprint.plugin.StartupPlugin, octoprint.plugin.SettingsPlugin, octoprint.plugin.EventHandlerPlugin):

	def __init__(self):
		self._console_logger = None

	def initialize(self):
		self._logger.info("LogZChange initialized...")
		self._console_logger = logging.getLogger("octoprint.plugins.zchange.console")

	def on_startup(self, host, port):
		console_logging_handler = logging.handlers.RotatingFileHandler(self._settings.get_plugin_logfile_path(postfix="console"), maxBytes=2*1024*1024)
		console_logging_handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
		console_logging_handler.setLevel(logging.DEBUG)

		self._console_logger.addHandler(console_logging_handler)
		self._console_logger.setLevel(logging.INFO)
		self._console_logger.propagate = False

	def on_event(self, event, payload):		
		if event == Events.PRINT_STARTED:
			self._console_logger.info("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
			self._console_logger.info( os.path.basename(payload.get("file")) )
			self._console_logger.info("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
		elif event == Events.PRINT_DONE:
			self._console_logger.info("---------------------------------------------------------------")
		elif event == Events.PRINT_FAILED:
			self._console_logger.info("------------------------- FAILED ------------------------------")
		elif event == Events.ERROR:
			self._console_logger.info("-------------------------- ERROR ------------------------------")
		elif event == Events.PRINT_CANCELLED:
			self._console_logger.info("----------------------- CANCELLED ------------------------------")
		elif event == Events.PRINT_PAUSED:
			self._console_logger.info("------------------------- PAUSED ------------------------------")
			
	def custom_action_handler(self, comm, line, action, *args, **kwargs):
		if action[:7] == "zchange":
			self._console_logger.info("Z %s"%action[8:])
			
def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = LogZChangePlugin()


	global __plugin_hooks__
	__plugin_hooks__ = {"octoprint.comm.protocol.action": __plugin_implementation__.custom_action_handler}

