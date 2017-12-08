#! /usr/bin/python
import os, time, json
from termcolor import colored, cprint
from getpass import getuser
import platform as pt
import socket

global localuser, remote_cmdip
global config

win_pt = "windows" in pt.platform().lower()

def _cls():
	if win_pt:
		t = os.system("cls")
	else:
		t = os.system("clear")
	pass

def helper():
	print("************************Console Helper************************")
	print("                 [LS]    Current Client Process					")
	print("                 [ADD]   Add a Client							")
	print("                 [RM]    Remove a Client							")
	print("                 [SW]    Switch a Client Link					")
	print("                 [SC]    Execute Script File						")
	print("                 [CLS]   Clear screen							")
	print("                 [EXIT]  Exit									")
	print
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

def script_file(file):
	pass

def request(frame, timeout=None):
	skt.settimeout(timeout)
	skt.send(frame)
	data = skt.recv()
	skt.settimeout(None)
	
	return data[0], data[1:]
	pass

def main():
	global skt
	skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	skt.connect(('', config['converg_disp_port']))

	_cls()
	helper()
	while True:
		tipstr = colored(localuser+" @ Aggregator:["+time.ctime()+"]\n$ ", 'cyan', 'on_grey')
		op, cmd = cmd_parse(raw_input(tipstr))

		try:
			if op=='ls':
				status, data = request('ls', 3)
				_cls()
				cprint("%s\n"%(data), 'green')
				helper()
				pass
			elif op=='add' and len(cmd)>=2:
				#'<command> <ip1> <ip2>'
				tmp = ('%s %s %s'%('add', cmd[0], cmd[1]))
				status, data = request(tmp, 3)
				print(tmp)
				pass
			elif op=='rm' or op=='kill' and len(cmd)>=1:
				#'<command> <task_id>'
				tmp = ('%s %s'%("rm", cmd[0]))
				status, data = request(tmp, 3)
				print(tmp)
				pass
			elif op=='sc' and len(cmd)>=1:
				script_file(cmd[1])
				pass
			elif op=='clear' or op=='cls':
				_cls()
				helper()
				pass
			elif op=='exit':
				print
				quit()
				pass
			else:
				cprint("Not Supported Format or Command.", 'red')
			pass
		except Exception as e:
			#raise e ##for debug
			cprint("...", 'red')
			pass
		pass
	pass

if __name__ == '__main__':
	with open('./config.json') as cf:
		config = json.load(cf)

	localuser = getuser()
	remote_cmdip = 'localhost'

	try:
		main()
	except Exception as e:
		_cls()
	finally:
		exit()