#! /usr/bin/python
'''
Aggregator: for data flow manipulation
@author: Mark Hong
@level: debug
'''
import math, socket, Queue
import threading, multiprocessing
from os import path
from sys import maxint
from collections import deque

from SourceService import RelayService, CacheService
from Utility.Utility import *

class CountWindow:
	"""docstring for CountWindow"""
	def __init__(self, ringBuffer):
		#countWindow = [Seq, Ratio, Count, Data]
		self.selected = 0 #q0
		self.countWindow = deque()
		self.ringBuffer = ringBuffer
		pass

	def add(self ,frame):
		Seq, Index, Ratio, Count, Data = frame

		pass

	def clear(self, number): #ACK window
		pass

class Aggregator(multiprocessing.Process):
	"""docstring for Aggregator
	Receiver Phase I: Count Window, Sliding Window, Selected link Sense
	"""
	def __init__(self, rf_tuple, fb_tuple):
		super(Aggregator, self).__init__()
		self.numA = 0#beginSequence
		self.numB = -1#endSequence
		self.paused = True
		self.req, self.res = rf_tuple
		self.fb_tuple = fb_tuple
		self.src_type = RelayService() #default for stream
		self.ops_map = {
			'set':self.setParam,
			'type':self.setType
		}
		self.config = load_json('./config.json')
		self.link_map = {'Wi-Fi':0,	'VLC':1}
		pass

	def thread_init(self):
		#self.config['stream_wifi_port'], self.config['stream_vlc_port_rx']
		self.wifiRecvHandle = threading.Thread(target=self.RecvThread, 
			args=('Wi-Fi', self.config['stream_wifi_port']))
		self.wifiRecvHandle.setDaemon(True)

		self.vlcRecvHandle = threading.Thread(target=self.RecvThread, 
			args=('VLC', self.config['stream_vlc_port_rx']))
		self.vlcRecvHandle.setDaemon(True)

		self.uplinkHandle = threading.Thread(target=self.uplinkThread, args=(self.fb_q, ))
		self.uplinkHandle.setDaemon(True)
		pass

	def class_init(self):
		self.count = CountWindow()
		self.fb_q = Queue.Queue()
		# Thread Handle Init
		self.thread_init()
		pass

	'''
	Process Helper Function
	'''
	def setParam(self, cmd):
		self.start()
		#setup parameter
		self.src_type, self.fhash, fsize, flength = cmd
		self.size = int(fsize)
		flength = float(flength)
		#setup endpoint
		self.numB = int(math.ceil(self.size / flength))
		if self.numB <= 0:#endless
			self.numB = maxint
			pass
		self.stop()
		self.res(True)
		pass

	def setType(self, src_type):
		if src_type='c':
			self.src_type = CacheService()
		else:
			self.src_type = RelayService()
		self.res(True)
		pass

	'''
	Process Thread Function
	'''
	def uplinkThread(self, fb_q):
		fb_skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		while not self.paused:
			if not fb_q.empty():
				frame = fb_q.get_nowait()
				fb_skt.sendto(frame, self.fb_tuple)
				pass
			pass
		pass

	def RecvThread(self, name, port): #phase I - Sliding Window
		recv_skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		recv_skt.bind(('', port))
		recv_skt.setblocking(False)
		fid = self.link_map[name]
		printh(name, 'Now on ', 'green')

		while not self.paused:
			try:
				raw, addr = recv_skt.recvfrom(4096)
				(Seq_s, Options, CRC), Data = unpack_helper(self.config['control_t'], raw)
				if False: #CRC verify here#
					break
				#print('From %s link:(%d,%s,%d,%s)'%(name, hex(Seq_s), Options, Data)) #for debug
				data = parse_options(Seq_s, Options) #(Seq, Index, Ratio, Count)
				data = data + (Data, )
				self.count.add(data)
				pass
			except Exception as e:
				pass
			pass
		printh(name, 'paused ', 'red')
		pass

	def agg_exit(self):
		self.src_type.stop()
		self.stop()
		printh('Aggregator', "Now exit...", 'red')
		exit()
		pass

	def run(self):
		try:
			self.class_init()
			while True:
				data = self.req()
				op, cmd = cmd_parse(data)
				self.ops_map[op](cmd)
				pass
		except Exception as e:
			printh('Aggregator', e, 'red') #for debug
		finally:
			self.agg_exit()
