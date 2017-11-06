
import multiprocessing 
import Queue

class Distributor(Process):
	"""Non-Blocking running Distributor Process
		@desc 
		@var source:
			data source for this distributor, 
			default as looped
		@var queue:
			multiprocess control side
	"""
	def __init__(self, char, queue):
		Process.__init__(self)
		self.source = "static" # udp/file_p/static
		self.__wifi_q = Queue()
		self.__vlc_q = Queue()
		self.buffer = Queue()
		#self.buffer.put("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
		pass
	
	def setSource(self, type):
		pass

	def uplinkThread(self):
		pass

	def sourceThread(self, src):
		pass

	def run(self):
		while True:
			#self.state_map[self.state]()
			pass
		pass