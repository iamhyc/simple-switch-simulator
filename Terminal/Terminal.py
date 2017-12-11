#! /usr/bin/python
'''
Terminal: for command manipulation
@author: Mark Hong
'''

from Aggregator import Aggregator

import json, math
import socket, string, binascii
from time import ctime, sleep, time
from threading import Thread
from multiprocessing import Process, Queue
from optparse import OptionParser

global config, options
global ops_map, src_type
global processor, p2c_q, c2p_q
global skt_req, skt_res

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

def request(frame, timeout=None):
	skt.settimeout(timeout)
	skt.send(frame)
	data = skt.recv()
	status = True if data=='+' else False
	skt.settimeout(None)
	return status, data[1:]
	pass

def exec_nowait(cmd):
	while not c2p_q.empty():
		c2p_q.get()
		pass
	p2c_q.put_nowait(cmd)
	pass

def exec_wait(cmd):
	while not c2p_q.empty():
		c2p_q.get()
		pass
	p2c_q.put(cmd)
	return c2p_q.get()

'''
Process Command Function
'''
def status_print_op(cmd, sock):
	response(True, sock)
	pass

def start_recv_op(cmd, sock):
	# false exists here
	fhash, fsize, flength = cmd
	cmd = ['set'] + cmd + [src_type]

	processor.stop()
	res = exec_wait(cmd)

	processor.start()
	response(True, sock)
	pass

def set_recv_type_op(cmd, sock):
	response(True, sock)
	pass

def idle_work_op(cmd, sock):
	response(True, sock)
	pass

'''
Process Internal Function
'''
def tcplink(sock, addr):
	while True:
		data = sock.recv(1024)
		op, cmd = cmd_parse(data)
		try:
			ops_map[op](cmd, sock, addr)
		except Exception as e:
			response(False, sock)
			pass
		pass
	pass

def term_exit():
	#terminate thread here
	exit()
	pass

def term_init():
	global skt_req, skt_res, processor, p2c_q, c2p_q, ops_map, src_type

	src_type = 'r' #'r' for relay, 'c' for cache
	ops_map = {
		# General Operation
		"ls":status_print_op,
		# Source Operation
		"src-now":start_recv_op,
		"src-type":set_recv_type_op,
		"idle":idle_work_op
	}

	# Server Socket Init
	skt_res = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	skt_res.bind(('', config['converg_term_port']))
	skt_res.listen(2)
	skt_req =socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	skt_req.connect((options.server, config['converg_disp_port']))

	# Register Procedure
	init_cmd = ('%s %s %s 0'%('add', options.wifi, options.vlc))
	status, fb_port = request(init_cmd) #block until feedback
	fb_port = int(fb_port)
	sock, addr = skt_res.accept() #accepet reverse TCP link
	
	# Init Aggregator Process
	p2c_q = multiprocessing.Queue() #Parent to Child Queue
	c2p_q = multiprocessing.Queue() #Child to Parent Queue
	queue = (p2c_q, c2p_q)
	processor = Aggregator(queue, fb_port)
	processor.daemon = True

	# Run NOW
	print('Connected with uplink port %d.'%(fb_port))
	processor.start()
	t = Thread(target=tcplink, args=(sock, addr))
    t.start()
	pass


def main():
	term_init()
	# Converg Layer Terminal

	while True:
		sock, addr = skt_res.accept()
		t = Thread(target=tcplink, args=(sock, addr))
    	t.start()
		pass
	pass

if __name__ == '__main__':
	with open('../config.json') as cf:
		config = json.load(cf)
		pass

	parser = OptionParser()
	parser.add_option("-s", "--server",
		dest="server", 
		default="localhost", 
		help="Designate the dispatcher server")
	parser.add_option("-w", "--wifi",
		dest="wifi", 
		default="localhost", 
		help="Designate the Wi-Fi interface")
	parser.add_option("-v", "--vlc",
		dest="vlc", 
		default="localhost", 
		help="Designate the VLC interface")
	(options, args) = parser.parse_args()

	try: #cope with Interrupt Signal
		main()
	except Exception as e:
		print(e) #for debug
		pass
	finally:
		term_exit()
