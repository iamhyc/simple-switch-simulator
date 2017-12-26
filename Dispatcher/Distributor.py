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
from Utility.Utility import *
from Utility.Math import randomString

class Distributor(multiprocessing.Process):
	"""Non-Blocking running Distributor Process
		@desc
	"""
	def __init__(self, task_id, fb_q, char, rf_tuple):
		#1 Internal Init
		multiprocessing.Process.__init__(self)
		self.config = load_json('./config.json')
		self.task_id 							= task_id
		self.fb_q 								= fb_q
		self.wifi_ip, self.vlc_ip, self.fb_port = char
		self.req, self.res 						= rf_tuple
		#2 sliding window init
		tmp = int(self.config['sWindow_tx'])/2
		self.link_map	=	{'Wi-Fi':0,	'VLC':1}
		self.sWindow	=	[tmp,	tmp]
		self.ptr		=	[0,		0]
		#2 plugin Source Init
		data = randomString(64)
		self.src = StreamSource(task_id, ["static", data]) #udp/file_p/static
		#3 Operation Map Driver
		self.ops_map = {
			"src-get":self.getSource,
			"src-set":self.configSource,
			"src-now":self.triggerSource,
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
		self.encoder.setRatio(int(ratio))
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
		fid = self.link_map[name]
		seq, sWindow = 0, sWindow
		while True:
			if len(xmit_q) and (seq-self.ptr[fid])<self.sWindow[fid] :
				seq += 1
				data = xmit_q.popleft()
				xmit_skt.sendto(data, addr_tuple)
				#print('To %s link: %s'%(name, data))
				pass
			pass
		pass

	def uplinkThread(self):
		fb_skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		fb_skt.bind(('', self.fb_port))

		while True:
			try:
				data = fb_skt.recv(1024)
				seq, fid, ftype, fdata = parse_control(data)
				if ftype=='RATE' or ftype=='CSI':
					frame = '%s %d %s %s'%(self.task_id, fid, ftype, fdata)
					self.fb_q.put_nowait(frame)
					pass
				elif ftype=='ACK':
					self.ptr[fid] = fdata
					pass
				elif ftype=='NAK':
					self.encoder.reput(fdata)
					#sWindow shrink on tuple_q[fid]
					pass
				elif ftype=='BIAS': #rx smart sense
					self.encoder.ratio += fdata
					pass
				else:
					raise Exception('control frame exception')
			except Exception as e:
				printh('uplink', e, 'red')
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
