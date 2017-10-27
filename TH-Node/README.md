# RPI Temperature and Humidity Node
Sample application to demonstrate the cloud infrastructure using a Raspberry PI
with the Honeywell HIH6130 sensor chip connect to I2C.

## Board setup

* IC2 setup

Run `raspi-config` and enable I2C in `Interfacing Options`.

Check the necessary kernel modules are in `/etc/modules`:
```
snd-bcm2835
i2c-dev
```

Check the config options in `/boot/config.txt`:
```
dtparam=i2c_arm=on
```

> Reboot needed

* Check for sensor presence

The command:
```
$ sudo i2cdetect -y 1
```
if properly connected it shows the sensor at address 0x27
```
root@raspberrypi:~# i2cdetect -y 1
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
00:          -- -- -- -- -- -- -- -- -- -- -- -- --
10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
20: -- -- -- -- -- -- -- 27 -- -- -- -- -- -- -- --
30: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
40: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
50: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
60: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
70: -- -- -- -- -- -- -- --
```

* Install Python 3
```
$ sudo apt-get install python3-dev
```

Install the HIH6130 Python library:
```
$ cd ./python-hih6130-master
$ sudo python3 setup.py install
```

* Install SMBUS for Python
```
sudo -i
apt-get install python3-dev
apt-get install libi2c-dev
apt-get install python3-smbus
cd /tmp
wget http://ftp.de.debian.org/debian/pool/main/i/i2c-tools/i2c-tools_3.1.0.orig.tar.bz2 # download Python 2 source
tar xavf i2c-tools_3.1.0.orig.tar.bz2
cd i2c-tools-3.1.0/py-smbus
mv smbusmodule.c smbusmodule.c.orig # backup
wget https://gist.githubusercontent.com/sebastianludwig/c648a9e06c0dc2264fbd/raw/2b74f9e72bbdffe298ce02214be8ea1c20aa290f/smbusmodule.c # download patched (Python 3) source
python3 setup.py build
python3 setup.py install
```

