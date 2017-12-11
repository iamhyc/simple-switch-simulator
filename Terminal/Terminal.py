#! /usr/bin/python
'''
Terminal: for command manipulation
@author: Mark Hong
'''

from Aggregator import Aggregator

import json
import socket, string, binascii
from time import ctime, sleep, time
from threading import Thread
from multiprocessing import Process, Queue
from optparse import OptionParser

global config, options
global processor

def cmd_parse(str):
	cmd = ''
	op_tuple = str.lower().split(' ')
	op = op_tuple[0]
	if len(op_tuple) > 1:
		cmd = op_tuple[1:]
		pass
	return op, cmd
	pass

def request(frame, timeout=None):
	skt.settimeout(timeout)
	skt.send(frame)
	data = skt.recv()
	status = True if data=='+' else False
	skt.settimeout(None)
	return status, data[1:]
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

def term_exit():
	#terminate thread here
	exit()
	pass

def term_init():
	global skt, processor

	# Server Socket Init
	skt_res = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	skt_res.bind(('', config['converg_term_port']))
	skt_res.listen(2)

	skt_req =socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	res_skt.connect((options.server, config['converg_disp_port']))
	
	init_cmd = ('%s %s %s 0'%('add', options.wifi, options.vlc))
	status, fb_port = request(init_cmd)#block until feedback
	fb_port = int(fb_port)

	sock, addr = skt.accept() #accepet reverse TCP link
	t = Thread(target=tcplink, args=(sock, addr))
    t.start()
	
	p2c_q = multiprocessing.Queue() #Parent to Child Queue
	c2p_q = multiprocessing.Queue() #Child to Parent Queue
	queue = (p2c_q, c2p_q)
	processor = Aggregator(queue, fb_port)
	print('Connected with uplink port %d.'%(fb_port))
	pass


def main():
	term_init()

	while True:
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
