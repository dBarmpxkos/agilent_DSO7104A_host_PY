# addr: 'USB0::0x0957::0x1755::MY48260377::0::INSTR'

import ivi
import pyvisa
from datetime import datetime
import PySimpleGUI as sg
from decimal import Decimal
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
		usb_connect_success = True
	except pyvisa.errors.VisaIOError:
		usb_connect_success = False

def configure_timebase(time_per_rec, acq_type):
	global scope
	scope.acquisition.time_per_record = time_per_rec # sec/Div. max:1e3(50s/Div) - min:1e-9(500ps/Div)
	scope.acquisition.type = acq_type # 'normal', high_resolution', 'average', 'peak_detect'

	# print(round(scope.acquisition.sample_rate)) # samples/sec
	                                           
def configure_channels(what_channel, ch_enable, ch_offset, ch_range, ch_coupling):
	global scope
	scope.channels[what_channel].enabled 	= ch_enable		# T/F
	scope.channels[what_channel].offset 	= ch_offset		# Volts
	scope.channels[what_channel].range 		= ch_range		# Volts/Div
	scope.channels[what_channel].coupling 	= ch_coupling 	# 'ac', 'dc', 'gnd'

def configure_trigger(tri_source, tri_slope, tri_level,tri_is_continuous):
	global scope
	# hardcoded for now
	scope.trigger.type = 'edge'
	scope.trigger.source = scope.channels[tri_source]
	scope.trigger.edge.slope = tri_slope		 # 'positive', 'negative'
	scope.trigger.level = tri_level				 # level in Volts
	scope.trigger.continuous = tri_is_continuous # True/False. 

def measure_and_log():
	global scope

	counter = 0 # used for naming 
	for ch in scope.channels[0:3]:
		if ch.enabled: 
			# datetime_channel construct filename
			dt_for_filename = datetime.now().strftime("%d-%m-%Y_%H-%M-%S_ch") + str(counter) + '.txt'
			with open(dt_for_filename, 'a') as f:
				scope.measurement.initiate()
				waveform = ch.measurement.fetch_waveform()
				for t in waveform:
					f.write('\t'.join(str(s) for s in t) + '\n')
		counter += 1 
# /funs -----------------------------------------------------------------


# menu ------------------------------------------------------------------
layout = [

# ---- Connection ------------------------------------------------------
[sg.Button('Connect'), sg.Button('Disconnect', disabled = True)],

# ---- Time Settings ---------------------------------------------------
[sg.Frame(layout=[ 
	[sg.Text('Timebase:'), sg.In(size=(8,1) ,key='timediv'), sg.Text('sec/div'), sg.VerticalSeparator(pad=None),
	 sg.Text('Acquisition Type:'), sg.Combo(['normal', 'high_resolution', 'average', 'peak_detect'], key='acq_type')],
	[sg.Text('Current Sampling Rate'), sg.Text('x', text_color='red', key='sampling_rate', size=(7,1)), sg.Text('samples/sec')],
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
	 sg.Text('Level'), sg.In(size=(8,1), default_text = 0.5, key='tri_level'), sg.Text('V')], 
	[sg.Checkbox('Continue After Trigger', default = True, key='tri_cont'),
	 sg.Text('Source Channel:'), sg.Combo([0,1,2,3], key='tri_source')],
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

window = sg.Window('Agilent MSO7104A Control v1.0', layout, no_titlebar=False, grab_anywhere=True)

while True:
	event, values = window.read()
	# print(event, values)

	if event is None:
		break

	if event == 'Connect':
		scan_USB_connect()
		if usb_connect_success is True:
			window.Element('Set Time Settings').Update(disabled=True)
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

	if event == 'Set Time Settings':
		if is_number(values['timediv']):
			configure_timebase(values['timediv'], values['acq_type'])	
			window.Element('sampling_rate').Update(str('%.2E' % Decimal(scope.acquisition.sample_rate)), text_color='green')

	if event == 'Set Amplitude Settings':
		if (is_number(values['ch0_voltdiv'])):
			configure_channels(0, values['ch0_EN'], 0, values['ch0_voltdiv'], values['ch0_coupling'])
		else:
			pass
		if (is_number(values['ch1_voltdiv'])):
			configure_channels(1, values['ch1_EN'], 0, values['ch1_voltdiv'], values['ch1_coupling'])
		else:
			pass
		if (is_number(values['ch2_voltdiv'])):
			configure_channels(2, values['ch2_EN'], 0, values['ch2_voltdiv'], values['ch2_coupling'])
		else:
			pass
		if (is_number(values['ch3_voltdiv'])):
			configure_channels(3, values['ch3_EN'], 0, values['ch3_voltdiv'], values['ch3_coupling'])
		else:
			pass

	if event == 'Set Trigger Settings':
		if (is_number(values['tri_level'])):
			configure_trigger(values['tri_source'], values['tri_slope'], values['tri_level'], values['tri_cont'])
		else:
			pass

	if event == 'Start Logging':
		if values['log_cont']:
			while True:
				measure_and_log() 
				if event == 'Stop Logging':
					break
		else:
			for i in range(0, values['times_to_log']):
				measure_and_log()
				if event == 'Stop Logging':
					break

window.close()