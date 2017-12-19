#! /usr/bin/python
'''
Source: Data Flow Source
@author: Mark Hong
@level: debug
'''
import json, socket
import threading, Queue
from os import path
from sys import maxint
from time import ctime, sleep
from urllib2 import urlopen
from Utility.Utility import printh

def zeroPadding(length, data):
	raw_len = len(data)
	if raw_len==0 or length<=0:
		return ''
	elif raw_len==length:
		return data
	else:
		pad_len = length - raw_len
		return data + chr(0) * pad_len
	pass

class udp_ops_class:
	"""docstring for udp_ops_class"""
	def __init__(self, port):
		self.port = int(port)
		self.size = -1

		self.hashcode = hash(self.port)
		self.char = ('udp', self.hashcode, self.size)

		self.skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.skt.setblocking(False)
		self.skt.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
		#self.skt.setblocking(0)
		self.skt.bind(('', self.port))
		pass
	
	def data_gethash_op(self):
		return self.hashcode

	def data_getsize_op(self):
		return self.size

	def data_read_op(self, length):
		return self.skt.recv(4096)
	
	def data_close_op(self):
		self.skt.close()
		pass

class file_ops_class:
	"""docstring for file_ops_class"""
	def __init__(self, url):
		url = path.join('Files', url)
		self.url = url
		self.size = path.getsize(self.url)

		self.hashcode = hash(self.url)
		self.char = ('file', self.hashcode, self.size)
		
		self.res = open(url, 'rb')
		pass

	def data_gethash_op(self):
		return self.hashcode

	def data_getsize_op(self):
		return self.size
	
	def data_read_op(self, length):
		data = self.res.read(length)
		return zeroPadding(length, data)
	
	def data_close_op(self):
		self.res.close()
		pass

class static_ops_class:
	"""docstring for static_ops_class"""
	def __init__(self, data):
		self.data = data
		self.size = len(self.data)

		self.hashcode = hash(self.data)
		self.char = ('static', self.hashcode, self.size)
		pass
	
	def data_gethash_op(self):
		return self.hashcode

	def data_getsize_op(self):
		return self.size

	def data_read_op(self):
		return zeroPadding(length, self.data)
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
		self.data = self.src_map[src[0]](src[1])
		pass

	def thread_init(self):
		self.sourceHandle = threading.Thread(target=self.readThread, args=())
		self.sourceHandle.setDaemon(True)
		pass

	def class_init(self):
		# Source Buffer
		self.buffer = Queue.Queue()
		# Source Buffer Handle
		self.thread_init()
		pass

	def config(self, cmd):
		return self.ops_map[cmd[0]](cmd[0], cmd[1])
	'''
	SET Operation Function
	'''
	def setSpeed(self, op, cmd):
		self.speed = float(cmd)
		return False # Not reset

	def setLength(self, op, cmd):
		self.length = int(cmd)
		self.data.length = int(cmd)
		return True # Need reset

	def setSource(self, op, cmd):
		self.stop() # stop read thread
		self.data.data_close_op() # close previous source
		self.buffer.queue.clear() # clear previous buffer

		self.data = self.src_map[op](cmd)
		return True # need reset

	'''
	GET Operation Function
	'''
	def getSource(self, op='', cmd=''):
		return self.data.char + (self.length, self.speed)

	'''
	DataSource Related Function
	'''
	def start(self):
		self.paused = False
		self.thread_init()
		self.sourceHandle.start()
		printh('Source', 'Now start...', 'green')
		pass

	def stop(self):
		self.paused = True
		if self.sourceHandle.is_alive():
			self.sourceHandle.join()
		printh('Source', 'Stream stopped...', 'red')
		pass

	def empty(self):
		return self.buffer.empty()

	def get(self):
		return self.buffer.get_nowait()
	
	def readThread(self):
		while not self.paused:
			interval = self.length / self.speed
			try:
				data = self.data.data_read_op(self.length)
				if not data:
					self.paused = True
					raise Exception('End of File')
					pass
				else:
					self.buffer.put_nowait(data)
					#print('Source Data: %s'%(data)) #for debug
					pass
				sleep(interval)
			except Exception as e:
				printh('read-thread', e, 'red')
			pass
		pass
