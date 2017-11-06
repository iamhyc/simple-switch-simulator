#! /usr/bin/python
from time import sleep, ctime
from multiprocessing import Process, Queue
import socket, string, binascii

from Distributor import Distributor
from Algorithm import Algorithm

global udp_wifi_port, udp_vlc_port
global udp_tx_setup, udp_rx_setup
global skt_res
global ClientCount
global proc_map, ops_map

remote_cmdip = 'localhost'
ALLOC_PORT_BASE = 20000

def cmd_parse(str):
	cmd = ''
	op_tuple = str.lower().split(' ', 1)
	op = op_tuple[0]
	if len(op_tuple) > 1:
		cmd = op_tuple[1].split(';')
		pass
	return op, cmd
	pass

def print_process(cmd):
	proc_list = '\n'.join( (item+' '+item.char) for item in proc_map)
	skt.sendto(proc_list, udp_tx_setup)
	pass

def add_client(cmd):
	wifi_ip, vlc_ip = cmd
	task_id = ClientCount;
	port = ALLOC_PORT_BASE + ClientCount

	p2c_q = Queue() #Parent to Child Queue
	c2p_q = Queue() #Child to Parent Queue

	proc_map[task_id] = {}
	proc_map[task_id].char = (wifi_ip, vlc_ip, port)
	proc_map[task_id].queue = (p2c_q, c2p_q)
	proc_map[task_id]._thread = Distributor(
									proc_map[task_id].char, 
									proc_map[task_id].queue
								)
	proc_map[task_id]._thread.daemon = True#set as daemon process
	proc_map[task_id]._thread.start()

	ClientCount += 1
	pass

def remove_client(cmd):
	task_id = cmd[0]
	if not proc_map.has_key(task_id):
		raise Exception

	#proc_map[task_id].join() # wait for itself exit
	proc_map[task_id]._thread.terminate() #forcely exit the server
	del proc_map[task_id] # delete the item
	pass

def main():
	skt_res = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	skt_req = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	skt_req.bind(udp_rx_setup)

	while True:
		data, addr = skt_cmd.recvfrom(1024)
		op, cmd = cmd_parse(data)
		try:
			ops_map[op](cmd)
		except Exception as e:
			print('\nErrorCode: %s'%(e))
			print('\"%s\" from %s'%(data, addr))
			#skt.sendto(op+' Failed', udp_tx_setup)
		pass
	pass
	pass

if __name__ == '__main__':
	ClientCount = 0
	udp_wifi_port = 11112
	udp_vlc_port = 11113
	udp_tx_setup = ('localhost', 11111)
	udp_rx_setup = (remote_cmdip, 11112)
	proc_map = {}
	ops_map = {
		"ls":print_process,
		"add":add_client,
		"rm":remove_client
	}

	print("Dispatcher is now online...")
	main()