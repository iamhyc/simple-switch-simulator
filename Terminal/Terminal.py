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

def term_exit():
	#terminate thread here
	exit()
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

	frame_struct = struct.Struct('IHH') #Or, Struct('IB')
	init_cmd = ('%s %s %s'%('add', options.wifi, options.vlc))

	try: #cope with Interrupt Signal
		main()
	except Exception as e:
		print(e) #for debug
		pass
	finally:
		term_exit()
