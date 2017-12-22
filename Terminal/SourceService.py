#! /usr/bin/python
'''
SourceService: for data flow manipulation
@author: Mark Hong
@level: debug
'''
import socket, struct, threading
from Utility.Utility import printh, build_control

class RelayService(object):
	"""docstring for RelayService
	Receiver Phase II(Stream): Buffer Window, Closed Link Sense
	"""
	def __init__(self, fb_tuple):
		self.paused = True
		self.fb_tuple = fb_tuple
		pass

	def init_ringbuffer(self):
		# self.ringbuffer = [0] * self.config['sWindow_rx']
		# for x in xrange(self.config['sWindow_rx']):
		# 	self.ringBuffer[x] = [-1, -1, 0, 0, [chr(0)] * 4096]
		# 	pass
		# pass
		pass

	def feedbackThread(self,fb_q):
		#build_control(0, 'RATE', inst_rate)
		#build_control(0, 'ACK', seq)
		#build_control(0, 'NAK', seq)
		#build_control(0, 'BIAS', pos)
		pass

	def redistThread(self):
		pass

	def processThread(self):
		pass

class CacheService(object):
	"""docstring for CacheService
	Receiver Phase II(Content): Buffer Window, Closed Link Sense
	"""
	def __init__(self, fb_tuple):
		self.paused = True
		self.fb_tuple = fb_tuple
		pass

	def init_ringbuffer(self):
		# redist_fp = open(path.join('Files', self.fhash), 'w+b')
		# redist_fp.truncate(self.size) #remove extra zeros
		# redist_fp.close()
		# printh('Aggregator', 'End of File', 'red')
		pass

	def feedbackThread(self):
		pass

	def processThread(self):
		pass
