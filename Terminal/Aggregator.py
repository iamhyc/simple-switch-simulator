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

from CountWindow import CountWindow
from SourceService import RelayService, CacheService
from Utility.Utility import *
from Utility.Data import parse_options

def seq_measure(data1, data2):
	#0, same window;1, adjacent window;-1, window loss
	(s1, m1, r1, c1) = data1
	(s2, m2, r2, c2) = data2
	s1i, s2i = (s1-c1), (s2-c2)
	if (s2-s1)==(c2-c1): #same window
		win_d, seq_d = 0, (s2-s1)
		pass
	elif (s2i-s1i)==(r1+m1-m2+2) and (r2>=r1): #adjacent window
		win_d = 1
		seq_d = (c2+1) if m1==1 else (s2-s1-m2)
		pass
	else: #window shrink, or, window loss
		win_d, seq_d = -1, -1
		pass
	return win_d, seq_d

def seq_get_loss(data, diseq_l):
	loss = []
	win_d, seq_d = seq_measure(data, diseq_l[-1])
	if win_d==0:
		loss = [x for x in xrange(data[0]-seq_d+1, data[0])]
	elif win_d==1:
		loss = []
	else:
		loss = []
	return loss

class Aggregator(multiprocessing.Process):
	"""docstring for Aggregator
	Receiver Phase I: Single Link Disorder, Selected link Sense
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

		self.uplinkHandle = threading.Thread(target=self.uplinkThread, args=())
		self.uplinkHandle.setDaemon(True)
		pass

	def class_init(self):
		self.buffer_q = Queue.Queue()
		self.fb_q = Queue.Queue()
		self.ringBuffer = deque([[0,0] for x in xrange(self.config['sWindow_rx'])])
		self.cWindow = CountWindow(
						self.buffer_q, 
						self.ringBuffer,
						self.fb_q)
		self.src_type = RelayService(
						self.config['content_client_port'],
						self.numB,
						self.ringBuffer,
						self.fb_q) #default for stream
		# Thread Handle Init
		self.thread_init()
		pass

	def agg_exit(self):
		self.src_type.stop()
		self.agg_stop()
		printh('Aggregator', "Now exit...", 'red')
		exit()
		pass

	def agg_start(self):
		self.paused = False
		self.thread_init()
		#sequence need adjust here
		self.wifiRecvHandle.start()
		self.vlcRecvHandle.start()
		self.uplinkHandle.start()
		self.cWindow.start()
		self.src_type.start()
		pass

	def agg_stop(self):
		self.paused = True
		self.cWindow.stop()
		self.src_type.stop()
		join_helper((self.wifiRecvHandle,
					self.vlcRecvHandle,
					self.uplinkHandle,
					self.cWindow, self.src_type))
		pass

	'''
	Process Helper Function
	'''
	def setParam(self, cmd):
		self.agg_stop()
		#setup parameter
		self.src_type, self.fhash, fsize, flength = cmd
		self.size = int(fsize)
		self.length = int(flength)
		flength = float(flength)
		#setup endpoint
		self.numB = int(math.ceil(self.size / length))
		if self.numB <= 0:#endless
			self.numB = maxint
			pass
		self.agg_start()
		self.res(True)
		pass

	def setType(self, src_type):
		if src_type=='c':
			self.src_type = CacheService(
								(self.fhash, self.numB, self.size, self.flength),
								self.ringBuffer,
								self.fb_q
								)
		else:
			self.src_type = RelayService( #default for stream
								self.config['content_client_port'],
								self.numB,
								self.ringBuffer,
								self.fb_q
								)
		self.res(True)
		pass

	'''
	Process Thread Function
	'''
	def uplinkThread(self):
		fb_skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		while not self.paused:
			if not self.fb_q.empty():
				frame = self.fb_q.get_nowait()
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
		maxSeq = 0
		diseq = 0 #zero-tolerance, should learn from link fragmentation
		diseq_l = deque([0] * (diseq+1)) 
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
				loss = seq_get_loss(data, diseq_l)
				for x in xrange(len(loss)):
					self.fb_q.put(build_control(fid,'NAK',loss[x]))
					pass
				maxSeq += 1
				diseq_l[maxSeq % (diseq+1)] = data
				#count window next
				data = data + (Data, )
				self.buffer_q.put(data)
				pass
			except Exception as e:
				pass
			pass
		printh(name, 'paused ', 'red')
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
