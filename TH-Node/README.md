# RPI Temperature and Humidity Node
Sample application to demonstrate the cloud infrastructure using a Raspberry PI
with the Honeywell HIH6130 sensor chip connect to I2C.

## Board setup

* IC2 setup

Specify the necessary kernel modules in `/etc/modules`:
```
snd-bcm2835
i2c-dev
```

* Check for sensor presence

The command:
```
$sudo i2cdetect -y 1
```
if properly connected it shows the sensor at address 0x27


Install the HIH6130 Python library:
```
$ cd ./python-hih6130-master
$ sudo python3 setup.py install
```
