#! /usr/bin/python
'''
Dispatcher: 
	[Data Layer] for data flow manipulation
	data source control shifts to Dispatcher.py
@author: Mark Hong
'''
import json
from time import sleep, ctime
from multiprocessing import Process, Queue
import thread
import socket
import binascii, struct

class QueueCoder:
	"""docstring for QueueCoder"""
	def __init__(self, tuple_q, ratio_list):
		self.tuple_q = tuple(tuple_q)
		self.splitter = list(ratio_list)
		self.number = len(tuple_q)
		self.count = 0
	
	def setRatio(self, ratio):
		#Ratio, Start, Stop, Switch
		#need a <Counter Class> first
		try:
			self.splitter = [float(x) for x in ratio.split(',')]
		except Exception as e:
			pass
		pass

	def put(self, raw):
		raw_len = len(raw)
		data_len = [int(round(x*raw_len)) for x in self.splitter[:self.number-1]]
		data_len.append(raw_len - sum(data_len)) #complementary last part

		#init a empty list(NOT SAME REFERENCE!)
		data = [''] * self.number 
		data_ptr = 0
		#firstly chop and add Transport Header
		#Seq[4B] + Size[2B] + Offset[2B] + Data
		#Or: Tail_Flag[1b]|Seq[4B] + Order[1B] + Data
		frame = struct.Struct('Ihh') #Or, Struct('IBs')
		for x in xrange(self.number):
			if data_len[x]:
				data[x] = frame.pack(
							self.count,#Sequence number
							raw_len,#total data size
							data_ptr,#offset in subpacket
						) + raw[data_ptr:data_ptr+data_len[x]]
				data_ptr += data_len[x]
				pass
			pass
		#then, straightly push into each split queue
		for x in xrange(self.number):
			if len(data[x]):
				self.tuple_q[x].put_nowait(data[x])

		self.count += 1
		print(self.count)
		return True

class Distributor(Process):
	"""Non-Blocking running Distributor Process
		@desc 
		@var source:
			data source for this distributor, 
			default as static
		@var queue:
			multiprocess control side
	"""
	udp_src_port	= 10086
	udp_wifi_port	= 11112 #self To port
	udp_vlc_port	= 11113 #self To port

	def __init__(self, task_id, char, queue):
		#1 Internal Init
		Process.__init__(self)
		self.config = {}
		self.task_id = task_id
		self.p2c_q, self.fb_q = queue
		self.wifi_ip, self.vlc_ip, self.fb_port = char
		with open('../config.json') as cf:
		 	self.config = json.load(cf)
			pass
		#2 Socket Init
		#self.setSource("static") #udp/file_p/static
		self.__vlc_skt = None
		self.__wifi_skt = None
		#3 Socket Queue Init 
		self.buffer = Queue()
		self.wifi_q = Queue()
		self.vlc_q = Queue()
		self.encoder = QueueCoder(
			(self.wifi_q,	self.vlc_q),
			(1.0,			0.0)
		)
		#4 Operation Map Driver
		self.ops_map = {
			"set":self.setValue,
			"ratio":self.encoder.setRatio,
		}
		pass
	
	def cmd_parse(self, str):
		cmd = ''
		op_tuple = str.lower().split(' ', 1)
		op = op_tuple[0]
		if len(op_tuple) > 1:
			cmd = op_tuple[1]
			pass
		return op, cmd

	def setValue(self, tuple):
		pass

	def setSource(self, src):
		pass

	def dist_start(self):
		#init feedback link --> non-blocking check
		thread.start_new_thread(self.uplinkThread,())# args[, kwargs]
		#init transmission link --> idle
		thread.start_new_thread(self.distXmitThread,())
		thread.start_new_thread(self.vlcXmitThread, (self.config['udp_vlc_port'], ))
		thread.start_new_thread(self.wifiXmitThread, (self.config['udp_wifi_port'], ))
		#init data source --> busy
		thread.start_new_thread(self.sourceThread, (self.config['udp_src_port'], ))
		pass

	def dist_stop(self):
		#close socket here
		#terminate thread here
		print("<%s-%d> now exit..."%("Client", self.task_id))
		exit()
		pass

	def uplinkThread(self):
		fb_skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		fb_skt.setblocking(0) #Non-blocking Socket
		fb_skt.bind(('', self.fb_port)) #should bind to the wifi_ip

		while True:
			try:
				data = fb_skt.recv(1024)
				self.fb_q.put(' '.join(task_id, cmd))#push into queue straightly
			except Exception as e:
				pass
			sleep(0)#surrender turn
		pass

	def sourceThread(self, port):
		src_skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		src_skt.setblocking(0)
		src_skt.bind(('', port)) 
		while True:
			try:
				data = src_skt.recv(4096)
				self.buffer.put_nowait(data)
				#print('Source Data: %s'%(data))
			except Exception as e:
				pass
			sleep(0)#surrender turn
		pass

	def distXmitThread(self):
		while True:
			if not self.buffer.empty():
				raw = self.buffer.get_nowait()
				self.encoder.put(raw)
				pass
			sleep(0)#surrender turn
			pass
		pass

	def vlcXmitThread(self, port):
		self.__vlc_skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

		while True:
			if not self.vlc_q.empty():
				data = self.vlc_q.get_nowait()
				#print('To VLC link: %s'%(data))
				self.__vlc_skt.sendto(data, (self.vlc_ip, port))
				pass
			sleep(0)#surrender turn
		pass

	def wifiXmitThread(self, port):
		self.__wifi_skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

		while True:
			if not self.wifi_q.empty():
				data = self.wifi_q.get_nowait()
				#print('To Wi-Fi link: %s'%(data))
				self.__wifi_skt.sendto(data, (self.wifi_ip, port))
				pass
			sleep(0)#surrender turn
		pass

	def run(self):
		try: # manipulate with process termination signal
			self.dist_start()
			while True: # main loop for control
				if not self.p2c_q.empty(): # data from Parent queue
					data = self.p2c_q.get_nowait()
					op, cmd = cmd_parse(data)
					self.ops_map[op](cmd)
					pass
				sleep(0)#surrender turn
				pass
		except Exception as e:
			print(e) #for debug
		finally:
			self.dist_stop()
			pass