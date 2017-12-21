#! /usr/bin/python
'''
Utility: useful function utilities
@author: Mark Hong
@level: release
'''
import json, time, struct, threading
from termcolor import colored, cprint
#import greenlet

def load_json(uri):
	try:
		with open(uri) as cf:
			return json.load(cf)
	except Exception as e:
		raise e
	pass

def cmd_parse(str):
	op, cmd = '', []
	op_tuple = str.lower().strip().split(' ')
	op = op_tuple[0]
	if len(op_tuple) > 1:
		cmd = op_tuple[1:]
		pass
	return op, cmd
	pass

def unpack_helper(fmt, data):
	    size = struct.calcsize(fmt)
	    return struct.unpack(fmt, data[:size]), data[size:]

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
	status = True if data[0]=='+' else False
	sock.settimeout(None)
	res = '' if len(data)<1 else data[1:]
	return status, res
	pass

def exec_watch(process, hook=None, fatal=False, gen=True):
	if gen:#external loop
		process.start()
		t = threading.Thread(target=exec_watch, args=(process, hook, fatal, False))
		t.setDaemon(True)
		t.start()
		pass
	else:#internal loop
		while process.is_alive():
			time.sleep(0.1)
			pass
		if fatal and hook: hook()
		pass
	pass

def printh(tip, cmd, color=None, split=' '):
	print(
		colored('[%s]%s'%(tip, split), 'magenta')
		+ colored(cmd, color)
		+ ' '
		)
	pass

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
		