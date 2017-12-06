#! /usr/bin/python
'''
Source: Data Flow Source
@author: Mark Hong
'''
import threading
import random


class Source(thrading.Thread):
	"""docstring for Source
		Two types of Source:
		* UDP Broadcast, single port occupy
		* hash File, hash to access file content
		* static, static content (tap-generator)
	"""
	def __init__(self):
		super(Source, self).__init__()
		
		self.type = 'static'
		self.source = ''
		pass

	def setSource():
		pass

	def run(self):
		pass
		