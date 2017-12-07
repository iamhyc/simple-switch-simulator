#! /usr/bin/python
'''
Source: Data Flow Source
@author: Mark Hong
'''
import json, random
import threading, Queue
from sys import maxint
from time import ctime, sleep
from urllib2 import urlopen

def zeroPadding(length, data):
		pad_len = length - len(data)
		return data + chr(0) * pad_len

class udp_ops_class:
	"""docstring for udp_ops_class"""
	def __init__(self, port, length):
		self.skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.skt.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
		#self.skt.setblocking(0)
		self.skt.bind(('', port))
		pass
	
	def data_read_op(self):
		return self.skt.recv(4096)
		pass
	
	def data_close_op(self):
		self.skt.close()
		pass

class file_ops_class:
	"""docstring for file_ops_class"""
	def __init__(self, url, length):
		self.length = length
		self.res = urlopen(url)
		pass
	
	def data_read_op(self):
		data = res.read(self.length)
		return zeroPadding(self.length, data)
	
	def data_close_op(self):
		res.close()
		pass

class static_ops_class:
	"""docstring for static_ops_class"""
	def __init__(self, data, length):
		self.data = data
		self.length = length
		pass
	
	def data_read_op(self):
		return zeroPadding(self.length, self.data)
		pass
	
	def data_close_op(self):
		pass

class StreamSource:
	"""docstring for Source
		Two types of Source:
		* UDP Broadcast, single port occupy
		* hash File, hash to access file content
		* static, static content (tap-generator)
	"""
	def __init__(self, src):
		# Source Stream Control
		self.speed = maxint #no limit
		self.length = 1500 #default value
		self.paused = False
		self.ops_map = {
			'udp':setSource,
			'static':setSource,
			'file':setSource,
			'length':setLength,
			'speed':setSpeed
		}
		self.src_map = {
			'udp':udp_ops_class,
			'file':file_ops_class,
			'static':static_ops_class
		}
		# Source Buffer
		self.buffer = Queue()
		# Cource Buffer Handle
		self.data = self.src_map[src[0]](src[1], self.length)
		self.sourceHandle = Thread(target=self.readThread, args=())
		self.sourceHandle.setDaemon(True)
		self.sourceHandle.start()
		pass

	def setSpeed(self, data):
		self.speed = float(data)
		return False # Not reset

	def setLength(self, data):
		self.length = int(data)
		return False # Not reset

	def setSource(self, cmd):
		self.paused = True # pause read operation
		self.data_close_op() # close previous source
		self.buffer.queue.clear() # clear previous buffer

		self.data = self.src_map[cmd[0]](cmd[1], self.length)
		self.paused = False
		return True # need reset

	def config(self, cmd):
		return self.ops_map[cmd[0]](cmd[1])

	def pause(self, status):
		self.paused = status
		pass

	def isPaused(self):
		return self.paused

	def empty(self):
		return self.buffer.empty()

	def get(self):
		return self.buffer.get_nowait()
	
	def readThread(self):
		while not self.paused:
			interval = self.length / self.speed
			try:
				data = self.data_read_op()
				self.buffer.put_nowait(data)
				#print('Source Data: %s'%(data)) #for debug
				sleep(interval)
			except Exception as e:
				pass
			pass
		pass
