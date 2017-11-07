#! /usr/bin/python
from time import sleep, ctime
from multiprocessing import Process, Queue
import socket, select
import binascii

class Distributor(Process):
	"""Non-Blocking running Distributor Process
		@desc 
		@var source:
			data source for this distributor, 
			default as looped
		@var queue:
			multiprocess control side
	"""
	def __init__(self, task_id, char, queue):
		#1 Internal Init
		Process.__init__(self)
		self.id = task_id
		self.p2c_q, self.fb_q = queue
		self.wifi_ip, self.vlc_ip, self.port = char
		self.ops_map = {
			"set":self.setValue,
			"ratio":self.setRatio,
		}
		#2 Source Thread Init
		self.setSource("static")
		# Socket Queue Init
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
		pass

	def setSource(self, type):
		##self.buffer.put("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
		pass

	def uplinkThread(self):
		fb_skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		fb_skt.setblocking(0)#Non-blocking Socket
		fb_skt.bind(('', self.port))

		while True:
			try:
				data = fb_skt.recv(1024)
				#push into queue straightly
				self.c2p_q.put(' '.join(task_id, cmd))
				pass
			except Exception as e:
				pass
			sleep(0)#surrender turn
		pass

	def sourceThread(self, src):
		sleep(0)#surrender turn
		pass

	def vlcXmitThread():
		sleep(0)#surrender turn
		pass

	def wifiXmitThread():
		sleep(0)#surrender turn
		pass

	def run(self):
		try:
			while True:
				if not self.p2c_q.empty(): # data from Parent queue
					data = self.p2c_q.get_nowait()
					op, cmd = cmd_parse(data)
					self.ops_map[op](cmd)
					pass
				sleep(0)#surrender turn
				pass
			pass
		except Exception as e:
			raise e
		finally:
			#close socket here
			#terminate thread here
			pass