#! /usr/bin/python
'''
Dispatcher: for instruction manipulation
@author: Mark Hong
'''
import json
from time import sleep, ctime
from multiprocessing import Process, Queue
import socket, string, binascii

from Distributor import Distributor
from Algorithm import Algorithm

global config
global skt_res, skt_req
global proc_map, ops_map
global ClientCount
global alg_node, fb_q, c2p_q

ALLOC_PORT_BASE = 20000

def cmd_parse(str):
	cmd = ''
	op_tuple = str.lower().split(' ')
	op = op_tuple[0]
	if len(op_tuple) > 1:
		cmd = op_tuple[1:]
		pass
	return op, cmd
	pass

def process_print(cmd, addr):
	proc_list = ''.join( ('%s %s\n')%(k, v['char']) for (k,v) in proc_map.items())
	skt_res.sendto(proc_list, (addr, config['udp_client_port']))
	pass

def add_client(cmd, addr):
	global ClientCount

	wifi_ip, vlc_ip = cmd
	task_id = ClientCount #allocate task_id
	port = ALLOC_PORT_BASE + ClientCount #allocate port nubmer

	p2c_q = Queue() #Parent to Child Queue

	proc_map[task_id] = {}
	proc_map[task_id]['char'] = (wifi_ip, vlc_ip, port)
	proc_map[task_id]['queue'] = (p2c_q, fb_q)
	proc_map[task_id]['_thread'] = Distributor(
									task_id,
									proc_map[task_id]['char'], 
									proc_map[task_id]['queue']
								)
	proc_map[task_id]['_thread'].daemon = True #set as daemon process
	proc_map[task_id]['_thread'].start()

	skt_res.sendto(str(port), (addr, config['udp_client_port']))
	skt_res.sendto('trick', (addr, 11081))
	print('Client %d on (%s %s %d)...'%(ClientCount, wifi_ip, vlc_ip, port))

	ClientCount += 1
	pass

def remove_client(cmd, addr):
	task_id = cmd[0]
	if not proc_map.has_key(task_id):
		raise Exception

	#proc_map[task_id].join() # wait for itself exit
	proc_map[task_id]['_thread'].terminate() #forcely exit the server
	del proc_map[task_id] # delete the item

	skt_res.sendto('1', (addr, config['udp_client_port']))
	pass

def disp_init():
	global skt_req, skt_res, fb_q, c2p_q, alg_node, ClientCount

	skt_res = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	skt_req = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	skt_req.bind(('', config['udp_server_port']))

	ClientCount = 0
	fb_q = Queue()
	c2p_q = Queue()
	alg_node = Algorithm((fb_q, c2p_q))
	alg_node.daemon = True #set as daemon process
	alg_node.start()
	pass

def disp_exit():
	alg_node.terminate()
	exit()
	pass

def main():
	disp_init()
	while True:
		#skt_req.settimeout(15) #for debug
		data, addr = skt_req.recvfrom(1024)
		op, cmd = cmd_parse(data)
		try:
			ops_map[op](cmd, addr[0])
		except Exception as e:
			print('\nErrorCode: %s'%(e))
			print('\"%s\" from %s'%(data, addr))
			#skt_res.sendto(op+' Failed', (addr, config['udp_client_port']))
			pass
		pass
	pass

if __name__ == '__main__':
	with open('../config.json') as cf:
		config = json.load(cf)

	proc_map = {}
	ops_map = {
		"ls":process_print,
		"add":add_client,
		"rm":remove_client
	}

	print("Dispatcher is now online...")
	try:
		main()
	except Exception as e:
		raise e #for debug
		pass
	finally:
		disp_exit()
