#! /usr/bin/python
from Utility.Utility import *
from getpass import getuser
from optparse import OptionParser
import platform as pt
import os, time, json, socket

class Console:
	"""docstring for Console"""
	def __init__(self):
		self.ops_map = {}
		self.items = {}
		pass

	def register(self, ops, callback, desc=''):
		for op in ops:
			self.ops_map[op] = callback
			pass
		
		if not desc=='':
			item = ', '.join(ops)
			self.items[item] = desc
			pass
		pass

	def apply(self, op, cmd):
		try:
			if self.ops_map.has_key(op):
				self.ops_map[op](cmd)
			else:
				default_op(op, cmd)
			return True
		except Exception as e:
			return False
		pass

win_pt = "windows" in pt.platform().lower()
def _cls():
	if win_pt:
		t = os.system("cls")
	else:
		t = os.system("clear")
	pass

def helper():
	print("*************************Console Helper**************************")
	print("                 [CLS]   Clear Screen							")
	print("                 [EXEC]  Execute Python Command					")
	print("                 [ALIAS] Show Command Alias						")
	print("                 [HELP]  Display Command Help					")
	print("                 [EXIT]  Exit									")
	print
	pass

def default_op(op, cmd):
	tmp = ' '.join([op]+cmd)
	status, data = request(tmp, skt, 3)
	print(status)
	return status, data

def ls_op_wrapper(cmd=[]):
	status, data = default_op('ls', cmd)
	_cls()
	cprint("%s\n"%(data), 'green')
	pass

def add_op_wrapper(cmd):
	default_op('add', cmd+['1'])
	pass

def src_op_wrapper(cmd):
	default_op('src-set', cmd)
	pass

def srcstop_op_wrapper(cmd):
	#src-set task_id static 0
	cmd = [cmd[0], 'static', chr(0)]
	default_op('src-set', cmd)
	pass

def srcnow_op_wrapper(cmd):
	default_op('src-now', cmd)
	pass

def del_op_wrapper(cmd):
	default_op('exit', cmd)
	pass

def cls_helper_op(cmd):
	_cls()
	helper()
	pass

def alias_helper_op(cmd):
	op = cmd[0]
	if ex.ops_map.has_key(op):
		for (k,v) in ex.items.items():
			if op in k: 
				printh(op, k)
				break
			pass
		if len(cmd)>=2:
			al = cmd[1:]
			ex.register(al, ex.ops_map[op])
			pass
		pass
	else:
		raise Exception('...')
	pass

def internal_helper_op(cmd=[]):
	for (k,v) in ex.items.items():
		tmp = k.split(', ')[0].upper()
		printh(tmp, v, 'yellow', split=':\t')
		pass
	print
	pass

def execute_helper_op(cmd):
	cmd = ' '.join(cmd)
	print(cmd)
	exec(cmd)
	pass

def script_helper_op(cmd):
	cmd = os.path.join('Scripts', cmd[0])
	scripts = open(cmd, 'r').readlines()
	for line in scripts:
		op, cmd = cmd_parse(line)
		if not ex.apply(op, cmd):
			break
		pass
	pass

def main():
	_cls()
	helper()

	if options.sc_file!='':
		ex.apply('script', [options.sc_file])
		pass
	
	while True:
		tipstr = colored('%s @ Simulator:[%s]\n$ '%(localuser, time.ctime()), 'cyan')
		op, cmd = cmd_parse(raw_input(tipstr))
		if ex.apply(op, cmd):
			pass
		else:
			printh(op, '...', 'red')
		pass
	pass

def _print(cmd=[]):
	pass

def _fini(cmd=[]):
	print
	quit()
	pass

def _init():
	global config, localuser, options, ex

	parser = OptionParser()
	parser.add_option("-s", "--server",
		dest="server", 
		default="127.0.0.1", 
		help="Designate the dispatcher server")
	parser.add_option("-c", "--script",
		dest="sc_file", 
		default="", 
		help="Designate the script file")
	(options, args) = parser.parse_args()

	config = load_json('./config.json')
	localuser = getuser()
	ex = Console()
	ex.register([''], _print)
	ex.register(['exit'], _fini)
	ex.register(['clear', 'cls'], cls_helper_op)
	ex.register(['alias', 'a'], alias_helper_op)
	ex.register(['help', 'h'], internal_helper_op)
	ex.register(['exec'], execute_helper_op)
	ex.register(['sc', 'script'], script_helper_op)

	ex.register(['ls'], ls_op_wrapper, 
		'List current clients status from Dispatcher.\n\t' + 
		colored('ls', 'green')
		)
	ex.register(['add'], add_op_wrapper,
		'Register a new CLIENT(for test).\n\t' + 
		colored('add <ip1> <ip2> <rc_flag=1>', 'green')
		)
	ex.register(['del', 'rm', 'kill'], del_op_wrapper,
		'Remove a CLIENT from Dispatcher.\n\t' +
		colored('rm/kill <task_id>', 'green')
		)
	ex.register(['src', 'src-set'], src_op_wrapper,
		'Setup the Source.\n\t' + 
		colored('src <task_id> <type> <data>', 'green')
		)
	ex.register(['now', 'src-now'], srcnow_op_wrapper,
		'Start the Source right now.\n\t' + 
		colored('now/src-now <task_id>', 'green')
		)
	ex.register(['stop', 'src-stop'], srcstop_op_wrapper,
		'Stop the Source right now.\n\t' + 
		colored('stop <task_id>', 'green')
		)
	pass

if __name__ == '__main__':
	_init()

	try:
		skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		skt.connect((options.server, config['converg_disp_port']))
		main()
	except Exception as e:
		cprint('bye', 'red')
		time.sleep(0.3)
		_cls()
		pass
	finally:
		_fini()
