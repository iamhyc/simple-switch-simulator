#! /usr/bin/python
'''
Utility: useful function utilities
@author: Mark Hong
@level: release
'''
import json, time, threading
from termcolor import colored, cprint

def load_json(uri):
	try:
		with open(uri) as cf:
			return json.load(cf)
	except Exception as e:
		raise e
	pass

def cmd_parse(str):
	cmd = ''
	op_tuple = str.lower().split(' ')
	op = op_tuple[0]
	if len(op_tuple) > 1:
		cmd = op_tuple[1:]
		pass
	return op, cmd
	pass

def response(status, sock, optional=''):
	if status:
		frame = '+'
	else:
		frame = '-'

	if optional != '':
		frame += optional
	
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

def printh(tip, cmd, color=None):
	print(
		colored('[%s] '%(tip), 'magenta') 
		+ colored(cmd, color)
		+ ' '
		)
	pass

class AlignExecutor:
	"""docstring for SyncExecutor"""
	def __init__(self, p2c_q, c2p_q):
		self.p2c_q = p2c_q
		self.c2p_q = c2p_q
		pass

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
		