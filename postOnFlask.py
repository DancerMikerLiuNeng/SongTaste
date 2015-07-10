#!/usr/bin/python
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup 
import os
#from urllib import unquote
from chardet.universaldetector import UniversalDetector
import chardet
import urllib2
import re
import json
import sys

reload(sys)
sys.setdefaultencoding("utf-8")

class SongTaste(object):

	def __init__(self,url):

		self._url = url #
		self._req = requests.session()
		self._context = urllib2.urlopen(url).read()
		self._idAndname = {}
		self._baseUrl = r'http://www.songtaste.com/song/'
		self._nameAndurl = {}
		self._rawJsonData = {}
		#self._context = self._req.get(url).text

	def findNameAndId(self):

		#textEncode = self.checkTextEncode(self._context)['encoding']
		
		#self._context = self._context.decode(textEncode)
		#print self._context.encode('utf-8')
		soup = BeautifulSoup(self._context)
		
		tmp = [i.text for i in  soup.find_all('script') if  i.text.strip().startswith('MSL')][0].split('MSL')

		for item in tmp:
			if len(item.split(','))>2:
				
				#print item.split(',')[0].strip('("').decode('unicode_escape')
				self._idAndname.setdefault(item.split(',')[1],item.split(',')[0].strip('("'))

	def checkTextEncode(self,text):


		ret = chardet.detect(text)
		return ret

	def lookForDownloadStr(self):

		for k in self._idAndname.keys():

			tmpUrl = self._baseUrl+k.replace('"','').strip()+"/"
			#tmpText = self._req.get(tmpUrl).text
			tmpText = urllib2.urlopen(tmpUrl).read()

			
			#tmpText = tmpText.encode(textEncode)

			tmpSoup = BeautifulSoup(tmpText)
			pattern = re.compile(r'strURL =.*;')
			context = tmpSoup.find(id = "playicon").text

			str_code = pattern.search(context)
			if str_code is None:
				pass
			else:
				str_code = str_code.group().split(';')[0].split('=')[1].strip().replace('"','')

			
			header = {"User-agent":"Mozilla/5.0 (Windows NT 6.1) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.57 Safari/536.11"}
			payload = {'str':str_code,'sid':k.replace('"','').strip(),'t':0}
			ret_text = self._req.post('http://www.songtaste.com/time.php',data=payload,headers = header).text

			if ret_text.endswith('.mp3'):
				self._nameAndurl.setdefault(self._idAndname[k],ret_text)
				#print self._idAndname[k].encode('utf-8')
			else:
				pass
		
		tmpDict = {}
		for k,v in self._nameAndurl.items():
			tmpDict.setdefault("name",k.decode('utf-8'))
			#print k.decode('utf-8')
			tmpDict.setdefault("url",v)
			self._rawJsonData.setdefault("song",[]).append(tmpDict)
			tmpDict = {}
		#print json.dumps(self._rawJsonData,sort_keys=True,indent=4,ensure_ascii=False)
		#print self.checkTextEncode(json.dumps(self._rawJsonData,sort_keys=True,indent=4))
		return  json.dumps(self._rawJsonData,sort_keys=True,indent=4,ensure_ascii=False)

from flask import Flask
app = Flask(__name__)

@app.route("/")
def retJson():
	songTasteObj = SongTaste(r'http://www.songtaste.com/music/')
	songTasteObj.findNameAndId()
	return songTasteObj.lookForDownloadStr()

if __name__ == '__main__':
	'''songTasteObj = SongTaste(r'http://www.songtaste.com/music/')
	songTasteObj.findNameAndId()
	songTasteObj.lookForDownloadStr()'''
	app.run()