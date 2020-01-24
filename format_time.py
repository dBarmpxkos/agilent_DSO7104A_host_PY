import numpy as np

waveform = np.arange(-0.5, 0.5, 0.001)
print(type(waveform))

with open('test.txt', 'a') as f:
	for t in waveform:
		print(t)


def measure_and_log(dt_for_filename, time_to_measure, time_interval):
	global scope

	counter = 0 # used for naming 
	abso_time = add_abso_time(time_interval/10)

	for ch in scope.channels[0:3]:
		if ch.enabled: 
			with open(dt_for_filename[counter], 'a') as f:
				abso_count = 0 # used for iterating through absolute time
				scope.measurement.initiate()
				sleep(time_to_measure) 			# crude way to give time before requesting the waveform
				waveform = ch.measurement.fetch_waveform()
				for t in waveform:
					f.write('\t'.join(str(s) for s in t) + str(abso_time(abso_count)) + '\n')
					abso_count += 1
		counter += 1 

