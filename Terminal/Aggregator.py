#! /usr/bin/python
'''
Aggregator: for data flow manipulation
@author: Mark Hong
'''
import socket, Queue
import json, binascii, struct
import threading, multiprocessing

global fb_skt, fb_port, redist_skt, redist_q
global wifiRecvHandle, vlcRecvHandle, redistHandle

def cmd_parse(str):
	cmd = ''
	op_tuple = str.lower().split(' ')
	op = op_tuple[0]
	if len(op_tuple) > 1:
		cmd = op_tuple[1:]
		pass
	return op, cmd
	pass

def unpack_helper(fmt, data):
	    size = struct.calcsize(fmt)
	    return struct.unpack(fmt, data[:size]), data[size:]

class Aggregator(multiprocessing.Process):
	"""docstring for Aggregator

	"""
	def __init__(self, queue, fb_port):
		super(Aggregator, self).__init__()
		self.numA = 0#beginSequence
		self.numB = -1#endSequence
		self.redist_paused = True
		self.proc_paused = True
		self.p2c_q, self.c2p_q = queue
		self.fb_port = fb_port
		self.src_type = 'r' #default for stream
		self.ops_map = {
			'set':self.setParam,
			'type':self.setType
		}

		with open('../config.json') as cf:
		 	self.config = json.load(cf)
			pass
		# RingBuffer Init
		# ringBuffer = [Seq, Size, sub1_Size, sub2_Size, Data]
		self.ringBuffer = [0] * self.config['sWindow_rx']
		for x in xrange(self.config['sWindow_rx']):
			self.ringBuffer[x] = [-1, -1, 0, 0, [chr(0)] * 4096]
			pass
		
		#Thread Handle Init
		self.redist_q = Queue.Queue()
		fb_skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.wifiRecvHandle = Thread(target=self.RecvThread, args=('Wi-Fi', self.config['stream_wifi_port']))
		self.vlcRecvHandle = Thread(target=self.RecvThread, args=('VLC', self.config['stream_vlc_port_rx']))
		self.redistFileHandle = Thread(target=redistFileThread, args=(redist_q, ))
		self.redistUDPHandle = Thread(target=redistUDPThread, args=(redist_q, ))
		self.wifiRecvHandle.setDaemon(True)
		self.vlcRecvHandle.setDaemon(True)
		self.redistFileHandle.setDaemon(True)
		self.redistUDPHandle.setDaemon(True)
		pass

	'''
	Process Helper Function
	'''
	def response(self, status, frame=''):
		if status:
			data = '+'
		else:
			data = '-'

		self.c2p_q.put_nowait(data + frame)
		return True

	def setParam(self, cmd):
		self.fhash, fsize, flength, self.src_type = cmd
		self.size = int(fsize)
		self.numB = math.ceil(fsize / float(flength))
		response(True)
		pass

	def setType(self, src_type):
		self.src_type = src_type
		response(True)
		pass

	def redistUDPThread(self, redist_q):
		redist_skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

		while not self.redist_paused:
			if not redist_q.empty():
				data = redist_q.get_nowait()
				#print('Redistributed Data: %s'%(data))
				redist_skt.sendto(data, ('localhost', 12306))#redistribution
			pass
		pass

	def redistFileThread(self, redist_q):
		redist_fp = open(self.file_name, 'wb')

		while not self.redist_paused:
			if not redist_q.empty():
				data = redist_q.get_nowait()
				#print('Redistributed Data: %s'%(data))
				redist_fp
				redist_fp.write(data)
				pass
			pass
		pass

	def RecvThread(self, name, port):
		recv_skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		recv_skt.bind(('', port))

		while True:
			raw, addr = recv_skt.recvfrom(4096)
			(Seq, Size, Offset, CRC), Data = unpack_helper(self.config['struct'], raw)
			#print('From %s link:(%d,%d,%d,%d,%s)'%(name, Seq, Size, Offset, CRC, Data)) #for debug

			ptr = Seq % self.config['sWindow_rx']
			if ringBuffer[ptr][0] != Seq:
				ringBuffer[ptr] = [Seq, Size - len(Data), [chr(0)]*Size]
				ringBuffer[ptr][2][Offset:Offset+len(Data)] = Data
				pass
			else:
				ringBuffer[ptr][2][Offset:Offset+len(Data)] = Data
				ringBuffer[ptr][1] -= len(Data)
				pass
			#statistical collection here
	    	#print(os.getpid())
	    	sleep(0) #surrender turn
		pass

	def recvStart():
		if self.src_type=='c':#cache type
			redistFileThread.start()
		else:
			redistUDPHandle.start()

		redistHandle.start()
		wifiRecvHandle.start()
		vlcRecvHandle.start()
		pass

	def process(self):
		recvStart()
		# should with start and end seq
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
		print("Aggregator now exit...")
		exit()
		pass

	def run(self):
		try:
			while True:
				if not self.p2c_q.empty():
					data = self.p2c_q.get_nowait()
					op, cmd = cmd_parse(data)
					self.ops_map[op](cmd)
					pass
				pass
		except Exception as e:
			raise e
		pass
