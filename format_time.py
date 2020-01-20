import numpy as np

def add_abso_time(file, time_interval):
	interval = time_interval/1000
	abs_time = np.arange(0, time_interval, interval)
	print(abs_time)

with open('a.txt', 'a') as f:
	# for t in waveform:
	# 	f.write('\t'.join(str(s) for s in t) + '\n')
	add_abso_time('a.txt', 0.1)