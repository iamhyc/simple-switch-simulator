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
from Utility.Utility import *

class Aggregator(multiprocessing.Process):
	"""docstring for Aggregator

	"""
	def __init__(self, rf_tuple, fb_tuple):
		super(Aggregator, self).__init__()
		self.numA = 0#beginSequence
		self.numB = -1#endSequence
		self.redist_paused = True
		self.proc_paused = True
		self.req, self.res = rf_tuple
		self.fb_tuple = fb_tuple
		self.src_type = 'r' #default for stream
		self.ops_map = {
			'set':self.setParam,
			'type':self.setType
		}
		self.config = load_json('./config.json')
		# RingBuffer Init
		# ringBuffer = [Seq, Size, sub1_Size, sub2_Size, Data]
		self.ringBuffer = [0] * self.config['sWindow_rx']
		pass

	def thread_init(self):
		self.wifiRecvHandle = threading.Thread(target=self.RecvThread, args=('wifi', self.config['stream_wifi_port']))
		self.wifiRecvHandle.setDaemon(True)

		self.vlcRecvHandle = threading.Thread(target=self.RecvThread, args=('vlc', self.config['stream_vlc_port_rx']))
		self.vlcRecvHandle.setDaemon(True)

		self.redistFileHandle = threading.Thread(target=self.redistFileThread, args=(self.redist_q, ))
		self.redistFileHandle.setDaemon(True)

		self.redistUDPHandle = threading.Thread(target=self.redistUDPThread, args=(self.redist_q, ))
		self.redistUDPHandle.setDaemon(True)

		self.uplinkHandle = threading.Thread(target=self.uplinkThread, args=(self.fb_q, ))
		self.uplinkHandle.setDaemon(True)

		self.procHandle = threading.Thread(target=self.processThread, args=(self.redist_q, ))
		self.procHandle.setDaemon(True)
		pass

	def class_init(self):
		# feedback init
		self.fb_skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #uplink feedback socket
		self.fb_q = Queue.Queue()
		self.redist_q = Queue.Queue()
		# Thread Handle Init
		self.init_ringbuffer()
		self.thread_init()
		pass

	'''
	Process Helper Function
	'''
	def feedback(self, status, ftype='', fdata=''):
		frame = build_frame(status, ftype, fdata)
		self.fb_q.put_nowait(frame)
		pass

	def init_ringbuffer(self):
		for x in xrange(self.config['sWindow_rx']):
			self.ringBuffer[x] = [-1, -1, 0, 0, [chr(0)] * 4096]
			pass
		pass

	def setParam(self, cmd):
		self.proc_stop()
		self.redist_stop()
		self.init_ringbuffer()
		#setup parameter
		self.src_type, self.fhash, fsize, flength = cmd
		self.size = int(fsize)
		flength = float(flength)
		#setup endpoint
		self.numB = int(math.ceil(self.size / flength))
		if self.numB<=0:#endless
			self.numB = maxint
			pass
		#self.remains = self.size - self.numB*flength #zeros in last packet
		self.thread_init()
		self.redist_start()
		self.proc_start()
		self.res(True)
		pass

	def setType(self, src_type):
		self.src_type = src_type
		self.res(True)
		pass

	def redist_stop(self):
		self.redist_paused = True
		if self.redistFileHandle.is_alive():
			self.redistFileHandle.join()
		if self.redistUDPHandle.is_alive():
			self.redistUDPHandle.join()
		self.redist_q.queue.clear()
		pass

	def proc_stop(self):
		self.proc_paused = True
		if self.wifiRecvHandle.is_alive():
			self.wifiRecvHandle.join()
		if self.vlcRecvHandle.is_alive():
			self.vlcRecvHandle.join()
		if self.procHandle.is_alive():
			self.procHandle.join()
		if self.uplinkHandle.is_alive():
			self.uplinkHandle.join()
		pass

	def redist_start(self):
		self.redist_paused = False
		if self.src_type=='r':
			self.redistUDPHandle.start()
		else:
			self.redistFileHandle.start()
		pass

	def proc_start(self):
		self.proc_paused = False
		self.wifiRecvHandle.start()
		self.vlcRecvHandle.start()
		self.uplinkHandle.start()
		if self.src_type=='r':
			self.procHandle.start()
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

	def redistUDPThread(self, redist_q):
		redist_skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

		while not self.redist_paused:
			if not redist_q.empty():
				data = redist_q.get_nowait()
				#print('Redistributed Data: %s'%(data))
				redist_skt.sendto(data, ('localhost', self.config['content_client_port']))#redistribution
			pass
		pass

	def redistFileThread(self, redist_q):
		redist_fp = open(path.join('Files', self.fhash), 'w+b')
		#redist_fp.fillin(chr(0), self.size) #not needed

		seq_map = [{'flag':False} for x in xrange(self.numB)]
		ptr, tot = 0, self.numB

		while not self.proc_paused and redist_q.empty():
			time.sleep(0.1) # wait
			pass

		while not self.redist_paused and tot>0:
			while not redist_q.empty():
				raw = redist_q.get_nowait()
				#print('Redistributed Data: %s'%(raw)) #for debug
				(Seq, Size, Offset, CRC), Data = unpack_helper(self.config['struct'], raw)
				seq_map[Seq][str(Offset)] = len(Data)
				redist_fp.seek(Seq*Size + Offset)
				redist_fp.write(Data)

				if sum(seq_map[Seq].values())==Size:
					seq_map[Seq]['flag'] = True
					tot -=1
					pass
				pass

			while ptr<self.numB and seq_map[ptr]['flag']:
				print(ptr)
				ptr = ptr + 1 #% (self.numB)
				pass

			if ptr<self.numB:
				print('Loss: %d'%(ptr))
				self.feedback(False, fdata=ptr) #retransmission
				time.sleep(0.001) #wait for transmission
				pass
			pass
		
		redist_fp.truncate(self.size) #remove extra zeros
		redist_fp.close()
		printh('Aggregator', 'End of File', 'red')
		pass

	def RecvThread(self, name, port):
		recv_skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		recv_skt.bind(('', port))
		recv_skt.setblocking(False)
		printh(name.upper(), 'Now on', 'green')

		while not self.proc_paused:
			try:
				last_time = time.time()
				raw, addr = recv_skt.recvfrom(4096)

				if self.src_type=='r':
					(Seq, Size, Offset, CRC), Data = unpack_helper(self.config['struct'], raw)
					data_len = len(Data)
					#print('From %s link:(%d,%d,%d,%d,%s)'%(name, Seq, Size, Offset, CRC, Data)) #for debug
					ptr = Seq % self.config['sWindow_rx']
					if self.ringBuffer[ptr][0] != Seq:
						self.ringBuffer[ptr] = [Seq, Size - data_len, [chr(0)]*Size]
						self.ringBuffer[ptr][2][Offset:Offset+data_len] = Data
						pass
					else:
						self.ringBuffer[ptr][2][Offset:Offset+data_len] = Data
						self.ringBuffer[ptr][1] -= data_len
						pass
					pass
				else: #src_type=='c'
					self.redist_q.put_nowait(raw)
					pass

				rate_inst = data_len / (time.time() - last_time)
				self.feedback(True, name, '%d'%(rate_inst))
				pass
			except Exception as e:
				pass
			pass
		pass

	def processThread(self, redist_q): #for relay only
		while self.ringBuffer[0][0] != self.numA and not self.proc_paused:
			time.sleep(0.1) # wait
			pass

		cnt, ptr = 0, 0
		timeout = time.time() # packet time counter
		while cnt <= self.numB and not self.proc_paused:
			ptr = (cnt % self.config['sWindow_rx'])
			if time.time()-timeout < self.config['Atimeout']:
				if self.ringBuffer[ptr][0] == cnt: #assume: writing not over reading
					timeout = time.time() # subpacket time counter

					sub_verified = False
					while time.time()-timeout < self.config['Btimeout']:
						if self.ringBuffer[ptr][1] == 0:
							redist_q.put_nowait(''.join(self.ringBuffer[ptr][2]))
							sub_verified = True
							break
						pass

					timeout = time.time() # reset subpacket time counter
					cnt += 1
					ptr = (cnt % self.config['sWindow_rx'])
					if sub_verified:
						print(cnt)
					else:
						print("subPacket loss in %d."%(cnt))
					pass
				pass
			else: # packet loss
				timeout = time.time() # reset packet time counter
				cnt += 1
				ptr = (cnt % self.config['sWindow_rx'])
				print("Packet %d loss."%(cnt))
				pass
			pass
		#after the aggregation process
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
				op, cmd = data[0], data[1:]
				self.ops_map[op](cmd)
				pass
		except Exception as e:
			printh('Aggregator', e, 'red') #for debug
		finally:
			self.agg_exit()
