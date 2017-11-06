
from multiprocessing import Process, Queue

class Algorithm(Process):
	"""Non-Blocking running Algorithm Process
		@desc
	"""
	def __init__(self, arg):
		super(Algorithm, self).__init__()
		self.arg = arg

	def run(self):
		pass
		