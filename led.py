# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin
from octoprint.events import eventManager, Events
import smbus
import RPi.GPIO as GPIO 

__plugin_name__ = "LED Plugin"
__plugin_version__ = "0.0.1"
__plugin_description__ = "Handle status LEDs..."


class LEDPlugin(octoprint.plugin.StartupPlugin, octoprint.plugin.ShutdownPlugin, octoprint.plugin.EventHandlerPlugin):

	LED_STATUS = 3
	
	PIN_POWER = 24
	
	#funduino address
	I2C_ADDRESS = 0x04
	
	#led status
	LED_OFF = 0
	LED_ON = 1
	LED_BLINK = 2
	LED_BLINK_FAST = 3
	LED_BLINK_BEEP_BEEP = 4
	LED_FADE = 5

	bus = smbus.SMBus(1)

	def initialize(self):
		#self._logger.setLevel(logging.DEBUG)
		self._logger.info("Running RPi.GPIO version '{0}'...".format(GPIO.VERSION))
		if GPIO.VERSION < "0.6":
			raise Exception("RPi.GPIO must be greater than 0.6")
			
		GPIO.setmode(GPIO.BCM)
		GPIO.setwarnings(False)

	def send_led_command(self, status):
		try:
			self.bus.write_word_data(self.I2C_ADDRESS, self.LED_STATUS, status)
		except:
			pass
		
	def on_startup(self, host, port):
		self.send_led_command(self.LED_BLINK)
		
	def on_shutdown(self):
		self.send_led_command(self.LED_BLINK_FAST)

	def on_event(self, event, payload):
		if event == Events.POWER_ON:
			self.send_led_command(self.LED_FADE)
			
		elif event == Events.POWER_OFF:	
			self.send_led_command(self.LED_ON)
		
		elif event == Events.CONNECTED:
			if GPIO.input(self.PIN_POWER) :
				self.send_led_command(self.LED_FADE)
			else:
				self.send_led_command(self.LED_ON)	
		
		elif event == Events.DISCONNECTED:
			self.send_led_command(self.LED_BLINK_BEEP_BEEP)
			
def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = LEDPlugin()


