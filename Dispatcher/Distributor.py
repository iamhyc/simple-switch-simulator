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
from QueueCoder import QueueCoder
from Utility.Utility import cmd_parse, printh, load_json
from Utility.Math import randomString

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
		#2 sliding window init
		tmp = int(self.config['sWindow_tx'])/2
		self.sWindow = {
			'Wi-Fi': tmp,
			'VLC':tmp
		}
		#2 plugin Source Init
		data = randomString(64)
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

		#remain feedback rejust here#
		#adjust and coerce window upper bound
		#deal with ACK

		pass

	def EncoderThread(self):
		while True: #no window limit on source
			if not self.src.empty():
				raw = self.src.get()
				self.encoder.put(raw)
				pass
			pass
		pass

	def XmitThread(self, name, addr_tuple, xmit_q, sWindow):
		xmit_skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		seq, ptr, sWindow = 0, 0, sWindow
		while True:
			#add tx sliding window here#
			if len(xmit_q):
				seq += len(xmit_q)
				while ptr<seq:
					##ptr need adjust in feedback part
					# if (seq-ptr)<self.sWindow[name]:
					# 	ptr += 1
					# 	data = xmit_q.popleft()
					# 	xmit_skt.sendto(data, addr_tuple)
					# 	pass
					pass
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
