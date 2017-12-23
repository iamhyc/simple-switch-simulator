#! /usr/bin/python
'''
QueueEncoder: map one-queue 2 two-queue
@author: Mark Hong
@level: debug
'''
from Utility.Utility import build_options
from Utility.Math import *

class QueueCoder:
	"""docstring for QueueCoder"""
	def __init__(self, tuple_q, ratio_list, sWindow):
		self.tuple_q = tuple(tuple_q)
		self.sWindow = sWindow
		#Tx Ring Bufferd Window
		self.tx_window = [chr(0)] * sWindow
		#Distribution Parameter
		self.ratio = 0 #'+' for q0, '-' for q1
		self.count = 0 #'+' for q0, '-' for q1
		self.seq = 0
		pass

	def class_init(self):
		self.crcGen = crcFactory('crc-8')
		#Cache-and-Go: S[1b]|Seq[4B] + Option[1B] + CRC8[1B]
		#Split-and-Go: T[1b]|Seq[4B] + Order[1B] + CRC8[1B]
		self.frame = struct.Struct('IBB')
		self.buffer = ctypes.create_string_buffer(self.frame.size)
		self.crcFrame = struct.Struct('IB')
		self.crcBuffer = ctypes.create_string_buffer(self.crcFrame.size)
		pass

	def setRatio(self, ratio):
		if sign(ratio)!=sign(self.ratio):
			self.count = 0 #adapt to mutation
		self.ratio = ratio
		pass

	def clearAll(self, numA=0):
		self.tuple_q[0].clear()
		self.tuple_q[1].clear()
		self.seq = numA #restart packet sequence
		pass

	def build_struct(self, index, options, raw):
		#raw_len = len(raw) #useless for now
		seq_singed = ((index&0x01)<<31) & self.seq
		self.crcFrame.pack_into(
			self.crcBuffer, 0,
			seq_singed,#Sequence number
			options,#options section
			)
		crcValue = self.crcGen(self.crcBuffer)
		self.frame.pack_into(
			self.buffer, 0, 
			seq_singed, options, crcValue)
		header = ctypes.string_at(
			ctypes.addressof(self.buffer),
			self.frame.size)
		return (header + raw)

	def reput(self, seq):
		printh('Encoder', 'reput %d'%(seq))
		seq = seq % self.sWindow

		raw = self.tx_window[seq]
		options = build_options(self.ratio, self.count)
		frame = build_struct(raw, options)
		#reput into the favorable side, without count balance
		self.tuple_q[pos(self.ratio)].appendleft(frame)
		pass

	def put(self, raw):
		if abs(self.count) > abs(self.ratio): #critical point
			self.count = 0
			index = 1 - pos(self.ratio)
			options = build_options(self.ratio, self.count)
			frame = build_struct(index, raw, options)
			self.tuple_q[index].append(frame)
			pass
		else: #accumulation process
			index = pos(self.ratio)
			options = build_options(self.ratio, self.count)
			frame = build_struct(index, raw, options)
			self.count += sign(self.ratio)
			self.tuple_q[index].append(frame)
			pass
		#here add for tx_window#
		tmp = self.seq % self.sWindow
		self.tx_window[tmp] = raw
		#sequence number inc
		print(self.seq)
		self.seq += 1
		return True
