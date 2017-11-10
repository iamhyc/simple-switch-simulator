#! /usr/bin/python
import os, time, json
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
	print("                 [RUN]   Start a Client 							")
	print("                 [STOP]  Stop a Client 							")
	print("                 [SW]    Switch a Client Link					")
	print("                 [SC]    Execute Script File						")
	print("                 [CLS]   Clear screen							")
	print("                 [EXIT]  Exit									")
	print
	pass

def cmd_parse(str):
	cmd = ''
	op_tuple = str.lower().split(' ', 1)
	op = op_tuple[0]
	if len(op_tuple) > 1:
		cmd = op_tuple[1].split(' ')
		pass
	return op, cmd
	pass

def script_file(file):
	pass

def main():
	skt_cmd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	skt_recv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	skt_recv.settimeout(3.0)#3 seconds
	skt_recv.bind(('', config['udp_client_port']))

	_cls()
	helper()
	while True:
		tipstr = localuser+"@Aggregator:["+time.ctime()+"]$ "
		op, cmd = cmd_parse(raw_input(tipstr))

		try:
			if op=='ls':
				skt_cmd.sendto('ls', (remote_cmdip, config['udp_server_port']))
				data, ADDR = skt_recv.recvfrom(1024)
				_cls()
				print("%s\n"%(data))
				helper()
				pass
			elif op=='add' and len(cmd)>=2:
				#'<command> <ip1>;<ip2>'
				tmp = ('%s %s;%s'%('add', cmd[0], cmd[1]))
				skt_cmd.sendto(tmp, (remote_cmdip, config['udp_server_port']))
				print(tmp)
				pass
			elif op=='rm' or op=='kill' and len(cmd)>=1:
				#'<command> <task_id>'
				tmp = ('%s %s'%("rm", cmd[0]))
				skt_cmd.sendto(tmp, (remote_cmdip, config['udp_server_port']))
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
				print("\t\tNot Supported Format or Instruction...\n")
			pass
		except Exception as e:
			#raise e ##for debug
			print("...")
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