# -*- coding: utf-8 -*-  
import urllib
import urllib2
import base64
import re
import json  
import rsa  
import binascii  
import requests  
from bs4 import BeautifulSoup
import time
import web
import random


class weibo:
    def __init__(self):
        self.db = web.database(host='120.77.44.206', port=3306, dbn='mysql', db='weibo', user='niujiac', pw='n353081024')
        self.headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.79 Safari/537.36',
    }

    def login(self, username, password):
        session = requests.Session()
        url_prelogin = 'http://login.sina.com.cn/sso/prelogin.php?entry=weibo&callback=sinaSSOController.preloginCallBack&su=&rsakt=mod&client=ssologin.js(v1.4.5)&_=1364875106625'
        url_login = 'http://login.sina.com.cn/sso/login.php?client=ssologin.js(v1.4.5)'

        # get servertime,nonce, pubkey,rsakv
        resp = session.get(url_prelogin)
        json_data = re.findall(r'(?<=\().*(?=\))', resp.text)[0]
        data = json.loads(json_data)
        servertime = data['servertime']
        nonce = data['nonce']
        pubkey = data['pubkey']
        rsakv = data['rsakv']
        # print(urllib.parse.quote(username))
        su = base64.b64encode(username.encode(encoding="utf-8"))
        rsaPublickey = int(pubkey, 16)
        key = rsa.PublicKey(rsaPublickey, 65537)
        message = str(servertime) + '\t' + str(nonce) + '\n' + str(password)
        sp = binascii.b2a_hex(rsa.encrypt(message.encode(encoding="utf-8"), key))
        postdata = {
            'entry': 'weibo',
            'gateway': '1',
            'from': '',
            'savestate': '7',
            'userticket': '1',
            'ssosimplelogin': '1',
            'vsnf': '1',
            'vsnval': '',
            'su': su,
            'service': 'miniblog',
            'servertime': servertime,
            'nonce': nonce,
            'pwencode': 'rsa2',
            'sp': sp,
            'encoding': 'UTF-8',
            'url': 'http://weibo.com/ajaxlogin.php?framelogin=1&callback=parent.sinaSSOController.feedBackUrlCallBack',
            'returntype': 'META',
            'rsakv': rsakv,
        }
        response = session.post(url_login, data=postdata)
        login_url = re.findall(r'http://weibo.*&retcode=0', response.text)[0]
        print('登录成功')
        respo = session.get(login_url)
        uid = re.findall('"uniqueid":"(\d+)",', respo.text)[0]
        url = "http://weibo.com/u/" + uid
        print(url)
        return session

    def getpage(self, url):
        try:
            request = urllib2.Request(url, headers=self.headers)
            response = urllib2.urlopen(request)
            return response.read().decode('utf-8')
        except urllib2.URLError, e:
            print u"连接失败,错误原因",e.reason
            return None

    def getlist(self):
        dbdata = self.db.select('realtimehot', what='id, link', order='id ASC')
        dbdata1 = self.db.select('weiboitem', what='distinct listid')
        ids = []
        for id in dbdata1:
            ids.append(id.listid)
            #print id.listid
        dict = {}
        for data in dbdata:
            if data.id in ids:
                #print data.id, data.link
                continue
            if dict.get(data.link) == None:
                dict.setdefault(data.link, [data.id])
            else:
                dict[data.link].append(data.id)
            #list.append([data.id, data.link])
            #print data.id, data.link
        return dict

    def gettext(self, dictdata):
        for item in dictdata:
            print item, dictdata[item]
            page = self.getpage(item)
            #print page
            #page = session.get(item[1]).text
            soup = BeautifulSoup(page, "html.parser")
            script = soup.find_all('script')
            x = None
            for sc in script:
                if sc.string and '"pid":"pl_weibo_direct"' in sc.string:
                    x = json.loads(re.findall('{.*}', sc.string)[0], encoding="utf-8")
                    break
            try:
                data = x['html']
            except:
                print "被封了", "http://s.weibo.com"
                return 0
            #print data
            soup = BeautifulSoup(data, "html.parser")
            contents = soup.find_all('p', {"class": "comment_txt"})
            for i in range(len(contents)):
                print i, contents[i].text.replace('\n', '').strip()
                for id in dictdata[item]:
                    try:
                        self.db.insert('weiboitem', listid=id, content=contents[i].text.replace('\n', '').strip())
                    except:
                        pass
            time.sleep(random.randint(30, 60))

    def gettext1(self, dictdata, session):
        for item in dictdata:
            print item, dictdata[item]
            #page = self.getpage(item)
            #print page
            page = session.get(item[1]).text
            soup = BeautifulSoup(page, "html.parser")
            script = soup.find_all('script')
            x = None
            for sc in script:
                if sc.string and '"pid":"pl_weibo_direct"' in sc.string:
                    x = json.loads(re.findall('{.*}', sc.string)[0], encoding="utf-8")
                    break
            try:
                data = x['html']
            except:
                print "被封了", "http://s.weibo.com"
                return 0
            #print data
            soup = BeautifulSoup(data, "html.parser")
            contents = soup.find_all('p', {"class": "comment_txt"})
            for i in range(len(contents)):
                print i, contents[i].text.replace('\n', '').strip()
                for id in dictdata[item]:
                    try:
                        self.db.insert('weiboitem', listid=id, content=contents[i].text.replace('\n', '').strip())
                    except:
                        pass
            time.sleep(random.randint(30, 60))


if __name__ == '__main__':
    while True:
        test = weibo()
        #session = test.login('13717776265', 'n353081024')
        dict_data = test.getlist()
        if len(dict_data) == None:
            print 'none'
        else:
            test.gettext(dict_data)
            #test.gettext1(dict_data, session)
        time.sleep(60)

