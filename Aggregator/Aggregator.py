#! /usr/bin/python
'''
Aggregator: for data flow manipulation
@author: Mark Hong
'''
import json
import socket
import binascii, struct
from heapq import *
from multiprocessing import Process, Queue, Lock
from optparse import OptionParser

global config, options
global local_wifi_ip, local_vlc_proxy_ip, local_vlc_real_ip
global req_skt, res_skt, fb_skt, fb_port
global wifi_skt, vlc_skt, redist_skt
global wifiProcHandle, vlcProcHandle, redistProcHandle
global frame_struct
global ringBuffer, sWindow, timeout
global redist_q

def redistProc(queue):
	while True:
		if not redist_q.empty():
			data = redist_q.get_nowait()
			redist_skt.snedto(data, ('localhost', 95533))#redistribution
		pass
	pass

def wifiRecvProc(lock):
	wifi_skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	wifi_skt.bind(('', config['udp_wifi_port']))

	while True:
		raw, addr = wifi_skt.recvfrom(1024)
		Seq, Size, Offset, Data = frame_struct.unpack(raw)

		ptr = Seq % sWindow
		if ringBuffer[ptr][0] != Seq:
			with lock:
				ringBuffer[ptr] = [Seq, Size - len(Data), [chr(0)]*Size]
				ringBuffer[ptr][2][Offset:Offset+Size] = Data
			pass
		else:
			with lock:
				ringBuffer[ptr][1] -= len(Data)
				ringBuffer[ptr][2][Offset:Offset+Size] = Data
			pass
		#statistical collection here
    	#print(os.getpid())
    		pass
		pass
	pass

def vlcRecvProc(lock):
	vlc_skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	vlc_skt.bind(('', config['udp_vlc_port']))

	while True:
		raw, addr = vlc_skt.recvfrom(1024)
		Seq, Size, Offset, Data = frame_struct.unpack(raw)
		
		ptr = Seq % sWindow
		if ringBuffer[ptr][0] != Seq:
			with lock:
				ringBuffer[ptr] = [Seq, Size - len(Data), [chr(0)]*Size]
				ringBuffer[ptr][2][Offset:Offset+Size] = Data
			pass
		else:
			with lock:
				ringBuffer[ptr][1] -= len(Data)
				ringBuffer[ptr][2][Offset:Offset+Size] = Data
			pass
		#statistical collection here
    	#print(os.getpid())
    		pass
		pass
	pass

def recvStart():
	lock = multiprocessing.Lock()

	wifiProcHandle = multiprocessing.Process(target=wifiRecvProc,args=(lock,))
	vlcProcHandle = multiprocessing.Process(target=vlcRecvProc,args=(lock,))
	redistProcHandle = multiprocessing.Process(target=redistProc,args=(redist_q,))
	wifiProcHandle.daemon = True
	vlcProcHandle.daemon = True
	redistProcHandle.daemon = True
	redistProcHandle.start()
	wifiProcHandle.start()
	vlcProcHandle.start()
	pass

def agg_init():
	global ringBuffer, redist_q, redist_skt, req_skt, res_skt, fb_port, fb_skt

	ringBuffer = [[-1, -1, []]] * sWindow
	redist_q = Queue()

	redist_skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	req_skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	#fb_skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	res_skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	res_skt.bind(('', config['udp_client_port']))

	req_skt.send(init_cmd, (options.server, config['udp_server_port']))
	fb_port, addr = res_skt.recvfrom(1024)#block until feedback
	#assume no error here...hehe...
	pass

def agg_exit():
	#terminate process here
	exit()
	pass

def main():
	agg_init()
	recvStart()

	ptr = 0
	while True:
		if ringBuffer[ptr][0] > ptr:
			counter = 0
			while ringBuffer[ptr][1]!= 0 and counter < timeout:
				counter += counter
			if counter >= timeout:
				redist_q.put_nowait(''.join(ringBuffer[ptr][3]))
			pass
		pass
	pass

if __name__ == '__main__':
	with open('../config.json') as cf:
		config = json.load(cf)
		pass

	parser = OptionParser()
	parser.add_option("-s", "--server",
		dest="server", 
		default="192.168.1.100", 
		help="Designate the distributor server") 
	(options, args) = parser.parse_args()

	frame_struct = struct.Struct('Ihhs') #Or, Struct('IBs')
	local_wifi_ip = "localhost"
	local_vlc_proxy_ip = "localhost"
	local_vlc_real_ip = "localhost"#bind to the relay ip
	init_cmd = ('%s %s;%s'%('add', local_wifi_ip, local_vlc_proxy_ip))
	sWindow = 500#config.sWindow
	timeout = 100#config.timeout

	try: #cope with Interrupt Signal
		main()
	except Exception as e:
		raise e #for debug
		pass
	finally:
		agg_exit()