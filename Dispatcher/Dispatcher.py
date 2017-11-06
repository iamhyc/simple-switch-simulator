#! /usr/bin/python
from time import sleep, ctime
import multiprocessing
import socket, string, binascii

global udp_wifi_port, udp_vlc_port
global udp_tx_setup, udp_rx_setup
global proc_map, ops_map

remote_cmdip = 'localhost'

class Distributor(multiprocessing.Process):
	"""Non-Blocking running Distributor Process
		@desc 
		@var source:
			data source for this distributor, 
			default as looped
		@var queue:
			multiprocess control side
	"""
	def __init__(self, source):
		multiprocessing.Process.__init__(self)
		pass
		
	def run(self):
		while True:
			self.state_map[self.state]()
		pass


def main():
	skt_res = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	skt_req = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	skt_req.bind(udp_rx_setup)

	while True:
		data, addr = skt_cmd.recvfrom(1024)
		op_tuple = data.split(' ', 1)
		try:
			ops_map[op](skt_lock)
		except Exception as e:
			#print('\"%s\" from %s'%(data, addr))
			skt.sendto('-1'+' '+task_id, udp_tx_setup)
		pass
	pass
	pass

if __name__ == '__main__':
	udp_wifi_port = 11112
	udp_vlc_port = 11113
	udp_tx_setup = ('localhost', 11111)
	udp_rx_setup = (remote_cmdip, 11112)
	proc_map = {}

	print("Dispatcher is now online...")
	main()