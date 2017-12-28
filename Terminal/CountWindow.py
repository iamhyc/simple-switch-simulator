'''
CountWindow: for data flow manipulation
@author: Mark Hong
@level: debug
'''
import threading
from utility.Data import build_control

class CountWindow:
	"""docstring for CountWindow
	Receiver Phase II: Count Windows as Sliding Window
	"""
	def __init__(self, buffer_q, ringBuffer, fb_q):
		self.paused = True
		self.buffer = buffer_q #0
		self.bWindow = ringBuffer #2
		self.bsize = len(ringBuffer)
		self.fb_q = fb_q
		#internal init
		self.acked = -1 #sliding window bound
		self.sWindow = {} #1; [q1_pos, count, last_ratio, []]
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

	'''
	Process Helper Function
	'''
	def Liquidation(self, maxSeq, rWindow_l):
		if rWindow_l[-1][1][0]==0: #q1 abscence
			self.fb_q.put(build_control(1,'NAK',rWindow_l[-1][0]))
			pass
		while len(rWindow_l):
			Seqi = rWindow_l[-1][0]
			delta = len(rWindow_l[-1][1][3])
			Seqf = max(rWindow_l[-1][1][3])
			if (Seqi-Seqf+1)==delta: #window clear
				self.fb_q.put(build_control(0,'ACK',Seqf))
				self.acked = Seqf
				self.sWindow.pop(Seqi)
				pass
			
			while maxSeq>=Seqi:
				if not maxSeq in rWindow_l[-1][1][3]:
					count += 1
					self.fb_q.put(build_control((maxSeq==Seqi),'NAK',maxSeq))
					pass
				maxSeq -= 1
				pass
			pass
		pass

	def process(self, Seq, Mark, Ratio, Count):
		Seqi = Seq-Count-Mark+1
		last_Ratio = self.sWindow[Seqi][2]
		Seqi_exist = self.sWindow.has_key(Seqi)

		if Seqi_exist and Count<last_Ratio:
			#window accumulation
			self.sWindow[Seqi][1] += 1
			self.sWindow[Seqi][2] = Ratio
			self.sWindow[Seqi][3].append(Seq)
			if Mark==1:
				self.sWindow[Seqi][0] = self.sWindow[Seqi][1]
			pass
		elif not Seqi_exist and (Count<Ratio or Ratio==Count==(1-Mark)==0):
			#window trigger
			self.sWindow[Seqi] = [0, 1, Ratio, [Seq]]
			if Mark==1:
				self.sWindow[Seqi][0] = 1
			rWindow_l = sorted(self.sWindow.items())
			rWindow_index = map(lambda x:x==Seqi, rWindow_l).index(True)
			maxSeq = max(self.sWindow[rWindow_index][3])
			self.Liquidation(maxSeq, rWindow_l[:rWindow_index]) #exclude current window
			pass
		elif Count>=Ratio:
			#window completion
			if not Seqi_exist:
				self.sWindow[Seqi] = [0, 1, Ratio, [Seq]]
			else:
				self.sWindow[Seqi][1] += 1
				self.sWindow[Seqi][2] = Ratio
				self.sWindow[Seqi][3].append(Seq)
				pass
			rWindow_l = sorted(self.sWindow.items())
			rWindow_index = map(lambda x:x==Seqi, rWindow_l).index(True)
			self.Liquidation(Seq, rWindow_l[:rWindow_index+1]) #include current window
			pass
		else:
			printf('Impossible...')
			pass
		pass

	'''
	Process Thread Function
	'''
	def is_alive(self):
		return self.runHandle.is_alive()
		pass

	def runThread(self):
		while not self.paused:
			if not self.buffer.empty():
				frame = self.buffer.get_nowait()
				Seq, Mark, Ratio, Count, Data = frame
				self.bWindow[Seq % self.bsize][0] = Seq
				self.bWindow[Seq % self.bsize][1] = Data #put into buffer straightly
				if Seq > self.acked: #exclude retransmission
					self.process(Seq, Mark, Ratio, Count)
					pass
				pass
			else:
				#inc tx sliding window here#
				pass
			pass
		pass
