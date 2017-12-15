#! /usr/bin/python
'''
Dispatcher: for command manipulation
@author: Mark Hong
'''
import json
from multiprocessing import Process, Queue
from threading import Thread
import socket, string, binascii

from Distributor import Distributor
from Algorithm import Algorithm

global config
global proc_map, proc_remap
global ClientCount
global alg_node, fb_q, a2p_q

ALLOC_PORT_BASE = 20000

'''
Process Helper Function
'''
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
	
	skt_res.send(frame)
	pass

def request(frame, sock, timeout=None):
	sock.settimeout(timeout)
	sock.send(frame)
	status = sock.recv()
	sock.settimeout(None)
	if status[0]=='+':
		return True
	else:
		return False
	pass

def exec_nowait(task_id, cmd):
	while not proc_map[task_id]['queue'][1].empty():
		proc_map[task_id]['queue'][1].get()
		pass
	proc_map[task_id]['queue'][0].put_nowait(cmd)
	pass

def exec_wait(task_id, cmd):
	while not proc_map[task_id]['queue'][1].empty():
		proc_map[task_id]['queue'][1].get()
		pass
	proc_map[task_id]['queue'][0].put(cmd)
	return proc_map[task_id]['queue'][1].get()
	pass

'''
Process Command Function
'''
def process_print_op(cmd, sock, addr):
	proc_list = ''.join( ('%s %s\n')%(k, v['char']) for (k,v) in proc_map.items())
	response(True, sock, proc_list)
	pass

def register_client_op(cmd, sock, addr):
	global ClientCount

	wifi_ip, vlc_ip, rc = cmd
	task_id = ClientCount #allocate task_id
	port = ALLOC_PORT_BASE + ClientCount #allocate port nubmer

	p2c_q = Queue() #Parent to Child Queue
	c2p_q = Queue() #Child to Parent Queue

	proc_remap[wifi_ip] = task_id #revese map over Wi-Fi link
	proc_map[task_id] = {}
	proc_map[task_id]['char'] = (wifi_ip, vlc_ip, port)
	proc_map[task_id]['res_sock'] = sock
	proc_map[task_id]['queue'] = (p2c_q, c2p_q, fb_q)
	proc_map[task_id]['_thread'] = Distributor(
									task_id,
									proc_map[task_id]['char'], 
									proc_map[task_id]['queue']
								)
	proc_map[task_id]['_thread'].daemon = True #set as daemon process
	proc_map[task_id]['_thread'].start()
	#default source with `unique` <static> data, and wait to trigger

	response(True, sock, str(port))
	if rc == '0':
		proc_map[task_id]['req_sock'] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		proc_map[task_id]['req_sock'].connect((addr, config['converg_term_port']))
		pass
	print('Client %d on (%s %s %d)...'%(ClientCount, wifi_ip, vlc_ip, port))

	ClientCount += 1
	pass

def dist_exit_op(cmd, sock, addr):
	task_id = proc_remap[addr] if cmd[0] == '-1' else cmd[0] #-1 for no id
	if not proc_map.has_key(task_id):
		raise Exception

	#proc_map[task_id].join() # wait for itself exit
	proc_map[task_id]['_thread'].terminate() #forcely exit the server
	del proc_map[task_id] # delete the item

	response(True, sock)
	pass

def set_source_op(cmd, sock, addr):
	task_id = proc_remap[addr] if cmd[0] == '-1' else cmd[0] #-1 for no id
	if proc_map.has_key(task_id):
		p2c_cmd = ''.join(['src'] + cmd[1:])

		res = exec_wait(task_id, p2c_cmd)
		if res[0]=='+': # need notify Terminal side
			request(res[1:], proc_map[task_id]['req_sock'])
			pass
		response(True, sock) # to Controller Side
		pass
	else:
		response(False, sock)
		pass
	pass

def start_source_op(cmd, sock, addr):
	task_id = proc_remap[addr] if cmd[0] == '-1' else cmd[0] #-1 for no id
	if proc_map.has_key(task_id):
		p2c_cmd = 'src-now'
		res = exec_wait(task_id, p2c_cmd)
		response(True, sock)
		pass
	else:
		response(False, sock)
		pass
	pass

def idle_work_op(cmd, sock, addr):
	response(True, sock)
	pass

'''
Process Internal Function
'''
def disp_init():
	global skt, fb_q, a2p_q, alg_node, ClientCount, proc_map, proc_remap, ops_map

	# Map Init
	proc_map = {}
	proc_remap = {}
	ops_map = {
		# General Operation
		"ls":process_print_op,
		"add":register_client_op,
		# Specific Operation
		"src":set_source_op,
		"src-now":start_source_op,
		"idle":idle_work_op,
		"finish":dist_exit_op,
	}
	# converg Socket Init
	skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	skt.bind(('', config['converg_disp_port']))
	skt.listen(10)
	# plugin Alg. Node Init 
	ClientCount = 0
	fb_q = Queue()
	a2p_q = Queue()
	alg_node = Algorithm((fb_q, a2p_q))
	alg_node.daemon = True #set as daemon process
	alg_node.start()
	pass

def disp_exit():
	alg_node.terminate()
	exit()
	pass

def tcplink(sock, addr):
	while True:
		data = sock.recv(1024)
		op, cmd = cmd_parse(data)
		try:
			ops_map[op](cmd, sock, addr)
		except Exception as e:
			print('\nErrorCode: %s'%(e))
			print('\"%s\" from %s'%(data, addr))
			response(False, sock)
			pass
		pass
	pass

def main():
	disp_init()
	# Converg Layer Dispatcher

	while True:
		sock, addr = skt.accept()
		t = Thread(target=tcplink, args=(sock, addr))
    	t.start()
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
