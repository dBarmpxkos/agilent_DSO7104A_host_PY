# addr: 'USB0::0x0957::0x1755::MY48260377::0::INSTR'

import ivi
import pyvisa
from datetime import datetime
import PySimpleGUI as sg
from decimal import Decimal
import numpy as np
from time import sleep 

sg.ChangeLookAndFeel('Reddit')

rm    = None
scope = None
usb_connect_success = False
continuous_logging_switch = True

# funs ---------------------------------------------------------------
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def scan_USB_connect(): # need to add exceptions
	global rm, scope, usb_connect_success
	try: 
		rm = pyvisa.ResourceManager().list_resources()[0] # first resource
		scope = ivi.agilent.agilentMSO7104A(rm, prefer_pyvisa = True)
		scope.close()
		scope = ivi.agilent.agilentMSO7104A(rm, prefer_pyvisa = True)
		usb_connect_success = True
	except pyvisa.errors.VisaIOError:
		usb_connect_success = False

def configure_timebase(time_per_rec, acq_type):
	global scope
	scope.acquisition.time_per_record = time_per_rec # sec/Div. max:1e3(50s/Div) - min:1e-9(500ps/Div)
	scope.acquisition.type = acq_type # 'normal', high_resolution', 'average', 'peak_detect'
	# print(scope.acquisition.sample_rate) # samples/sec
	return True # crude af
	                                           
def configure_channels(what_channel, ch_enable, ch_offset, ch_range, ch_coupling):
	global scope
	scope.channels[what_channel].enabled 	= ch_enable		# T/F
	scope.channels[what_channel].offset 	= ch_offset		# Volts
	scope.channels[what_channel].range 		= ch_range		# Volts/Div
	scope.channels[what_channel].coupling 	= ch_coupling 	# 'ac', 'dc', 'gnd'

def configure_trigger(tri_source, tri_modifier, tri_slope, tri_level,tri_is_continuous):
	global scope
	# hardcoded for now
	scope.trigger.type = 'edge'
	scope.trigger.source = scope.channels[tri_source]
	scope.trigger.modifier = tri_modifier
	scope.trigger.edge.slope = tri_slope		 # 'positive', 'negative'
	scope.trigger.level = tri_level				 # level in Volts
	scope.trigger.continuous = tri_is_continuous # True/False. 

def construct_datetime_name():
	global scope

	dt_for_filename = [' '] * 4
	counter = 0 # used for naming 
	for ch in scope.channels[0:3]:
		if ch.enabled: 
			# datetime_channel construct filename
			dt_for_filename[counter] = datetime.now().strftime("%d-%m-%Y_%H-%M-%S_ch") + \
									   str(counter) + '.txt'
		counter += 1
	return dt_for_filename

def add_abso_time(time_interval):
	interval = time_interval/1000
	return np.arange(0, time_interval, interval)

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
# /funs -----------------------------------------------------------------


# menu ------------------------------------------------------------------
layout = [

# ---- Connection ------------------------------------------------------
[sg.Button('Connect'), sg.Button('Disconnect', disabled = True)],

# ---- Time Settings ---------------------------------------------------
[sg.Frame(layout=[ 
	[sg.Text('Timebase:'), sg.In(size=(8,1) ,key='timediv', default_text = 1e-3), sg.Text('sec/div'), sg.VerticalSeparator(pad=None),
	 sg.Text('Acquisition Type:'), sg.Combo(['normal', 'high_resolution', 'average', 'peak_detect'], key='acq_type')],
	[sg.Button('Set Time Settings', disabled = True)] 
	], title='Time Settings', title_color='black')],

# ---- Amplitude Configuration -----------------------------------------
[sg.Frame(layout=[ 
    [sg.Checkbox('Ch0:', default = True, key='ch0_EN'), sg.In(size=(8,1), default_text = 1, key='ch0_voltdiv'), 
     sg.Text('V/div'), sg.VerticalSeparator(pad=(15,2)), 
     sg.Combo(['ac', 'dc'], key='ch0_coupling'), sg.Text('Coupling')],
    [sg.Checkbox('Ch1:', key='ch1_EN'), sg.In(size=(8,1), default_text = 1, key='ch1_voltdiv'), sg.Text('       '), 
     sg.VerticalSeparator(pad=(15,2)),
     sg.Combo(['ac', 'dc'], key='ch1_coupling')],
    [sg.Checkbox('Ch2:', key='ch2_EN'), sg.In(size=(8,1), default_text = 1, key='ch2_voltdiv'), sg.Text('       '), 
     sg.VerticalSeparator(pad=(15,2)),
     sg.Combo(['ac', 'dc'], key='ch2_coupling')],
    [sg.Checkbox('Ch3:', key='ch3_EN'), sg.In(size=(8,1), default_text = 1, key='ch3_voltdiv'), sg.Text('       '), 
     sg.VerticalSeparator(pad=(15,2)),
     sg.Combo(['ac', 'dc'], key='ch3_coupling')],
    [sg.Button('Set Amplitude Settings', disabled = True)]
	], title='Amplitude Configuration', title_color='black')],  

# ---- Trigger ---------------------------------------------------------
[sg.Frame(layout=[ 
	[sg.Text('Slope:'), sg.Combo(['positive', 'negative'], key='tri_slope'),
	 sg.Text('Level'), sg.In(size=(8,1), default_text = 0.5, key='tri_level'), sg.Text('V'), 
	 sg.Text('Source Channel:'), sg.Combo([0,1,2,3], key='tri_source')], 
	[sg.Checkbox('Continue After Trigger', default = True, key='tri_cont'),
	 sg.Text('Modifier:'), sg.Combo(['none', 'auto'], key='tri_modifier')],
	[sg.Button('Set Trigger Settings', disabled = True)]
	], title='Trigger Settings', title_color='gray')],

# ---- Data Logging ----------------------------------------------------
[sg.Frame(layout=[ 
	
	[sg.Checkbox('Continuous Logging', default = True, key='log_cont'), sg.VerticalSeparator(pad=(15,2)), sg.Text('Times to log:'), sg.In(size=(8,1), key='times_to_log')],
	[sg.Button('Start Logging', disabled = True), sg.Button('Stop Logging', disabled = True),
	 sg.Text('Status:'), sg.Text('IDLE', key = 'status', size=(10,1))]
	], title='Data Logging', title_color='gray')
]

]

