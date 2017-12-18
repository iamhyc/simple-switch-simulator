#! /usr/bin/python
'''
Dispatcher: 
	[Data Layer] for data flow manipulation
	data source control shifts to Dispatcher.py
@author: Mark Hong
'''
import json, random, string, crcmod
import thread, socket, Queue
import binascii, struct, ctypes
import multiprocessing
from time import sleep, ctime

from StreamSource import StreamSource
from Utility.Utility import cmd_parse, printh


class QueueCoder:
	"""docstring for QueueCoder"""
	def __init__(self, tuple_q, ratio_list, sWindow):
		self.tuple_q = tuple(tuple_q)
		self.splitter = list(ratio_list)
		self.number = len(tuple_q)
		self.win_size = sWindow
		self.count = 0
		#(ring)Buffer Array as tx sliding window
		self.tx_window = [0] * sWindow
		for x in xrange(sWindow):
			self.tx_window[x] = [chr(0)] * self.number
			pass
		pass

	def class_init(self):
		self.crcGen = crcmod.predefined.Crc('crc-16')
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
			self.tuple_q[x].queue.clear()
		#del self.tx_window #dec reference counter
		self.count = 0 #reset packet sequence
		pass

	def reput(self, seq):
		for x in xrange(self.number):
			tmp = seq % self.win_size
			tmp_str = self.tx_window[tmp][x]
			if len(tmp_str):
				self.tuple_q[x].put_nowait(tmp_str)
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
				self.crcGen.update(self.crcBuffer)
				#print(self.crcGen.crcValue) #for debug
				self.frame.pack_into(self.buffer, 0, 
									self.count, raw_len, data_ptr, self.crcGen.crcValue)

				header = ctypes.string_at(
					ctypes.addressof(self.buffer),
					self.frame.size)
				data[x] = header + raw[data_ptr:data_ptr+data_len[x]]
				data_ptr += data_len[x]
				pass
			pass
		#then, straightly push into each split queue
		for x in xrange(self.number):
			if len(data[x]):
				tmp = self.count % self.win_size
				self.tx_window[tmp][x] = data[x]
				self.tuple_q[x].put_nowait(data[x])
				pass
			pass

		self.count += 1
		print(self.count)
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

	def __init__(self, task_id, char, queue):
		#1 Internal Init
		multiprocessing.Process.__init__(self)
		self.config = {}
		self.task_id = task_id
		self.p2c_q, self.c2p_q, self.fb_q = queue
		self.wifi_ip, self.vlc_ip, self.fb_port = char
		with open('config.json') as cf:
		 	self.config = json.load(cf)
			pass
		#2 plugin Source Init
		data = ''.join(random.choice(string.hexdigits.upper()) for x in xrange(64))
		self.src = StreamSource(["static", data]) #udp/file_p/static

		#3 Socket Init
		self.__vlc_skt = None
		self.__wifi_skt = None

		#4 Operation Map Driver
		self.ops_map = {
			"src-get":self.getSource,
			"src-set":self.configSource,
			"src-now":self.triggerSource,
			"set":self.setValue,
			"ratio":self.setRatio,
		}
		pass

	def class_init(self):
		#5 Socket Queue Init 
		self.wifi_q = Queue.Queue()
		self.vlc_q = Queue.Queue()
		self.encoder = QueueCoder(
			(self.wifi_q,	self.vlc_q),
			(0.0,			1.0),
			int(self.config['sWindow_rx'])
		)
		pass

	'''
	Process Helper Function
	'''
	def response(self, status, frame=''):
		if status:
			data = '+'
		else:
			data = '-'

		frame = '%s%s'%(data, frame)
		self.c2p_q.put_nowait(frame)
		return True

	def setRatio(self, ratio):
		ratio = [float(x) for x in ratio]
		self.encoder.setRatio(ratio)
		return self.response(True)

	def setValue(self, tuple):
		return self.response(True)

	def triggerSource(self, cmd):
		self.src.start()
		return self.response(True)

	def configSource(self, cmd):
		if self.src.config(cmd): #True for Restart
			self.encoder.clearAll()
			fname, fhash, fsize = self.src.data.char
			flength = self.src.length
			frame = 'src-now %s %d %d %d'%(fname, fhash, fsize, flength) #notify Rx side
			return self.response(True, frame)
		return self.response(False)

	def getSource(self, cmd):
		frame = self.src.getSource()
		return self.response(True, frame)
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

	def distXmitThread(self):
		while True:
			if not self.src.empty():
				raw = self.src.get()
				self.encoder.put(raw)
				pass
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
		pass

	def wifiXmitThread(self, port):
		self.__wifi_skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

		while True:
			if not self.wifi_q.empty():
				data = self.wifi_q.get_nowait()
				#print('To Wi-Fi link: %s'%(data))
				self.__wifi_skt.sendto(data, (self.wifi_ip, port))
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
		#init feedback link --> non-blocking check
		thread.start_new_thread(self.uplinkThread,())# args[, kwargs]
		#init transmission link --> idle
		thread.start_new_thread(self.vlcXmitThread, (self.config['stream_vlc_port_tx'], ))
		thread.start_new_thread(self.wifiXmitThread, (self.config['stream_wifi_port'], ))
		#init data source --> busy
		thread.start_new_thread(self.distXmitThread,())
		pass

	def dist_stop(self):
		#close socket here
		#terminate thread here
		printh('%s %d'%("Client", self.task_id), "Now exit...", 'red')
		exit()
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
				pass
		except Exception as e:
			printh('Distributor', e, 'red') #for debug
		finally:
			self.dist_stop()
			pass
