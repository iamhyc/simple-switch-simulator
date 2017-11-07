#! /usr/bin/python
'''
Dispatcher: for data flow manipulation
@author: Mark Hong
'''

from time import sleep, ctime
from multiprocessing import Process, Queue
import thread
import socket, select
import binascii


class Distributor(Process):
	"""Non-Blocking running Distributor Process
		@desc 
		@var source:
			data source for this distributor, 
			default as static
		@var queue:
			multiprocess control side
	"""
	udp_wifi_port = 11112#self To port
	udp_vlc_port = 11113#self To port

	def __init__(self, char, queue):
		#1 Internal Init
		Process.__init__(self)
		self.p2c_q, self.fb_q = queue
		self.wifi_ip, self.vlc_ip, self.port = char
		self.ops_map = {
			"set":self.setValue,
			"ratio":self.setRatio,
		}
		#2 Socket Init
		self.setSource("static")
		self.__vlc_skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.__wifi_skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		#3 Socket Queue Init
		self.source = "static" # udp/file_p/static
		self.buffer = Queue()
		self.wifi_q = Queue()
		self.vlc_q = Queue()
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

	def setRatio(self, ratio):
		#Ratio, Start, Stop, Switch
		#need a <Counter Class> first
		pass

	def setSource(self, src):
		if src=='static':
			self.buffer.put("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
			pass
		elif src=='file':
			pass
		elif src=='udp':
			pass
		else:
			pass
		pass

	def _start():
		#init feedback link --> non-blocking check
		thread.start_new_thread(uplinkThread)# args[, kwargs]
		#init transmission link --> idle
		thread.start_new_thread(distXmitThread)
		thread.start_new_thread(vlcXmitThread)
		thread.start_new_thread(wifiXmitThread)
		#init data source --> busy
		thread.start_new_thread(sourceThread)
		pass

	def _stop():
		#close socket here
		#terminate thread here
		pass

	def uplinkThread(self):
		fb_skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		fb_skt.setblocking(0) #Non-blocking Socket
		fb_skt.bind(('', self.port)) #should bind to the wifi_ip

		while True:
			try:
				data = fb_skt.recv(1024)
				self.fb_q.put(' '.join(task_id, cmd))#push into queue straightly
			except Exception as e:
				pass
			sleep(0)#surrender turn
		pass

	def sourceThread(self, src):
		while True:
			sleep(0)#surrender turn
		pass

	def distXmitThread():
		pass

	def vlcXmitThread(self):
		while True:
			if not self.vlc_q.empty():
				data = self.vlc_q.get_nowait()
				__vlc_skt.sendto(data, (self.vlc_ip, udp_vlc_port))
				pass
			sleep(0)#surrender turn
		pass

	def wifiXmitThread(self):
		while True:
			if not self.wifi_q.empty():
				data = self.wifi_q.get_nowait()
				__wifi_skt.sendto(data, (self.wifi_ip, udp_wifi_port))
				pass
			sleep(0)#surrender turn
		pass

	def run(self):
		try: # manipulate with process termination signal
			self._start()
			while True: # main loop for control
				if not self.p2c_q.empty(): # data from Parent queue
					data = self.p2c_q.get_nowait()
					op, cmd = cmd_parse(data)
					self.ops_map[op](cmd)
					pass
				sleep(0)#surrender turn
				pass
		except Exception as e:
			raise e
		finally:
			self._stop()
			pass