#! /usr/bin/python
'''
Aggregator: for data flow manipulation
@author: Mark Hong
'''
import json
import socket
import binascii, struct
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

def redistProc(redist_q):
	while True:
		if not redist_q.empty():
			data = redist_q.get_nowait()
			redist_skt.snedto(data, ('localhost', 95533))#redistribution
		pass
	pass

def wifiRecvProc(lock, port):
	global config

	wifi_skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	wifi_skt.bind(('', port))

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

def vlcRecvProc(lock, port):
	global config

	vlc_skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	vlc_skt.bind(('', port))

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
	lock = Lock()

	wifiProcHandle = Process(target=wifiRecvProc,args=(lock, config['udp_wifi_port']))
	vlcProcHandle = Process(target=vlcRecvProc,args=(lock, config['udp_vlc_port']))
	redistProcHandle = Process(target=redistProc,args=(redist_q,))
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
	res_skt.settimeout(5)

	req_skt.sendto(init_cmd, (options.server, config['udp_server_port']))
	fb_port, addr = res_skt.recvfrom(1024)#block until feedback
	try:
		#hope no error here...
		fb_port = int(fb_port)
		print('Connected with uplink port %d.'%(fb_port))
	except Exception as e:
		raise e
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
		default="localhost", 
		help="Designate the dispatcher server") 
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
		print(e) #for debug
		pass
	finally:
		agg_exit()