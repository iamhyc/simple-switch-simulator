#! /usr/bin/python
'''
Aggregator: for data flow manipulation
@author: Mark Hong
'''
import socket, Queue
import json, binascii, struct
import threading, multiprocessing
from sys import maxint
from time import ctime, sleep, time
from Utility.Utility import cmd_parse, printh

def build_frame(status, ftype='', fdata=''):
	if status:
		status = '+'
	else:
		status = '-'
	
	if ftype:
		return "%s%s %s"%(status, ftype, fdata)
	else:
		return "%s%s"%(status, fdata)

def unpack_helper(fmt, data):
	    size = struct.calcsize(fmt)
	    return struct.unpack(fmt, data[:size]), data[size:]

class Aggregator(multiprocessing.Process):
	"""docstring for Aggregator

	"""
	def __init__(self, queue, fb_tuple):
		super(Aggregator, self).__init__()
		self.numA = 0#beginSequence
		self.numB = -1#endSequence
		self.redist_paused = True
		self.proc_paused = True
		self.p2c_q, self.c2p_q = queue
		self.fb_tuple = fb_tuple
		self.src_type = 'r' #default for stream
		self.ops_map = {
			'set':self.setParam,
			'type':self.setType
		}

		with open('config.json') as cf:
		 	self.config = json.load(cf)
			pass
		# RingBuffer Init
		# ringBuffer = [Seq, Size, sub1_Size, sub2_Size, Data]
		self.ringBuffer = [0] * self.config['sWindow_rx']
		pass

	def class_init(self):
		self.init_ringbuffer()
		# feedback init
		self.fb_skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #uplink feedback socket
		self.redist_q = Queue.Queue()
		self.fb_q = Queue.Queue()
		#Thread Handle Init
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
		self.procHandle = threading.Thread(target=self.processThread, args=())
		self.procHandle.setDaemon(True)
		pass

	'''
	Process Helper Function
	'''
	def response(self, status, ftype='', fdata=''):
		frame = build_frame(status, ftype, fdata)
		self.c2p_q.put_nowait(frame)
		return True

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
		proc_stop()
		redist_stop()

		self.fhash, fsize, flength, self.src_type = cmd
		self.size = int(fsize)
		flength = float(flength)

		self.numB = math.ceil(fsize / flength) - 1
		if self.numB<0:
			self.numB = maxint
			pass

		#self.remains = self.size - self.numB*flength #zeros in last packet
		
		redist_start()
		proc_start()
		response(True)
		pass

	def setType(self, src_type):
		self.src_type = src_type
		response(True)
		pass

	def redist_stop(self):
		self.redist_paused = True
		self.redist_q.queue.clear()
		pass

	def redist_start(self):
		self.redist_paused = False
		if self.src_type=='r':
			self.redistUDPThread.start()
		else:
			self.redistFileHandle.start()
		pass

	def proc_stop(self):
		self.proc_paused = True
		self.init_ringbuffer()
		pass

	def proc_start(self):
		self.proc_paused = False
		self.wifiRecvHandle.start()
		self.vlcRecvHandle.start()
		if not self.src_type=='r':
			self.procHandle.start()
		pass

	'''
	Process Thread Function
	'''
	def uplinkThread(self, fb_q):
		while not fb_q.empty:
			frame = fb_q.get_nowait()
			self.fb_skt.sendto(frame, self.fb_tuple)
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
		redist_fp = open(self.fhash, 'r+b')
		#redist_fp.fillin(chr(0), self.size) #not needed

		seq_map = [0] * self.numB
		ptr, tot = 0, 2*self.numB

		while not self.redist_paused and tot>0:
			
			while not redist_q.empty():
				raw = redist_q.get_nowait()
				(Seq, Size, Offset, CRC), Data = unpack_helper(self.config['struct'], raw)
				#print('Redistributed Data: %s'%(data))
				redist_fp.seek(Seq*Size + Offset)
				redist_fp.write(Data)

				if seq_map[Seq] < 2:
					seq_map[Seq] += 1
					tot -=1
					pass
				pass

			while ptr <= self.numB and seq_map[ptr]==2: ptr = (ptr+1) % (self.numB+1)
			feedback(False, fdata=ptr) #retransmission
			sleep(0.05) #wait for transmission
			pass
		
		redist_fp.truncate(self.size) #remove extra zeros
		redist_fp.close()
		pass

	def RecvThread(self, name, port):
		recv_skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		recv_skt.bind(('', port))

		while self.proc_paused:
			last_time = time()
			raw, addr = recv_skt.recvfrom(4096)

			if self.src_type=='r':
				(Seq, Size, Offset, CRC), Data = unpack_helper(self.config['struct'], raw)
				data_len = len(Data)
				#print('From %s link:(%d,%d,%d,%d,%s)'%(name, Seq, Size, Offset, CRC, Data)) #for debug
				ptr = Seq % self.config['sWindow_rx']
				if ringBuffer[ptr][0] != Seq:
					ringBuffer[ptr] = [Seq, Size - data_len, [chr(0)]*Size]
					ringBuffer[ptr][2][Offset:Offset+data_len] = Data
					pass
				else:
					ringBuffer[ptr][2][Offset:Offset+data_len] = Data
					ringBuffer[ptr][1] -= data_len
					pass
				pass
			else: #src_type=='c'
				self.redist_q.put_nowait(raw)
				pass

			rate_inst = data_len / time() - last_time
			feedback(True, name, '%d'%(rate_inst))
			pass
		pass

	def processThread(self): #for relay only
		while ringBuffer[0][0] != self.numA:
			sleep(0.1) # wait
			pass

		cnt, ptr = 0, 0
		timeout = time() # packet time counter
		while cnt <= self.numB and not self.proc_paused:
			ptr = (cnt % self.config['sWindow_rx'])
			if time()-timeout < self.config['Atimeout']:
				if ringBuffer[ptr][0] == cnt: #assume: writing not over reading
					timeout = time() # subpacket time counter

					sub_verified = False
					while time()-timeout < self.config['Btimeout']:
						if ringBuffer[ptr][1] == 0:
							redist_q.put_nowait(''.join(ringBuffer[ptr][2]))
							sub_verified = True
							break
						pass

					timeout = time() # reset subpacket time counter
					cnt += 1
					ptr = (cnt % self.config['sWindow_rx'])
					if sub_verified:
						print(cnt)
					else:
						print("subPacket loss in %d."%(cnt))
					pass
				pass
			else: # packet loss
				timeout = time() # reset packet time counter
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
				if not self.p2c_q.empty():
					data = self.p2c_q.get_nowait()
					op, cmd = cmd_parse(data)
					self.ops_map[op](cmd)
					pass
				pass
		except Exception as e:
			printh('Aggregator', e, 'red') #for debug
		finally:
			self.agg_exit()
