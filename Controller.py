
import time
import os
from getpass import getuser
import platform as pt
import socket

localuser = getuser()
win_pt = "windows" in pt.platform().lower()

global udp_tx_setup, udp_rx_setup

def _cls():
	if win_pt:
		t = os.system("cls")
	else:
		t = os.system("clear")
	pass

def helper():
	print("************************Controller Helper************************")
	print("                 [LS] Current Client Process						")
	print("                 [ADD] Add a Client								")
	print("                 [SC] Execute Script File						")
	print("                 [CLS/CLEAR] Clear screen						")
	print("                 [EXIT] Exit										")
	print
	pass

def script_file(file):
	pass

def main():
	skt_cmd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	skt_recv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	skt_recv.settimeout(3.0)#3 seconds
	skt_recv.bind(udp_rx_setup)

	_cls()
	helper()
	while True:
		tipstr = localuser+"@Aggregator["+time.ctime()+"]> "
		cmd = raw_input(tipstr).lower().split()

		try:
			if cmd[0]=='ls':
				skt_cmd.sendto('ls', udp_tx_setup)
				data, ADDR = skt_recv.recvfrom(1024)
				_cls()
				print(data)
				print
				helper()
				pass
			elif cmd[0]=='add' and len(cmd)>=3:
				tmp = (" ").join(("add", cmd[1], cmd[2]))
				skt_cmd.sendto(tmp, udp_tx_setup)
				print(tmp)
				pass
			elif cmd[0]=='sc' and len(cmd)>=2:
				script_file(cmd[1])
				pass
			elif cmd[0]=='clear' or cmd[0]=='cls':
				_cls()
				helper()
				pass
			elif cmd[0]=='exit':
				print
				quit()
				pass
			else:
				print("No Kidding...")
			pass
		except Exception as e:
			#raise e ##for debug
			print("...")

		pass
	pass

if __name__ == '__main__':
	udp_tx_setup = ('localhost', 11112)
	udp_rx_setup = ('localhost', 11111)

	main()