window = sg.Window('Agilent MSO7104A Control v1.0', layout, no_titlebar=False)

while True:
	event, values = window.read()
	# print(event, values)

	if event is None:
		break

	if event == 'Connect':
		scan_USB_connect()
		if usb_connect_success is True:
			window.Element('Set Time Settings').Update(disabled=False)
			window.Element('Set Amplitude Settings').Update(disabled=False)
			window.Element('Set Trigger Settings').Update(disabled=False)
			window.Element('Start Logging').Update(disabled=False)
			window.Element('Stop Logging').Update(disabled=False)
			window.Element('Disconnect').Update(disabled=False)
			window.Element(key='status').Update('CONNOK', text_color='green')
		else:
			window.Element(key='status').Update('CONERR', text_color='red')

	if event == 'Disconnect':
		scope.close()
		window.Element('Set Time Settings').Update(disabled=True)
		window.Element('Set Amplitude Settings').Update(disabled=True)
		window.Element('Set Trigger Settings').Update(disabled=True)
		window.Element('Start Logging').Update(disabled=True)
		window.Element('Stop Logging').Update(disabled=True)
		window.Element('Disconnect').Update(disabled=True)
		window.Element(key='status').Update('DISCON', text_color='green')

	if event == 'Set Time Settings':				# configure_timebase takes total time window as argument. Osc has 10 div
		if is_number(values['timediv']):			# multiply by 10 for user input as s/div
			configure_timebase(str(float(values['timediv'])*10), values['acq_type'])

	if event == 'Set Amplitude Settings': 			# configure channels takes total amplitude as argument. Osc has 8 div
		if (is_number(values['ch0_voltdiv'])):		# multiply by 8 for user input as V/div
			configure_channels(0, values['ch0_EN'], 0, str(float(values['ch0_voltdiv'])*8), values['ch0_coupling'])
		else:
			pass
		if (is_number(values['ch1_voltdiv'])):
			configure_channels(1, values['ch1_EN'], 0, str(float(values['ch1_voltdiv'])*8), values['ch1_coupling'])
		else:
			pass
		if (is_number(values['ch2_voltdiv'])):	
			configure_channels(2, values['ch2_EN'], 0, str(float(values['ch2_voltdiv'])*8), values['ch2_coupling'])
		else:
			pass
		if (is_number(values['ch3_voltdiv'])):
			configure_channels(3, values['ch3_EN'], 0, str(float(values['ch3_voltdiv'])*8), values['ch3_coupling'])
		else:
			pass

	if event == 'Set Trigger Settings':
		if (is_number(values['tri_level'])):
			configure_trigger(values['tri_source'], values['tri_modifier'], values['tri_slope'], values['tri_level'], values['tri_cont'])
		else:
			pass

	if event == 'Start Logging':
		window.Element(key='status').Update('LOG', text_color='blue')
		dt_for_filename = construct_datetime_name();

		while True:
			# timeout needed for non-blocking read.
			event, values = window.read(timeout = 0.01)
			if event == 'Stop Logging':
				window.Element(key='status').Update('IDLE', text_color='green')
				break

			if values['log_cont']:
				measure_and_log(dt_for_filename, float(values['timediv'])*10)

			elif is_number(values['times_to_log']) and int(values['times_to_log']) > 0:
				for i in range(0, int(values['times_to_log'])):
					measure_and_log(dt_for_filename, float(values['timediv'])*10)
					# timeout needed for non-blocking read 
					event, values = window.read(timeout = 0.01)	
					if event == 'Stop Logging':
						window.Element(key='status').Update('IDLE', text_color='green')
						break

				window.Element(key='status').Update('IDLE', text_color='green')
				break

		add_abso_time(dt_for_filename[0], float(values['timediv'])*10)

if scope:
	scope.close()
window.close()