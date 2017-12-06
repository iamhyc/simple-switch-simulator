#! /usr/bin/python
'''
Source: Data Flow Source
@author: Mark Hong
'''
import threading


class Source(thrading.Thread):
	"""docstring for Source
		Two types of Source:
		* UDP Broadcast, single port occupy
		* hash File, hash to access file content
		* static, static content (tap-generator)
	"""
	def __init__(self):
		super(Source, self).__init__()
		pass

	def run(self):
		pass
		