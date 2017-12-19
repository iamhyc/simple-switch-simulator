#! /usr/bin/python
from Utility.Utility import *
from getpass import getuser
import platform as pt
import os, time, json, socket

global localuser, remote_cmdip
global skt, config

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
	print("                 [SRC]   Change a Client Source					")
	print("                 [STOP]  Stop a Client Source					")
	print("                 [NOW]   Start a Client Source					")
	print("                 [SC]    Execute Script File						")
	print("                 [CLS]   Clear screen							")
	print("                 [EXIT]  Exit									")
	print
	pass

def script_file(file):
	pass

def main():
	global skt
	skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	try:
		skt.connect(('localhost', config['converg_disp_port']))
	except Exception as e:
		cprint('bye', 'red')
		time.sleep(0.5)
		raise e

	_cls()
	helper()
	while True:
		tipstr = colored(localuser+" @ Aggregator:["+time.ctime()+"]\n$ ", 'cyan')
		op, cmd = cmd_parse(raw_input(tipstr))

		try:
			if op=='ls':
				status, data = request('ls', skt, 3)
				_cls()
				cprint("%s\n"%(data), 'green')
				helper()
				pass
			elif op=='add' and len(cmd)>=2:
				#'<command> <ip1> <ip2>'
				tmp = ('%s %s %s 1'%('add', cmd[0], cmd[1]))
				status, data = request(tmp, skt, 3)
				print(status)
				pass
			elif op=='src' and len(cmd)>=3:
				#'<command> <task_id> <type> <data>'
				tmp = ('%s %s %s %s'%('src-set', cmd[0], cmd[1], cmd[2]))
				status, data = request(tmp, skt, 3)
				print(status)
				pass
			elif op=='stop' and len(cmd)>=1:
				#'<command> <task_id> <type> <data>'
				tmp = 'src-set %s static %s'%(cmd[0], chr(0))
				status, data = request(tmp, skt, 3)
				print(status)
				pass
			elif op=='now' and len(cmd)>=1:
				#'<command> <task_id> <type> <data>'
				tmp = ('%s %s'%('src-now', cmd[0]))
				status, data = request(tmp, skt, 3)
				print(status)
				pass
			elif op=='rm' or op=='kill' and len(cmd)>=1:
				#'<command> <task_id>'
				tmp = ('%s %s'%("exit", cmd[0]))
				status, data = request(tmp, skt, 3)
				print(status)
				pass
			elif op=='sc' and len(cmd)>=1:
				script_file(cmd[0])
				pass
			elif op=='exec' and len(cmd)>=1:
				exec(cmd[0])
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
				printh(op, 'Command Format Error', 'red')
			pass
		except Exception as e:
			#raise e #for debug
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
		pass
	finally:
		exit()
