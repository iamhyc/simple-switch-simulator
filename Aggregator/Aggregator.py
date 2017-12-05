#! /usr/bin/python
'''
Aggregator: for data flow manipulation
@author: Mark Hong
'''
import json
import socket
import binascii, struct
import Queue
from threading import Thread
from time import ctime, sleep, time
from optparse import OptionParser

global ringBuffer
global config, options
global frame_struct, ringBuffer
global fb_skt, fb_port, redist_skt, redist_q
global wifiRecvHandle, vlcRecvHandle, redistHandle

def unpack_helper(fmt, data):
    size = struct.calcsize(fmt)
    return struct.unpack(fmt, data[:size]), data[size:]

def redistThread(redist_q):
	redist_skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

	while True:
		if not redist_q.empty():
			data = redist_q.get_nowait()
			#print('Redistributed Data: %s'%(data))
			redist_skt.sendto(data, ('localhost', 12306))#redistribution
		sleep(0) #surrender turn
		pass
	pass

def wifiRecvThread(config):
	global ringBuffer
	wifi_skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	wifi_skt.bind(('', config['udp_wifi_port']))

	while True:
		raw, addr = wifi_skt.recvfrom(4096)
		(Seq, Size, Offset), Data = unpack_helper(config['frame_struct'], raw)
		#print('From Wi-Fi link:(%d,%d,%d,%s)'%(Seq, Size, Offset, Data)) #for debug

		ptr = Seq % config['sWindow']
		if ringBuffer[ptr][0] != Seq:
			ringBuffer[ptr] = [Seq, Size - len(Data), [chr(0)]*Size]
			ringBuffer[ptr][2][Offset:Offset+len(Data)] = Data
			pass
		else:
			ringBuffer[ptr][2][Offset:Offset+len(Data)] = Data
			ringBuffer[ptr][1] -= len(Data)
			pass
		#statistical collection here
    	#print(os.getpid())
    	sleep(0) #surrender turn
	pass

def vlcRecvThread(config):
	global ringBuffer
	vlc_skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	vlc_skt.bind(('', config['udp_vlc_port']))

	while True:
		raw, addr = vlc_skt.recvfrom(4096)
		(Seq, Size, Offset), Data = unpack_helper(config['frame_struct'], raw)
		#print('From VLC link:(%d,%d,%d,%s)'%(Seq, Size, Offset, Data)) #for debug
		
		ptr = Seq % config['sWindow']
		if ringBuffer[ptr][0] != Seq:
			ringBuffer[ptr] = [Seq, Size - len(Data), [chr(0)]*Size]
			ringBuffer[ptr][2][Offset:Offset+len(Data)] = Data
			pass
		else:
			ringBuffer[ptr][2][Offset:Offset+len(Data)] = Data
			ringBuffer[ptr][1] -= len(Data)
			pass
		#statistical collection here
    	#print(os.getpid())
    	sleep(0) #surrender turn
	pass

def recvStart():
	global ringBuffer, config
	
	wifiRecvHandle = Thread(target=wifiRecvThread, args=(config, ))
	vlcRecvHandle = Thread(target=vlcRecvThread, args=(config, ))
	redistHandle = Thread(target=redistThread, args=(redist_q, ))
	wifiRecvHandle.setDaemon(True)
	vlcRecvHandle.setDaemon(True)
	redistHandle.setDaemon(True)

	redistHandle.start()
	wifiRecvHandle.start()
	vlcRecvHandle.start()
	pass

def agg_init():
	global config, ringBuffer, redist_q, fb_port, fb_skt

	# ringBuffer = [Seq, Size, sub1_Size, sub2_Size, Data]
	ringBuffer = [0] * config['sWindow']
	for x in xrange(config['sWindow']):
		ringBuffer[x] = [-1, -1, 0, 0, [chr(0)] * 4096]
		pass
	redist_q = Queue.Queue()
	
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
	
	while ringBuffer[0][0] != 0:
		sleep(0.1) # wait
		pass

	cnt, ptr = 0, 0
	timeout = time() # packet time counter
	while True:
		ptr = (cnt % config['sWindow'])
		if time()-timeout < config['Atimeout']:
			if ringBuffer[ptr][0] == cnt: #assume: writing not over reading
				timeout = time() # subpacket time counter

				sub_verified = False
				while time()-timeout < config['Btimeout']:
					if ringBuffer[ptr][1] == 0:
						redist_q.put_nowait(''.join(ringBuffer[ptr][2]))
						sub_verified = True
						break
					pass

				timeout = time() # reset subpacket time counter
				cnt += 1
				ptr = (cnt % config['sWindow'])
				if sub_verified:
					print(cnt)
				else:
					print("subPacket loss in %d."%(cnt))
				pass
			pass
		else: # packet loss
			timeout = time() # reset packet time counter
			cnt += 1
			ptr = (cnt % config['sWindow'])
			print("Packet %d loss."%(cnt))
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
	parser.add_option("-w", "--wifi",
		dest="wifi", 
		default="localhost", 
		help="Designate the Wi-Fi interface")
	parser.add_option("-v", "--vlc",
		dest="vlc", 
		default="localhost", 
		help="Designate the VLC interface")
	(options, args) = parser.parse_args()

	frame_struct = struct.Struct('Ihhs') #Or, Struct('IBs')
	init_cmd = ('%s %s %s'%('add', options.wifi, options.vlc))

	try: #cope with Interrupt Signal
		main()
	except Exception as e:
		print(e) #for debug
		pass
	finally:
		agg_exit()
