#!/usr/bin/env python
#----------------------------------------------------------------
#	Note:
#		ds18b20's data pin must be connected to pin7.
#		replace the 28-XXXXXXXXX as yours.
#----------------------------------------------------------------
import os
import requests
import time

ds18b20 = ''

def setup():
	global ds18b20
	for i in os.listdir('/sys/bus/w1/devices'):
		if i != 'w1_bus_master1':
			ds18b20 = i

def read():
#	global ds18b20
	location = '/sys/bus/w1/devices/' + ds18b20 + '/w1_slave'
	tfile = open(location)
	text = tfile.read()
	tfile.close()
	secondline = text.split("\n")[1]
	temperaturedata = secondline.split(" ")[9]
	temperature = float(temperaturedata[2:])
	temperature = temperature / 1000
	return temperature
	
def loop():
	while True:
		temp = read()
		if temp != None:
			status_code = upload(temp)
			print('Current temp:{} C, status_code:{}'.format('%0.3f'%temp, status_code))

def upload(temp):
	host_name = 'http://192.168.1.108:8086'# target host name
	db_name = 'xiaogu'
	user_name = 'test'
	user_passwd = 'test'
	upload_url = '{}/write?db={}&u={}&p={}'.format(host_name,db_name,user_name,user_passwd)
	print(upload_url)
	text = 'pi temp={}'.format(temp)
	response = requests.post(upload_url, data=text.encode('utf-8'))
	if response.status_code == 404:
		requests.get('{}/query?u={}&p={}&q=create database {}'.format(host_name,user_name,user_passwd,db_name))
		response = requests.post(upload_url, data=text.encode('utf-8'))
	time.sleep(10)
	return response.status_code

def destroy():
	pass

if __name__ == '__main__':
	try:
		setup()
		loop()
	except KeyboardInterrupt:
		destroy()
