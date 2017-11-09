#! /usr/bin/python
'''
Aggregator: for data flow manipulation
@author: Mark Hong
'''
import json
import thread
import socket
import binascii, struct
from optparse import OptionParser

global config, options
global cmd_skt, wifi_skt, vlc_skt

def _init():
	wifi_skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	pass

def main():
	pass

if __name__ == '__main__':
	with open('../config.json') as cf:
		config = json.load(cf)
		pass

	parser.add_option("-s", "--server",
		dest="server", 
		default="192.168.1.100", 
		help="Designate the distributor server") 
	(options, args) = parser.parse_args()

	try:
		main()
	except Exception as e:
		#raise e
	finally:
		exit()