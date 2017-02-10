# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin

from octoprint.events import eventManager, Events
import logging
import logging.handlers
import os
from time import sleep
import re, time


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
	
	def on_event(self, event, payload):		
		if event == Events.PRINT_STARTED:
			self.started = time.strftime("%Y%m%d%H%M%S")
		elif event == Events.PRINT_DONE:
			title = "Print Done"
			message="'{0}' printed in {1}. Timelapse will be available shortly.".format( payload.get("name"), display_time(payload.get("time")) )
			link =  "{0}/{1}_{2}.mpg".format(self._settings.get(["movie_link"]).strip("/"), os.path.splitext(payload.get("name"))[0], self.started )
			self.send_prowl(title, message, link)
			
	def send_prowl(self, title, message, link = None):
		prowl_key = self._settings.get(["prowl_key"])
		self._logger.info("Sending message '{0}':'{1}' [link:{2}]".format(title, message, link))
		if prowl_key:
			try:
				service = Pyrowl(prowl_key)
				res = service.push(self._settings.get(["name"]), title, message, link).get(prowl_key)
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
			movie_link  = "vlc://octoprint.local",
			prowl_key = None
		)			
			
def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = ProwlPlugin()


#	global __plugin_hooks__
#	__plugin_hooks__ = {
#		"octoprint.comm.protocol.gcode.queuing": __plugin_implementation__.testme
#	}


## ---- PROWL
#original code: https://github.com/babs/pyrowl/tree/master

from xml.dom.minidom import parseString
from httplib import HTTPSConnection
from urllib import urlencode

__version__ = "0.1"

API_SERVER = 'api.prowlapp.com'
ADD_PATH   = '/publicapi/add'

USER_AGENT="Pyrowl/v%s"%__version__

def uniq_preserve(seq): # Dave Kirby
	# Order preserving
	seen = set()
	return [x for x in seq if x not in seen and not seen.add(x)]

def uniq(seq):
	# Not order preserving
	return {}.fromkeys(seq).keys()

class Pyrowl(object):
	"""Pyrowl(apikey=[], providerkey=None)
takes 2 optional arguments:
 - (opt) apykey:	  might me a string containing 1 key or an array of keys
 - (opt) providerkey: where you can store your provider key
"""

	def __init__(self, apikey=[], providerkey=None):
		self._providerkey = None
		self.providerkey(providerkey)
		if apikey:
			if type(apikey) == str:
				apikey = [apikey]
		self._apikey		  = uniq(apikey)

	def addkey(self, key):
		"Add a key (register ?)"
		if type(key) == str:
			if not key in self._apikey:
				self._apikey.append(key)
		elif type(key) == list:
			for k in key:
				if not k in self._apikey:
					self._apikey.append(k)

	def delkey(self, key):
		"Removes a key (unregister ?)"
		if type(key) == str:
			if key in self._apikey:
				self._apikey.remove(key)
		elif type(key) == list:
			for k in key:
				if key in self._apikey:
					self._apikey.remove(k)

	def providerkey(self, providerkey):
		"Sets the provider key (and check it has the good length)"
		if type(providerkey) == str and len(providerkey) == 40:
			self._providerkey = providerkey

	def push(self, application="", event="", description="", url="", priority=0, batch_mode=False):
		"""Pushes a message on the registered API keys.
takes 5 arguments:
 - (req) application: application name [256]
 - (req) event:	   event name	   [1024]
 - (req) description: description	  [100000]
 - (opt) url:		 url			  [512]
 - (opt) priority:	from -2 (lowest) to 2 (highest) (def:0)
 - (opt) batch_mode:  call API 5 by 5 (def:False)

Warning: using batch_mode will return error only if all API keys are bad
 cf: http://www.prowlapp.com/api.php
"""
		datas = {
			'application': application[:256].encode('utf8'),
			'event':	   event[:1024].encode('utf8'),
			'description': description[:10000].encode('utf8'),
			'priority':	priority
		}

		if url:
			datas['url'] = url[:512]

		if self._providerkey:
			datas['providerkey'] = self._providerkey

		results = {}

		if not batch_mode:
			for key in self._apikey:
				datas['apikey'] = key
				res = self.callapi('POST', ADD_PATH, datas)
				results[key] = res
		else:
			for i in range(0, len(self._apikey), 5):
				datas['apikey'] = ",".join(self._apikey[i:i+5])
				res = self.callapi('POST', ADD_PATH, datas)
				results[datas['apikey']] = res
		return results
		
	def callapi(self, method, path, args):
		headers = { 'User-Agent': USER_AGENT }
		if method == "POST":
			headers['Content-type'] = "application/x-www-form-urlencoded"
		http_handler = HTTPSConnection(API_SERVER)
		http_handler.request(method, path, urlencode(args), headers)
		resp = http_handler.getresponse()

		try:
			res = self._parse_reponse(resp.read())
		except Exception, e:
			res = {'type':	"pyrowlerror",
				   'code':	600,
				   'message': str(e)
				   }
			pass
		
		return res

	def _parse_reponse(self, response):
		root = parseString(response).firstChild
		for elem in root.childNodes:
			if elem.nodeType == elem.TEXT_NODE: continue
			if elem.tagName == 'success':
				res = dict(elem.attributes.items())
				res['message'] = ""
				res['type']	= elem.tagName
				return res
			if elem.tagName == 'error':
				res = dict(elem.attributes.items())
				res['message'] = elem.firstChild.nodeValue
				res['type']	= elem.tagName
				return res
										
	