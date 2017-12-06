#! /usr/bin/python
'''
Source: Data Flow Source
@author: Mark Hong
'''
import threading, Queue
import random

class Source:
	"""docstring for Source
		Two types of Source:
		* UDP Broadcast, single port occupy
		* hash File, hash to access file content
		* static, static content (tap-generator)
	"""
	def __init__(self):
		self.speed = -1 #no limit
		self.buffer = Queue()
		self.type = 'static'
		self.char = ''
		self.sourceHandle = Thread(target=bufferThread)
		self.sourceHandle.setDaemon(True)
		pass

	def setSource(cmd):
		self.buffer.queue.clear()

		case, data = cmd
		if case=='static':
			self.char = data
			pass
		elif case=='udp':
			pass
		else case=='file':
			pass
		pass

	def bufferThread(self):
		#fill in buffer according to speed limit
		pass

	def empty(self):
		return self.buffer.empty()

	def get(self):
		return self.buffer.get_nowait()
		