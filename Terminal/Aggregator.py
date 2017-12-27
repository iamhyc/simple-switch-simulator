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
from Utility.Data import parse_options

def seq_measure():
	#0, same window;1, adjacent window;-1, multi window
	pass

def seq_adjacent(diseq, data):
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
		self.ops_map = {
			'set':self.setParam,
			'type':self.setType
		}
		self.config = load_json('./config.json')
		self.link_map = {'Wi-Fi':0,	'VLC':1}
		pass

	def thread_init(self):
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
		self.buffer_q = Queue()
		self.ringBuffer = deque([0] * self.config['sWindow_rx'])
		self.count = CountWindow(
						self.buffer_q, 
						self.ringBuffer,
						self.fb_q)
		self.src_type = RelayService(
						self.numB,
						self.ringBuffer,
						self.fb_q) #default for stream
		self.fb_q = Queue.Queue()
		# Thread Handle Init
		self.thread_init()
		pass

	def start(self):
		self.paused = True
		self.thread_init()
		#sequence need adjust here
		self.wifiRecvHandle.start()
		self.vlcRecvHandle.start()
		self.uplinkHandle.start()
		self.count.start()
		self.src_type.start()
		pass

	def stop(self):
		self.paused = True
		self.count.stop()
		self.src_type.stop()
		join_helper((self.wifiRecvHandle,
					self.vlcRecvHandle,
					self.uplinkHandle,
					self.count, self.src_type))
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
			self.src_type = CacheService(self.ringBuffer)
		else:
			self.src_type = RelayService(self.ringBuffer)
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

	def RecvThread(self, name, port):
		fid = self.link_map[name]
		recv_skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		recv_skt.bind(('', port))
		recv_skt.setblocking(False)
		#internal init#
		last_mark = 0 #record last mark
		diseq = 0 #zero-tolerance, should learn from link fragmentation
		diseq_l = deque([0] * (seqdo+1)) 
		printh(name, 'Now on ', 'green')

		while not self.paused:
			try:
				raw, addr = recv_skt.recvfrom(4096)
				(Seq_s, Options, CRC), Data = unpack_helper(self.config['control_t'], raw)
				if False: #CRC verify here#
					break
				#print('From %s link:(%d,%s,%d,%s)'%(name, hex(Seq_s), Options, Data)) #for debug
				data = parse_options(Seq_s, Options) #(Seq, Mark, Ratio, Count)
				#single link check here
				loss = seq_adjacent(data, last_mark)
				[self.feedback(loss[x]) for x in xrange( len(loss) )]
				last_mark = data[1]
				#count window next
				data = data + (Data, )
				self.buffer_q.put(data)
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
