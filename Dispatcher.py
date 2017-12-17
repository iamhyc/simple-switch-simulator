#! /usr/bin/python
'''
Dispatcher: for command manipulation
@author: Mark Hong
'''
import threading, multiprocessing
import os, json, string, binascii, socket

from Dispatcher.Distributor import Distributor
from Dispatcher.Algorithm import Algorithm
from Utility.Utility import *

global config
global proc_map, proc_remap
global ClientCount
global alg_node, fb_q, a2p_q

ALLOC_PORT_BASE = 20000

'''
Process Helper Function
'''

# def exec_nowait(task_id, cmd):
# 	while not proc_map[task_id]['queue'][1].empty():
# 		proc_map[task_id]['queue'][1].get()
# 		pass
# 	proc_map[task_id]['queue'][0].put_nowait(cmd)
# 	pass

# def exec_wait(task_id, cmd):
# 	while not proc_map[task_id]['queue'][1].empty():
# 		proc_map[task_id]['queue'][1].get()
# 		pass
# 	proc_map[task_id]['queue'][0].put(cmd)
# 	return proc_map[task_id]['queue'][1].get()
# 	pass

'''
Process Command Function
'''
def process_print_op(cmd, sock, addr):
	proc_list = ''
	for (k,v) in proc_map.items():
		data = proc_map[k]['se'].exec_wait('src-get')
		status, src_char = data[0], data[1:]
		proc_list += '%s\t%s\n'%(k, v['char']) + '\t%s\n'%(src_char)
		pass
	response(True, sock, proc_list)
	pass

def dist_exit_op(cmd, sock, addr):
	task_id = proc_remap[addr] if cmd[0] == '-1' else int(cmd[0]) #-1 for no id

	if not proc_map.has_key(task_id):
		raise Exception('hehe')

	proc_map[task_id]['thread'].terminate() #forcely exit the server
	del proc_map[task_id] # delete the item

	response(True, sock)
	printh('Dispatcher', 'Client %d exit.'%(task_id), 'red')
	pass

def register_client_op(cmd, sock, addr):
	global ClientCount

	wifi_ip, vlc_ip, rc = cmd
	task_id = ClientCount #allocate task_id
	port = ALLOC_PORT_BASE + ClientCount #allocate port nubmer

	p2c_q = multiprocessing.Queue() #Parent to Child Queue
	c2p_q = multiprocessing.Queue() #Child to Parent Queue

	proc_remap[wifi_ip] = task_id #revese map over Wi-Fi link
	proc_map[task_id] = {}
	proc_map[task_id]['char'] = (wifi_ip, vlc_ip, port)
	proc_map[task_id]['res_sock'] = sock
	proc_map[task_id]['se'] = SyncExecutor(p2c_q, c2p_q)
	proc_map[task_id]['queue'] = (p2c_q, c2p_q, fb_q)
	proc_map[task_id]['thread'] = Distributor(
									task_id,
									proc_map[task_id]['char'], 
									proc_map[task_id]['queue']
								)
	proc_map[task_id]['thread'].daemon = True #set as daemon process
	proc_map[task_id]['thread'].start()
	#default source with `unique` <static> data, and wait to trigger

	response(True, sock, str(port))
	if rc == '0':
		proc_map[task_id]['req_sock'] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		proc_map[task_id]['req_sock'].connect((addr, config['converg_term_port']))
		pass
	printh('Dispatcher', 'Client %d on (%s %s %d)...'%(ClientCount, wifi_ip, vlc_ip, port))

	ClientCount += 1
	pass

def set_source_op(cmd, sock, addr):
	task_id = proc_remap[addr] if cmd[0] == '-1' else int(cmd[0]) #-1 for no id
	if proc_map.has_key(task_id):
		p2c_cmd = ' '.join(['src-set'] + cmd[1:])
		res = proc_map[task_id]['se'].exec_wait(p2c_cmd)
		if res[0]=='+': # need notify Terminal side
			frame = res[1:]
			request(frame, proc_map[task_id]['req_sock'])
			print('notified %d'%(task_id))
			pass
		response(True, sock) # to Controller Side
		pass
	else:
		response(False, sock)
		pass
	pass

def start_source_op(cmd, sock, addr):
	task_id = proc_remap[addr] if cmd[0] == '-1' else int(cmd[0]) #-1 for no id
	if proc_map.has_key(task_id):
		p2c_cmd = 'src-now'
		res = proc_map[task_id]['se'].exec_wait(p2c_cmd)
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
	global skt, fb_q, a2p_q, alg_node, ClientCount, proc_map, proc_remap, ops_map, fbHandle

	# Map Init
	proc_map = {}
	proc_remap = {}
	ops_map = {
		# General Operation
		"ls":process_print_op,
		"add":register_client_op,
		# Specific Operation
		"src-set":set_source_op,
		"src-now":start_source_op,
		"idle":idle_work_op,
		"exit":dist_exit_op,
	}
	# converg Socket Init
	skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	skt.bind(('', config['converg_disp_port']))
	skt.listen(10)
	# plugin Alg. Node Init
	ClientCount = 0
	fb_q = multiprocessing.Queue()
	a2p_q = multiprocessing.Queue()
	alg_node = Algorithm((fb_q, a2p_q))
	alg_node.daemon = True #set as daemon process
	exec_watch(alg_node, hook=disp_exit, fatal=True)
	# alg_node.start()
	# plugin Alg. Node feedback
	fbHandle = threading.Thread(target=fbThread, args=(fb_q, ))
	fbHandle.setDaemon(True)
	fbHandle.start()
	pass

def disp_exit():
	global alg_node
	if alg_node.is_alive():
		alg_node.terminate()
		pass
	os._exit(0)
	pass

def fbThread(fb_q):
	while True:
		if not fb_q.empty():
			frame = fb_q.get_nowait()
			op, data = cmd_parse(frame)
			task_id, ratio = data[0], data[1:]
			exec_nowait()
			pass
		pass
	pass

def tcplink(sock, addr):
	while True:
		try:
			data = sock.recv(1024)
			op, cmd = cmd_parse(data)
			ops_map[op](cmd, sock, addr)
		except (socket.error, Exception) as e:
			if e.message=='' : return
			print(e)
			response(False, sock)
			pass
		pass
	pass

def main():
	disp_init()
	# Converg Layer Dispatcher

	while True:
		sock, addr = skt.accept()
		t = threading.Thread(target=tcplink, args=(sock, addr[0]))
		t.setDaemon(True)
		t.start()
		pass
	pass

if __name__ == '__main__':
	with open('config.json') as cf:
		config = json.load(cf)

	printh('Dispatcher', "Dispatcher is now online...", 'green')
	try:
		main()
	except Exception as e:
		#raise e #for debug
		pass
	finally:
		disp_exit()
