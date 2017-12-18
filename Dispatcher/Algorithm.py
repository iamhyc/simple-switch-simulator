#! /usr/bin/python
from Utility.Utility import printh
from multiprocessing import Process, Queue
import threading
from time import sleep
import Queue

def frame_parse(frame):
	return frame.split(' ', 2)
	pass

class Algorithm(Process):
	"""Non-Blocking running Algorithm Process
		@desc
	"""
	def __init__(self, queue):
		#1 Internal Init
		Process.__init__(self)
		self.fb_q, self.a2p_q = queue
		self.tensity = 0.9 #higher for faster response
		#2 Map Init
		self.term_map = {}
		self.const_map = {
			'wifi': 0,
			'vlc': 1
		}
		pass

	def countup(self, frame):
		task_id, link_name, data = frame_parse(frame)
		data = float(data)
		if self.term_map[task_id]:
			index = self.const_map[link_name]
			self.term_map[task_id]['rate'][index] = (
				self.term_map[task_id]['rate'][index] * (1-self.tensity)
				 + data * self.tensity
			)
			pass
		else:#init statistics
			self.term_map[task_id] = {
				'rate':[0, 0]
			}
			pass
		pass

	'''
	Process Thread Function
	'''
	def applyThread(self, interval):
		wifi, vlc = self.const_map['wifi'], self.const_map['vlc']
		while True:
			for (k,v) in self.term_map.items():
				#apply operations, self.a2p_q
				r = v['rate'][wifi] / v['raste'][vlc]
				frame = "%s %s %.2f %.2f"('ratio', k, r/(1+r), 1/(1+r))
				pass
			sleep(interval) #apply periodically
			pass
		pass

	'''
	Process Entrance Function
	'''
	def alg_start(self):
		printh('Algorithm', 'Algorithm is now online...', 'green')
		#3 Thread Handle Init
		self.applyHandle = threading.Thread(target=self.applyThread, args=(5.0,))
		self.applyHandle.setDaemon(True)
		self.applyHandle.start()
		pass

	def alg_stop(self):
		pass

	def alg_exit(self):
		printh('Algorithm', "Now exit...", 'red')
		exit()
		pass

	def run(self):
		self.alg_start()
		try:
			while True:
				if not self.fb_q.empty():
					frame = fb_q.get_nowait()
					self.countup(frame)
					pass
				pass
		except Exception as e:
			printh('Algorithm', e, 'red') #for debug
			pass
		finally:
			self.alg_exit()
