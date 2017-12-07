#! /usr/bin/python
'''
Aggregator: for data flow manipulation
@author: Mark Hong
'''
import json, random, string, struct
import socket
from optparse import OptionParser

global config, options

def main():
	skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	max_size = 4096 - struct.Struct(config['struct']).size
	options.len = max_size if options.len>max_size else options.len

	while True:
		raw_input('Tap to continue...')
		data = ''.join(random.choice(string.hexdigits.upper()) for x in range(options.len))
		for x in xrange(options.number):
			skt.sendto(data, (options.server, config['udp_src_port']))
		print(data)
		pass
	pass

if __name__ == '__main__':
	with open('./config.json') as cf:
		config = json.load(cf)
		pass

	parser = OptionParser()
	parser.add_option("-s", "--server",
		dest="server",
		type="string",
		default="localhost", 
		help="Designate the distributor server")
	parser.add_option("-l", "--length",
		dest="len",
		type="int",
		default=256, 
		help="Designate the distributor server")
	parser.add_option("-n", "--number",
		dest="number",
		type="int",
		default=1, 
		help="Designate the distributor server")
	(options, args) = parser.parse_args()

	try:
		main()
	except Exception as e:
		pass
	finally:
		exit()