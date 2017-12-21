#! /usr/bin/python
'''
Dispatcher: for data flow manipulation
@author: Mark Hong
@level: debug
'''
import thread, socket
import struct, ctypes
import multiprocessing
from collections import deque
from time import sleep, ctime

from StreamSource import StreamSource
from Utility.Utility import cmd_parse, printh, load_json
from Utility.Math import *

class QueueCoder:
	"""docstring for QueueCoder"""
	def __init__(self, tuple_q, ratio_list, sWindow):
		self.tuple_q = tuple(tuple_q)
		self.splitter = list(ratio_list)
		self.number = len(tuple_q)
		self.win_size = sWindow
		self.count = 0
		#(ring)Buffer Array as tx sliding window
		self.tx_window = [[chr(0)] * self.number for x in xrange(sWindow)]
		pass

	def class_init(self):
		self.crcGen = crcFactory('crc-16')
		#Seq[4B] + Size[2B] + Offset[2B] + CRC16[2B] + Data
		#Or: Tail_Flag[1b]|Seq[4B] + Order[1B] + CRC8[2B] + Data
		self.frame = struct.Struct('IHHH') #Or, Struct('IBs')
		self.buffer = ctypes.create_string_buffer(self.frame.size)
		self.crcFrame = struct.Struct('IHH')
		self.crcBuffer = ctypes.create_string_buffer(self.crcFrame.size)
		pass

	def setRatio(self, ratio):
		#Ratio, Start, Stop, Switch
		#need a <Counter Class> first
		self.splitter = [float(x) for x in ratio]
		pass

	def clearAll(self):
		for x in xrange(self.number):
			self.tuple_q[x].clear()
		#del self.tx_window #dec reference counter
		self.count = 0 #reset packet sequence
		pass

	def reput(self, seq):
		printh('Encoder', 'reput %d'%(seq))
		seq = seq % self.win_size
		for x in xrange(self.number):
			tmp = seq % self.win_size
			tmp_str = self.tx_window[tmp][x]
			if len(tmp_str) > 1:
				self.tuple_q[x].appendleft(tmp_str)
				pass
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
		for x in xrange(self.number):
			if data_len[x]:
				self.crcFrame.pack_into(self.crcBuffer, 0,
										self.count,#Sequence number
										raw_len,#total data size
										data_ptr,#offset in subpacket
										)
				crcValue = self.crcGen(self.crcBuffer)
				self.frame.pack_into(self.buffer, 0, 
									self.count, raw_len, data_ptr, crcValue)

				header = ctypes.string_at(
					ctypes.addressof(self.buffer),
					self.frame.size)
				data[x] = header + raw[data_ptr:data_ptr+data_len[x]]
				data_ptr += data_len[x]
				pass
			pass
		#then, straightly push into each split queue
		for x in xrange(self.number):
			tmp = self.count % self.win_size
			self.tx_window[tmp][x] = data[x]
			if len(data[x]):
				self.tuple_q[x].append(data[x])
				pass
			pass

		print(self.count)
		self.count += 1
		return True

class Distributor(multiprocessing.Process):
	"""Non-Blocking running Distributor Process
		@desc 
		@var source:
			data source for this distributor, 
			default as static
		@var queue:
			multiprocess control side
	"""

	def __init__(self, task_id, fb_q, char, rf_tuple):
		#1 Internal Init
		multiprocessing.Process.__init__(self)
		self.task_id = task_id
		self.fb_q = fb_q
		self.wifi_ip, self.vlc_ip, self.fb_port = char
		self.req, self.res = rf_tuple
		self.config = load_json('./config.json')
		#2 plugin Source Init
		data = ''.join(random.choice(string.hexdigits.upper()) for x in xrange(64))
		self.src = StreamSource(task_id, ["static", data]) #udp/file_p/static

		#3 Operation Map Driver
		self.ops_map = {
			"src-get":self.getSource,
			"src-set":self.configSource,
			"src-now":self.triggerSource,
			"set":self.setValue,
			"ratio":self.setRatio,
		}
		pass

	def class_init(self):
		#4 Socket Queue Init 
		self.wifi_q = deque()
		self.vlc_q = deque()
		self.encoder = QueueCoder(
			(self.wifi_q,	self.vlc_q),
			(0.0,			1.0),
			int(self.config['sWindow_tx'])
		)
		pass

	'''
	Process Helper Function
	'''
	def setRatio(self, ratio):
		ratio = [float(x) for x in ratio]
		self.encoder.setRatio(ratio)
		return self.res(True)

	def setValue(self, tuple):
		return self.res(True)

	def triggerSource(self, cmd):
		self.src.start()
		#init feedback link --> non-blocking check
		thread.start_new_thread(self.uplinkThread,())# args[, kwargs]
		#init transmission link --> idle
		thread.start_new_thread(self.XmitThread, 
			('Wi-Fi', (self.wifi_ip, self.config['stream_wifi_port']), self.wifi_q)
		)
		thread.start_new_thread(self.XmitThread, 
			('VLC', (self.vlc_ip, self.config['stream_vlc_port_tx']), self.vlc_q)
		)
		#init data source --> busy
		thread.start_new_thread(self.EncoderThread,())
		return self.res(True)

	def configSource(self, cmd):
		if self.src.config(cmd): #True for Restart
			self.encoder.clearAll()
			fname, fhash, fsize = self.src.data.char
			flength = self.src.length
			frame = 'src-now %s %s %d %d'%(fname, fhash, fsize, flength) #notify Rx side
			return self.res(True, frame)
		return self.res(False)

	def getSource(self, cmd):
		frame = self.src.getSource()
		return self.res(True, frame)
	'''
	Process Thread Function
	'''
	def uplinkThread(self):
		fb_skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		fb_skt.bind(('', self.fb_port))

		while True:
			try:
				data = fb_skt.recv(1024)
				status, data = data[0], data[1:]
				if status=='+': #statistical data
					frame = '%s %s'%(task_id, data[1:])
					self.fb_q.put_nowait(frame)
					pass
				elif status=='-': #retransmission rquest
					self.encoder.reput(int(data))
					pass
			except Exception as e:
				pass
		pass

	def EncoderThread(self):
		while True:
			if not self.src.empty():
				raw = self.src.get()
				self.encoder.put(raw)
				pass
			pass
		pass

	def XmitThread(self, name, addr_tuple, xmit_q):
		xmit_skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		while True:
			if len(xmit_q):
				data = xmit_q.popleft()
				#print('To %s link: %s'%(name, data))
				xmit_skt.sendto(data, addr_tuple)
				pass
			pass
		pass

	'''
	Process Entrance Function
	'''
	def dist_start(self):
		self.class_init()
		self.src.class_init()
		self.encoder.class_init()
		pass

	def dist_stop(self):
		#close socket here
		#terminate thread here
		self.src.stop()
		printh('%s %d'%("Client", self.task_id), "Now exit...", 'red')
		exit()
		pass

	def run(self):
		try: # manipulate with process termination signal
			self.dist_start()
			while True: # main loop for control
				data = self.req()
				op, cmd = cmd_parse(data)
				self.ops_map[op](cmd)
				pass
		except Exception as e:
			printh('Distributor', e, 'red') #for debug
		finally:
			self.dist_stop()
			pass
