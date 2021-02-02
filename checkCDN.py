# -*- coding: utf-8 -*-
import dns.resolver
import requests
import ipaddress
import geoip2.database
import socket
import sys
import re
from concurrent.futures import ThreadPoolExecutor,wait, ALL_COMPLETED
from const import all_CNAME,cdns,ASNS

def matched(obj,list):
	#print(obj)
	for i in list:
		if i in obj:
			return True
	return False


def getCNAMES(domain):
	cnames = []
	cname = getCNAME(domain)
	if cname is not None:
		cnames.append(cname)
	while(cname != None):
		cname = getCNAME(cname)
		if cname is not None:
			cnames.append(cname)
	return cnames

def getCNAME(domain):
	try:
		answer = dns.resolver.resolve(domain,'CNAME')
	except:
		return None
	cname = [_.to_text() for _ in answer][0]
	return cname


def checkIP(ip):
	try:
		for cdn in cdns:
			if ipaddress.ip_address(ip) in ipaddress.ip_network(cdn):
				return True
		return False
	except:
		return False

def getIP(domain):
	try:
		addr = socket.getaddrinfo(domain,None)
	except:
		return None
	return str(addr[0][4][0])


def checkASN(ip):
	try:
		with geoip2.database.Reader('GeoLite2-ASN.mmdb') as reader:
			response = reader.asn(ip)
			for i in ASNS:
				if response.autonomous_system_number == int(i):
					return True
	except:
		return False
	return False



def wFile(file,str):
	try:
		f = open(file,'a')
		f.write(str)
		f.write('\n')
	finally:
		f.close()

def check(data):
	if not re.search(r'\d+\.\d+\.\d+\.\d+', data):
		ip = getIP(data)
	else:
		ip = data
	if ip is None:
		return

	cdnip = checkIP(ip)

	if cdnip == True:
		print(data+": CDN")
		wFile('cdn.txt',data)
		return

	cdnasn = checkASN(ip)
	if cdnasn == True:
		print(data+": CDN")
		wFile('cdn.txt',data)
		return

	if not re.search(r'\d+\.\d+\.\d+\.\d+', data):
		cnames = getCNAMES(data)
		match = False
		for i in cnames:
			match = matched(i,all_CNAME)
			if match == True:
				break
		if match == True:
			print(data+": CDN")
			wFile('cdn.txt',data)
			return
	print(data+": notCDN")
	wFile('notcdn.txt',data)
	wFile('ip.txt',ip)
	return



if __name__ == '__main__':
	if len(sys.argv) != 2:
		print("error command -h for help")
		exit()
	if sys.argv[1] == '-h':
		print("")
		print("checkCDN.py list.txt")
		print("")
		exit()
	dataList = []
	try:
		f = open(sys.argv[1])
		for text in f.readlines():
			data = text.strip('\n')
			dataList.append(data)
	finally:
		f.close()
	with ThreadPoolExecutor(max_workers=100) as pool:
		all_task = [pool.submit(check,data) for data in dataList]
		wait(all_task, return_when=ALL_COMPLETED)