#! /usr/bin/python
'''
Proxy:
	[Publish subLayer] top-level of Cache Side, provide content service
@author: Mark Hong
'''
import os, time, json
from getpass import getuser
import platform as pt
import socket

global localuser, remote_cmdip
global config

win_pt = "windows" in pt.platform().lower()

def main():
	pass

if __name__ == '__main__':
	with open('../config.json') as cf:
		config = json.load(cf)

	localuser = getuser()
	remote_cmdip = 'localhost'

	try:
		main()
	except Exception as e:
		_cls()
	finally:
		exit()