import web

urls = (
    '/', 'index'
)

#!/usr/bin/python

import requests
from bs4 import BeautifulSoup 
import os
#from urllib import unquote
import chardet
import urllib2
import re
import json


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

		soup = BeautifulSoup(self._context)
		
		tmp = [i.text for i in  soup.find_all('script') if  i.text.strip().startswith('MSL')][0].split('MSL')

		for item in tmp:
			if len(item.split(','))>2:
				#print repr(item.split(',')[0].strip('("'))
				self._idAndname.setdefault(item.split(',')[1],item.split(',')[0].strip('("'))

	def lookForDownloadStr(self):

		for k in self._idAndname.keys():

			tmpUrl = self._baseUrl+k.replace('"','').strip()+"/"
			tmpText = self._req.get(tmpUrl).text
			#tmpText = urllib2.urlopen(tmpUrl).read()
			tmpSoup = BeautifulSoup(tmpText)
			pattern = re.compile(r'strURL =.*;')
			context = tmpSoup.find(id = "playicon").text.encode('utf-8')

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
			else:
				pass
		
		tmpDict = {}
		for k,v in self._nameAndurl.items():
			tmpDict.setdefault("name",k)
			tmpDict.setdefault("url",v)
			self._rawJsonData.setdefault("song",[]).append(tmpDict)
			tmpDict = {}
		return  json.dumps(self._rawJsonData,sort_keys=True,indent=4)

class index:
    def GET(self):
    	testObj = SongTaste(r'http://www.songtaste.com/music/')
    	testObj.findNameAndId()
    	#print testObj._idAndname
    	return  testObj.lookForDownloadStr()
        

if __name__ == "__main__":
    app = web.application(urls, globals())
    app.run()
