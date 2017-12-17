#! /usr/bin/python
'''
Terminal: for command manipulation
@author: Mark Hong
'''

from Terminal.Aggregator import Aggregator
from Utility.Utility import *

import os, json
import socket, string, binascii
import threading, multiprocessing
from optparse import OptionParser

global config, options
global ops_map, src_type
global processor, skt_req, skt_res

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
	print(cmd)
	res = se.exec_wait(cmd)

	response(True, sock)
	pass

def set_recv_type_op(cmd, sock):
	cmd = ['type'] + [cmd[0]]
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
		try:
			data = sock.recv(1024)
			op, cmd = cmd_parse(data)
			ops_map[op](cmd, sock, addr)
		except Exception as e:
			try:
				response(False, sock)
			except Exception as e:
				printh('Terminal', 'Link Broken!', 'red')
				raise e
			finally:
				exit()
			raise e
			pass
		pass
	pass

def term_exit():
	try:
		#terminate threads here
		processor.terminate()
		request('exit -1', skt_req, 3)
	except Exception as e:
		pass
	finally:
		os._exit(0)
	pass

def term_init():
	global se, skt_req, skt_res, processor, p2c_q, c2p_q, ops_map, src_type

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
	status, fb_port = request(init_cmd, skt_req, 3) #block until feedback
	fb_port = int(fb_port)
	sock, addr = skt_res.accept() #accepet reverse TCP link
	
	# Init Aggregator Process
	p2c_q = multiprocessing.Queue() #Parent to Child Queue
	c2p_q = multiprocessing.Queue() #Child to Parent Queue
	se = AlignExecutor(p2c_q, c2p_q)
	processor = Aggregator((p2c_q, c2p_q), (options.server, fb_port))
	processor.daemon = True

	# Run NOW
	printh('Terminal', 'Connected with uplink port %d.'%(fb_port), 'green')
	exec_watch(processor, hook=term_exit, fatal=True)
	t = threading.Thread(target=tcplink, args=(sock, addr[0]))
	t.setDaemon(True)
	exec_watch(t, hook=term_exit, fatal=True)
	#t.start()
	pass


def main():
	term_init()
	# Converg Layer Terminal

	while True:
		sock, addr = skt_res.accept()
		t = threading.Thread(target=tcplink, args=(sock, addr[0]))
		t.start()
		pass
	pass

if __name__ == '__main__':
	with open('config.json') as cf:
		config = json.load(cf)
		pass

	parser = OptionParser()
	parser.add_option("-s", "--server",
		dest="server", 
		default="127.0.0.1", 
		help="Designate the dispatcher server")
	parser.add_option("-w", "--wifi",
		dest="wifi", 
		default="127.0.0.1", 
		help="Designate the Wi-Fi interface")
	parser.add_option("-v", "--vlc",
		dest="vlc", 
		default="127.0.0.1", 
		help="Designate the VLC interface")
	(options, args) = parser.parse_args()

	try: #cope with Interrupt Signal
		main()
	except Exception as e:
		print(e) #for debug
		pass
	finally:
		term_exit()
