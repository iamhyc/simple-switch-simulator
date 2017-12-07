#! /usr/bin/python
'''
Dispatcher: for command manipulation
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
global proc_map, proc_remap
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

def response(status, addr, optional):
	if status:
		frame = '+'
	else:
		frame = '-'
	frame += '\n' + optional
	skt_res.sendto(frame, (addr, config['converg_term_port']))
	pass

def process_print(cmd, addr):
	proc_list = ''.join( ('%s %s\n')%(k, v['char']) for (k,v) in proc_map.items())
	response(True, addr, proc_list)
	pass

def register_client(cmd, addr):
	global ClientCount

	wifi_ip, vlc_ip = cmd
	task_id = ClientCount #allocate task_id
	port = ALLOC_PORT_BASE + ClientCount #allocate port nubmer

	p2c_q = Queue() #Parent to Child Queue

	proc_remap[wifi_ip] = task_id #revese map over Wi-Fi link
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
	#default source with `unique` <static> data, and wait to trigger

	response(True, addr, str(port))
	#skt_res.sendto('kick', (addr, 11081)) #kick VLC receiver
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

	response(True, addr)
	pass

def set_source(cmd, addr):
	task_id = proc_remap[addr] if cmd[0]<-1 else cmd[0] #-1 for no id
	if proc_map.has_key(task_id):
		p2c_cmd = ''.join(['src'] + cmd[1:])
		proc_map[task_id]['queue'][0].put_nowait(p2c_cmd)
		pass
	else:
		response(False, addr)
		pass
	pass

def start_source(cmd, addr):
	task_id = proc_remap[addr] if cmd[0]<-1 else cmd[0] #-1 for no id
	if proc_map.has_key(task_id):
		p2c_cmd = 'src-now'
		proc_map[task_id]['queue'][0].put_nowait(p2c_cmd)
		pass
	else:
		response(False, addr)
		pass
	pass

def idle_work(cmd, addr):
	response(True, addr)
	pass

def disp_init():
	global skt_req, skt_res, fb_q, c2p_q, alg_node, ClientCount, proc_map, proc_remap

	# Map Init
	proc_map = {}
	proc_remap = {}
	# converg Socket Init
	skt_res = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	skt_req = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	skt_req.bind(('', config['converg_disp_port']))
	# plugin Alg. Node Init 
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
	# Converg Layer Dispatcher
	ops_map = {
		# General Operation
		"ls":process_print,
		"add":register_client,
		# Specific Operation
		"rm":remove_client,
		"src":set_source,
		"src-now":start_source
		"idle":idle_work
	}

	while True:
		#skt_req.settimeout(15) #for Windows debug
		data, addr = skt_req.recvfrom(1024)
		op, cmd = cmd_parse(data)
		try:
			ops_map[op](cmd, addr[0])
		except Exception as e:
			print('\nErrorCode: %s'%(e))
			print('\"%s\" from %s'%(data, addr))
			skt_res.sendto(op+' Failed', (addr, config['converg_term_port']))
			pass
		pass
	pass

if __name__ == '__main__':
	with open('../config.json') as cf:
		config = json.load(cf)

	print("Dispatcher is now online...")
	try:
		main()
	except Exception as e:
		#raise e #for debug
		pass
	finally:
		disp_exit()
