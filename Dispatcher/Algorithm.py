#! /usr/bin/python
from numpy import *
from multiprocessing import Process, Queue
from time import sleep

class Algorithm(Process):
	"""Non-Blocking running Algorithm Process
		@desc
	"""
	def __init__(self, queue):
		Process.__init__(self)
		self.fb_q, self.c2p_q = queue

	def run(self):
		while True:
			sleep(1)
			pass
		pass
		