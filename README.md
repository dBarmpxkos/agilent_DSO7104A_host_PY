# Python GUI :computer: controller for ⚡ Agilent DSO7104A

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
1) install IOLibSuite_18_1_24715
2) install Agilent546XX driver
3) install Python (tested with 3.6.0)
	3a pip install pyserial
	3b pip install -U pyvisa
	3c python ivi [https://github.com/python-ivi/python-ivi]
	3d pip install pysimplegui
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Exposes:
- timescale control
- acquisition mode
- amplitude control per channel
- trigger settings (mode, source)
- two logging modes (continuous, with iterations)
