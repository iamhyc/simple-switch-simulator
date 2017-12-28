'''
SourceService: for data flow manipulation
@author: Mark Hong
@level: debug
'''
import time, threading
from Utility.Utility import printh
from Utility.Data import build_control

class RelayService:
	"""docstring for RelayService
	Receiver Phase III(Stream): Buffer Window, Fatal Sense
	"""
	def __init__(self, redist_port, numB, ringBuffer, fb_q):
		self.paused = True
		self.port = redist_port
		self.ringBuffer = ringBuffer
		self.bsize = len(ringBuffer)
		self.fb_q = fb_q
		#internal init
		self.acked = 0
		pass

	def feedback(self, fb_frame):
		#build_control(0, 'RATE', inst_rate)
		#build_control(0, 'ACK', seq)
		#build_control(0, 'NAK', seq)
		#build_control(0, 'BIAS', pos)
		self.fb_q.put(fb_frame)
		pass

	def start(self):
		self.paused = False
		self.processHandle = threading.Thread(target=processThread,
				args=(0.5, ))
		self.processHandle.setDaemon(True)
		self.processHandle.start()
		pass

	def stop(self):
		self.paused = True
		pass

	def is_alive(self):
		return self.processHandle.is_alive()
		pass

	def processThread(self ,timeout):
		redist_skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		#redist_skt.sendto(data, ('', self.port))
		while not self.paused:
			last_time = time.time()
			while time.time()-last_time<0.3: #timeout with 0.3s
				index = self.acked % self.bsize
				if self.ringBuffer[index][0]==self.acked:
					redist_skt.sendto(self.ringBuffer[index][1], ('', self.port))
					self.acked += 1
					last_time = time.time()
					pass
				pass
			#fail with timeout
			self.fb_q.put(build_control(0,'NAK',self.acked))
			pass
		pass

class CacheService:
	"""docstring for CacheService
	Receiver Phase III(Content): Buffer Window, Fatal Sense
	"""
	def __init__(self, char_t, ringBuffer, fb_q):
		self.paused = True
		self.fhash, self.numB, self.size, self.length = char_t
		self.ringBuffer = ringBuffer
		self.bsize = len(ringBuffer)
		self.fb_q = fb_q
		pass

	def start(self):
		self.paused = False
		self.processHandle = threading.Thread(target=processThread,
				args=(0.5, ))
		self.processHandle.setDaemon(True)
		self.processHandle.start()
		pass

	def stop(self):
		self.paused = True
		pass

	def is_alive(self):
		return self.processHandle.is_alive()
		pass

	def processThread(self):
		redist_fp = open(path.join('Files', self.fhash), 'w+b')
		#redist_fp.fillin(chr(0), self.size) #not needed
		tot = self.numB
		seq_map = [time.time()] * self.numB

		while not self.paused and tot>0:
			itert, ptr, maxB = 0, 0, 0
			index = ptr % self.bsize
			while ptr<=self.numB:
				thisB = self.ringBuffer[index][0]
				if seq_map[ptr]!=-1:
					if thisB==ptr:
						redist_fp.seek(ptr*self.length)
						redist_fp.write(self.ringBuffer[index][1])
						maxB = thisB #update maxB for this iteration
						tot -= 1
						seq_map[ptr] = -1
						pass
					elif time.time()-seq_map[ptr]>1.0: #timeout with 1s
						self.fb_q.put(build_control(0,'NAK',ptr))
						seq_map[ptr] = time.time()
						pass
					pass
				ptr += 1
				pass
			print('iteration %d: %d'%(itert, maxB))
			pass

		redist_fp.truncate(self.size) #remove extra zeros
		redist_fp.close()
		printh('Aggregator', 'End of File', 'red')
		pass
