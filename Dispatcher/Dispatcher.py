#! /usr/bin/python
'''
Dispatcher: for instruction manipulation
@author: Mark Hong
'''

from time import sleep, ctime
from multiprocessing import Process, Queue
import socket, string, binascii

from Distributor import Distributor
from Algorithm import Algorithm

global udp_wifi_port, udp_vlc_port
global udp_tx_port, udp_rx_port
global skt_res, skt_req
global proc_map, ops_map
global ClientCount
global alg_node, fb_q, c2p_q

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

def process_print(cmd, addr):
	proc_list = '\n'.join( (item+' '+item.char) for item in proc_map)
	skt.sendto(proc_list, (addr, udp_tx_port))
	pass

def add_client(cmd, addr):
	wifi_ip, vlc_ip = cmd
	task_id = ClientCount #allocate task_id
	port = ALLOC_PORT_BASE + ClientCount #allocate port nubmer

	p2c_q = Queue() #Parent to Child Queue

	proc_map[task_id] = {}
	proc_map[task_id].char = (wifi_ip, vlc_ip, port)
	proc_map[task_id].queue = (p2c_q, fb_q)
	proc_map[task_id]._thread = Distributor(
									proc_map[task_id].char, 
									proc_map[task_id].queue
								)
	proc_map[task_id]._thread.daemon = True #set as daemon process
	proc_map[task_id]._thread.start()

	skt.sendto(str(port), (addr, udp_tx_port))
	ClientCount += 1
	pass

def remove_client(cmd, addr):
	task_id = cmd[0]
	if not proc_map.has_key(task_id):
		raise Exception

	#proc_map[task_id].join() # wait for itself exit
	proc_map[task_id]._thread.terminate() #forcely exit the server
	del proc_map[task_id] # delete the item

	skt.sendto('1', (addr, udp_tx_port))
	pass

def _init():
	skt_res = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	skt_req = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	skt_req.bind(('', udp_rx_port))

	fb_q = Queue()
	c2p_q = Queue()
	alg_node = Algorithm((fb_q, c2p_q))
	alg_node.daemon = True #set as daemon process
	alg_node.start()
	pass

def main():
	_init()
	while True:
		data, addr = skt_req.recvfrom(1024)
		op, cmd = cmd_parse(data)
		try:
			ops_map[op](cmd, addr)
		except Exception as e:
			print('\nErrorCode: %s'%(e))
			print('\"%s\" from %s'%(data, addr))
			#skt.sendto(op+' Failed', (addr, udp_tx_port))
		pass
	pass
	pass

if __name__ == '__main__':
	ClientCount = 0
	udp_req_port = 11111#slef To port
	udp_res_port = 11110#From self port
	proc_map = {}
	ops_map = {
		"ls":process_print,
		"add":add_client,
		"rm":remove_client
	}

	print("Dispatcher is now online...")
	main()