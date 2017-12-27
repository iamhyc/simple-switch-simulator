'''
SourceService: for data flow manipulation
@author: Mark Hong
@level: debug
'''
import socket, struct, threading
from Utility.Utility import printh
from Utility.Data import build_control

class RelayService:
	"""docstring for RelayService
	Receiver Phase III(Stream): Buffer Window, Fatal Sense
	"""
	def __init__(self, ringBuffer, fb_q):
		self.paused = True
		self.ringBuffer = ringBuffer
		self.fb_q = fb_q
		pass

	def feedback(self):
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
		pass

class CacheService:
	"""docstring for CacheService
	Receiver Phase III(Content): Buffer Window, Fatal Sense
	"""
	def __init__(self, ringBuffer, fb_q):
		self.paused = True
		self.ringBuffer = ringBuffer
		self.fb_q = fb_q
		pass

	def init_ringbuffer(self):
		# redist_fp = open(path.join('Files', self.fhash), 'w+b')
		# redist_fp.truncate(self.size) #remove extra zeros
		# redist_fp.close()
		# printh('Aggregator', 'End of File', 'red')
		pass

	def feedbackThread(self):
		pass

	def processThread(self):
		pass
