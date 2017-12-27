#! /usr/bin/python
'''
Math: useful data function utilities
@author: Mark Hong
@level: release
'''
import time, struct

frame_type = {
	'ACK':0x00,
	'NAK':0x01,
	'RATE':0x02,
	'CSI':0x03,
	'BIAS':0x04
}

def unpack_helper(fmt, data):
	unpack_data = [0] * len(fmt)
	size = struct.calcsize(fmt)
	try:
		unpack_data, data = struct.unpack(fmt, data[:size]), data[size:]
	except Exception as e:
		pass
	finally:
		return unpack_data, data
	pass

#options pad#
def build_options(ratio, count):
	#options: 4b for ratio, 4b for count
	return (0xFF & 
			(abs(ratio)&0x0F)<<4 & 
			(abs(count)&0x0F)
			)

def parse_options(seq_s, options):
	mark = seq_s&(1<<31)
	seq = seq_s&(0x7FFFFFFF)
	ratio = (options&0xF0)>>4
	count = (options&0x0F)
	return (seq, mark, ratio, count)

#control frame#
def build_control(fid, ftype, fdata):
	t = time.time()
	ftype = frame_type[ftype]
	pad = 0x0F & ((fid&0x01)<<3 & (ftype&0x07))
	return struct.pack('IBi', t, pad, fdata)

def parse_control(frame):
	seq, pad, fdata = struct.unpack('IBi', frame)
	fid, ftype = (pad>>3)&0x01, pad&0x07
	ftype = frame_type.keys()[frame_type.values().index(ftype)]
	return seq, fid, ftype, fdata
