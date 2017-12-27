'''
SourceService: for data flow manipulation
@author: Mark Hong
@level: debug
'''
import threading

class CountWindow:
	"""docstring for CountWindow
	Receiver Phase II: Count Windows as Sliding Window
	"""
	def __init__(self, buffer_q, ringBuffer, fb_q):
		self.paused = True
		self.buffer = buffer_q #0
		self.bWindow = ringBuffer #2
		self.fb_q = fb_q
		#internal init
		self.selected = 0 #q0, 0 for Wi-Fi, 1 for VLC
		self.sWindow = {} #1;hash for sort
		#countWindow = [Seq, Ratio, Count, Data]
		pass

	def clear(self, number): #ACK window
		pass

	def process(self):
		if not self.buffer.empty():
			frame = self.buffer.get_nowait()
			Seq, Index, Ratio, Count, Data = frame
			pass
		else:
			#inc tx sliding window here#
			pass
		pass

	def start(self):
		self.paused = False
		self.runHandle = threading.Thread(target=self.runThread)
		self.runHandle.setDaemon(True)
		self.runHandle.start()
		pass

	def stop(self):
		self.paused = True
		pass

	def is_alive(self):
		return self.runHandle.is_alive()
		pass

	def runThread(self):
		while not self.paused: self.process
		pass
