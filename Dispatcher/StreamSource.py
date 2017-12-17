#! /usr/bin/python
'''
Source: Data Flow Source
@author: Mark Hong
'''
import json, socket
import threading, Queue
from os.path import getsize
from sys import maxint
from time import ctime, sleep
from urllib2 import urlopen

def zeroPadding(length, data):
	raw_len = len(data)
	if raw_len > 0:
		pad_len = length - len(data)
		return data + chr(0) * pad_len
		pass
	else:
		return ''


class udp_ops_class:
	"""docstring for udp_ops_class"""
	def __init__(self, port, length):
		self.char = ('udp', port, length)
		self.port, self.length = int(port), length
		self.skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.skt.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
		#self.skt.setblocking(0)
		self.skt.bind(('', self.port))
		pass
	
	def data_gethash_op(self):
		return hash(self.port)

	def data_getsize_op(self):
		return (-1)*self.length

	def data_read_op(self):
		return self.skt.recv(4096)
		pass
	
	def data_close_op(self):
		self.skt.close()
		pass

class file_ops_class:
	"""docstring for file_ops_class"""
	def __init__(self, url, length):
		self.char = ('file', url, length)
		self.length = length
		self.url = url
		self.res = open(url, 'wb')
		pass

	def data_gethash_op(self):
		return hash(self.url)

	def data_getsize_op(self):
		return os.path.getsize(self.url)
	
	def data_read_op(self):
		data = res.read(self.length)
		return zeroPadding(self.length, data)
	
	def data_close_op(self):
		res.close()
		pass

class static_ops_class:
	"""docstring for static_ops_class"""
	def __init__(self, data, length):
		self.char = ('static', data, length)
		self.data = data
		self.length = length
		pass
	
	def data_gethash_op(self):
		return hash(self.data)

	def data_getsize_op(self):
		return len(data)

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
		self.paused = True
		self.ops_map = {
			'udp':self.setSource,
			'static':self.setSource,
			'file':self.setSource,
			'length':self.setLength,
			'speed':self.setSpeed,
			'get':self.getSource
		}
		self.src_map = {
			'udp':udp_ops_class,
			'file':file_ops_class,
			'static':static_ops_class
		}
		self.data = self.src_map[src[0]](src[1], self.length)
		pass

	def class_init(self):
		# Source Buffer
		self.buffer = Queue.Queue()
		# Source Buffer Handle
		self.sourceHandle = threading.Thread(target=self.readThread, args=())
		self.sourceHandle.setDaemon(True)
		pass

	def config(self, cmd):
		return self.ops_map[cmd[0]](cmd[0], cmd[1])
	'''
	SET Operation Function
	'''
	def setSpeed(self, op, data):
		self.speed = float(data)
		return False # Not reset

	def setLength(self, op, data):
		self.length = int(data)
		return True # Need reset

	def setSource(self, op, cmd):
		self.stop() # stop read thread
		self.data.data_close_op() # close previous source
		self.buffer.queue.clear() # clear previous buffer

		self.data = self.src_map[op](cmd, self.length)
		return True # need reset

	'''
	GET Operation Function
	'''
	def getSource(self, op):
		return self.data.char

	'''
	DataSource Related Function
	'''
	def start(self):
		self.paused = False
		self.sourceHandle.start()
		pass

	def stop(self):
		self.paused = True
		pass

	def empty(self):
		return self.buffer.empty()

	def get(self):
		return self.buffer.get_nowait()
	
	def readThread(self):
		while not self.paused:
			interval = self.length / self.speed
			try:
				data = self.data.data_read_op()
				if not data:
					self.paused = True
					pass
				else:
					self.buffer.put_nowait(data)
					#print('Source Data: %s'%(data)) #for debug
					pass
				sleep(interval)
			except Exception as e:
				pass
			pass
		pass
