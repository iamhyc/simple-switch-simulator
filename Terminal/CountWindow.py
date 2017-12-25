#! /usr/bin/python
'''
SourceService: for data flow manipulation
@author: Mark Hong
@level: debug
'''
import threading

class CountWindow(threading.Thread):
	"""docstring for CountWindow
	Receiver Phase I: Count Windows as Sliding Window
	"""
	def __init__(self, buffer_q, bWindow):
		self.paused = True
		#countWindow = [Seq, Ratio, Count, Data]
		self.selected = 0 #q0
		self.buffer = buffer_q
		self.sWindow = {} #hash for sort
		self.bWindow = ringBuffer
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

	def stop(self):
		self.paused = True
		pass

	def run(self):
		while not self.paused: self.process
		pass