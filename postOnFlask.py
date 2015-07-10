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

from threading import Thread, RLock, Lock
from time import sleep
from functools import wraps
from threading import current_thread

reload(sys)
sys.setdefaultencoding("utf-8")
 
def synchronous( tlockname ):
    """
    A decorator to place an instance based lock around a method
    from: http://code.activestate.com/recipes/577105-synchronization-decorator-for-class-methods/
    """
 
    def _synched(func):
        @wraps(func)
        def _synchronizer(self,*args, **kwargs):
            tlock = self.__getattribute__( tlockname)
            tlock.acquire()
            try:
                return func(self, *args, **kwargs)
            finally:
                tlock.release()
        return _synchronizer
    return _synched
 
class ThreadPoolThread(Thread):
    
    def __init__(self, pool):
        Thread.__init__(self)
        self.__pool = pool
        self.start()
    def run(self):
        try:
            while True:
                task = self.__pool.pop_task()
                if task == None:
                    break
                if task[1] != None and task[2] != None:
                    task[0](*task[1], **task[2])
                elif task[1] != None:
                    task[0](*task[1])
                else:
                    task[0]()
        finally:
            # Always inform about thread finish
            self.__pool.thread_finished()
    
 
class ThreadPool(object):
    
    def __init__(self, thread_count):
        self.__tasks = []
        self.task_lock = Lock()
        self.__thread_count = thread_count
        self.__threads = []
        self.threads_lock = Lock()
        self.__finished_threads_count = 0
        self.finished_threads_count_lock = Lock()
        
    @synchronous('task_lock')
    def add_task(self, callable_, args=None, kwds=None):
        self.__tasks.append((callable_, args, kwds))
    
    @synchronous('task_lock')
    def pop_task(self):
        if len(self.__tasks) > 0:
            return self.__tasks.pop(0)
        else:
            return None
    
    def start_workers(self):
        self.__finished_threads_count = 0
        self.__threads = []
        for i in range(self.__thread_count):
            worker = ThreadPoolThread(self)
            self.__threads.append(worker)
    
    def wait(self):
        """
        Wait for every worker threads to finish
        """
        while True:
            finished_threads_count = self.get_finished_threads_count()
            if finished_threads_count == self.__thread_count:
                break
            sleep(0.1)
    
    @synchronous('finished_threads_count_lock')
    def thread_finished(self):
        self.__finished_threads_count += 1
    
    @synchronous('finished_threads_count_lock')
    def get_finished_threads_count(self):
        return self.__finished_threads_count
 
#theading pool code come from https://gist.github.com/junaidpv/1130407
class SongTaste(object):

	def __init__(self,url):

		self._url = url #
		self._req = requests.session()
		self._context = urllib2.urlopen(url).read()
		self._idAndname = {}
		self._baseUrl = r'http://www.songtaste.com/song/'
		self._nameAndurl = {}
		self._rawJsonData = {}
		self._workpool = ThreadPool(30)
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

	def urlFetcher(self,k):

		tmpUrl = self._baseUrl+k.replace('"','').strip()+"/"
		#tmpText = self._req.get(tmpUrl).text
		tmpText = urllib2.urlopen(tmpUrl).read()

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
			print self._idAndname[k].encode('utf-8')
		else:
			pass

			
	def mutilUrlFetcher(self):

		if self._idAndname == {} or self._idAndname is None:
			self.findNameAndId()
		
		for k in self._idAndname.keys():
			
			self._workpool.add_task(self.urlFetcher, (k,))

		self._workpool.start_workers()
		self._workpool.wait()
		

	def composeJson(self):

		
		tmpDict = {}
		for k,v in self._nameAndurl.items():
			tmpDict.setdefault("name",k.decode('utf-8'))
			tmpDict.setdefault("url",v)
			self._rawJsonData.setdefault("song",[]).append(tmpDict)
			tmpDict = {}

		print json.dumps(self._rawJsonData,sort_keys=True,indent=4,ensure_ascii=False)
		return json.dumps(self._rawJsonData,sort_keys=True,indent=4,ensure_ascii=False)




	def lookForDownloadStr(self):

		for k in self._idAndname.keys():

			tmpUrl = self._baseUrl+k.replace('"','').strip()+"/"
			#tmpText = self._req.get(tmpUrl).text
			tmpText = urllib2.urlopen(tmpUrl).read()

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
			tmpDict.setdefault("url",v)
			self._rawJsonData.setdefault("song",[]).append(tmpDict)
			tmpDict = {}

		return  json.dumps(self._rawJsonData,sort_keys=True,indent=4,ensure_ascii=False)

from flask import Flask
app = Flask(__name__)

@app.route("/")
def retJson():
	songTasteObj = SongTaste(r'http://www.songtaste.com/music/')
	songTasteObj.mutilUrlFetcher()
	
	return songTasteObj.composeJson()

if __name__ == '__main__':
	
	songTasteObj = SongTaste(r'http://www.songtaste.com/music/')
	songTasteObj.mutilUrlFetcher()
	songTasteObj.composeJson()
	#app.run()