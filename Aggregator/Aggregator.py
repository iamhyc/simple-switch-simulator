#! /usr/bin/python
'''
Aggregator: for data flow manipulation
@author: Mark Hong
'''
import json
import thread
import socket
import binascii, struct

global config

def main():
	try:
		pass
	except Exception as e:
		raise e
	finally:
		pass

if __name__ == '__main__':
	with open('../config.json') as cf:
		config = json.load(cf)
		pass
	main()