#! /usr/bin/python
'''
Math: useful control function utilities
@author: Mark Hong
@level: release
'''

def parse_frame(frame):
	status = True if frame[0]=='+' else False
	res = '' if len(frame)<1 else frame[1:].split(' ')
	return status, res

def build_frame(status, ftype='', fdata=''):
	if status:
		status = '+'
	else:
		status = '-'
	
	if ftype:
		return "%s%s %s"%(status, ftype, fdata)
	else:
		return "%s%s"%(status, fdata)

def response(status, sock, optional=''):
	frame = build_frame(status, fdata=optional)
	sock.send(frame)
	pass

def request(frame, sock, timeout=None):
	sock.settimeout(timeout)
	sock.send(frame)
	data = sock.recv(1024)
	sock.settimeout(None)
	return parse_frame(data)

class AlignExecutor:
	"""docstring for AlignExecutor"""
	def __init__(self, p2c_q, c2p_q):
		self.p2c_q = p2c_q
		self.c2p_q = c2p_q
		pass

	def ReqFactory(self):
		def req():
			while self.p2c_q.empty(): pass
			data = self.p2c_q.get_nowait()
			return data
			pass
		return req

	def ResFactory(self):
		def res(status, fdata=''):
			frame = build_frame(status, fdata=fdata)
			self.c2p_q.put_nowait(frame)
			return True
			pass
		return res

	def exec_nowait(self, cmd):
		while not self.c2p_q.empty():
			self.c2p_q.get()
			pass
		self.p2c_q.put_nowait(cmd)
		pass

	def exec_wait(self, cmd):
		while not self.c2p_q.empty():
			self.c2p_q.get()
			pass
		self.p2c_q.put(cmd)
		return self.c2p_q.get()
