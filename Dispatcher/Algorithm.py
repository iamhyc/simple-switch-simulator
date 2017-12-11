#! /usr/bin/python
from multiprocessing import Process, Queue
from time import sleep

class Algorithm(Process):
	"""Non-Blocking running Algorithm Process
		@desc
	"""
	def __init__(self, queue):
		Process.__init__(self)
		self.fb_q, self.a2p_q = queue

	def run(self):
		try:
			while True:
				#print("hei,heihei")
				sleep(1)
				pass
		except Exception as e:
			#raise e #for debug
			pass
		finally:
			print("<%s> now exit..."%("Algorithm node"))
			exit()
