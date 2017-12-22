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

class Aggregator(multiprocessing.Process):
	"""docstring for Aggregator
	Receiver Phase I: Count Window, Sliding Window, Selected link Sense
	"""
	def __init__(self, rf_tuple, fb_tuple):
		super(Aggregator, self).__init__()
		self.numA = 0#beginSequence
		self.numB = -1#endSequence
		self.proc_paused = True
		self.req, self.res = rf_tuple
		self.fb_tuple = fb_tuple
		self.src_type = 'r' #default for stream
		self.ops_map = {
			'set':self.setParam,
			'type':self.setType
		}
		self.config = load_json('./config.json')
		#ringBuffer = [Seq, Ratio, Count, Data]
		self.ringBuffer = [0] * self.config['sWindow_rx']
		pass

	def thread_init(self):
		#self.config['stream_wifi_port'], self.config['stream_vlc_port_rx']
		self.wifiRecvHandle = threading.Thread(target=self.RecvThread, 
			args=('wifi', self.config['stream_wifi_port']))
		self.wifiRecvHandle.setDaemon(True)

		self.vlcRecvHandle = threading.Thread(target=self.RecvThread, 
			args=('vlc', self.config['stream_vlc_port_rx']))
		self.vlcRecvHandle.setDaemon(True)
		pass

	def class_init(self):
		# feedback init
		self.fb_skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #uplink feedback socket
		self.fb_q = Queue.Queue()
		# Thread Handle Init
		self.thread_init()
		pass

	'''
	Process Helper Function
	'''
	def setParam(self, cmd):

		#setup parameter
		self.src_type, self.fhash, fsize, flength = cmd
		self.size = int(fsize)
		flength = float(flength)
		#setup endpoint
		self.numB = int(math.ceil(self.size / flength))
		if self.numB <= 0:#endless
			self.numB = maxint
			pass

		self.res(True)
		pass

	def setType(self, src_type):
		self.src_type = src_type
		self.res(True)
		pass

	'''
	Process Thread Function
	'''
	def uplinkThread(self, fb_q):
		while not self.proc_paused:
			if not fb_q.empty():
				frame = fb_q.get_nowait()
				self.fb_skt.sendto(frame, self.fb_tuple)
				pass
			pass
		pass

	def RecvThread(self, name, port):
		#recv_skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		#recv_skt.bind(('', port))
		#recv_skt.setblocking(False)
		#raw, addr = recv_skt.recvfrom(4096)

		#remain for phase I - Sliding Window refactor here#

		pass


	def agg_exit(self):
		#close socket here
		#terminate thread here
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
