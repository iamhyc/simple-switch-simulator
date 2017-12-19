#! /usr/bin/python
'''
Math: useful math function utilities
@author: Mark Hong
@level: release
'''
import random, math, string
from crcmod import mkCrcFun

def randomString(len, dtype='hex'):
	data = ''
	if dtype=='hex':
		data = ''.join(random.choice(string.hexdigits.upper()) for x in xrange(len))
	elif dtype=='dec':
		data = ''.join(random.choice(string.digits) for x in xrange(len))
	elif dtype=='char':
		data = ''.join(random.choice(string.uppercase) for x in xrange(len))
	else:
		pass
	return data

def crcFactory(dtype='crc-16'):
	if dtype=='crc-32':
		return mkCrcFun(0x104c11db7, initCrc=0, xorOut=0xFFFFFFFF)
	else:
		return mkCrcFun(0x11021, rev=False, initCrc=0x0000, xorOut=0x0000)
	pass