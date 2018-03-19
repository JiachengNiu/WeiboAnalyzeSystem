# -*- coding: utf-8 -*-  
import urllib
import urllib.parse
import base64
import re
import json  
import rsa  
import binascii  
import requests  
from bs4 import BeautifulSoup
import time
  
class weibo:
    def login(self, username, password):
        session = requests.Session()
        url_prelogin = 'http://login.sina.com.cn/sso/prelogin.php?entry=weibo&callback=sinaSSOController.preloginCallBack&su=&rsakt=mod&client=ssologin.js(v1.4.5)&_=1364875106625'
        url_login = 'http://login.sina.com.cn/sso/login.php?client=ssologin.js(v1.4.5)'

        #get servertime,nonce, pubkey,rsakv
        resp = session.get(url_prelogin)
        json_data = re.findall(r'(?<=\().*(?=\))', resp.text)[0]
        data = json.loads(json_data)
        servertime = data['servertime']
        nonce = data['nonce']
        pubkey = data['pubkey']
        rsakv = data['rsakv']
        #print(urllib.parse.quote(username))
        su = base64.b64encode(username.encode(encoding="utf-8"))
        rsaPublickey= int(pubkey,16)
        key = rsa.PublicKey(rsaPublickey,65537)
        message = str(servertime) +'\t' + str(nonce) + '\n' + str(password)
        sp = binascii.b2a_hex(rsa.encrypt(message.encode(encoding="utf-8"),key))
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
            'rsakv' : rsakv,
        }
        response = session.post(url_login, data=postdata)
        login_url = re.findall(r'http://weibo.*&retcode=0', response.text)[0]
        print('登录成功')
        respo = session.get(login_url)
        uid = re.findall('"uniqueid":"(\d+)",', respo.text)[0]
        url = "http://weibo.com/u/"+uid
        print(url)
        return session

    def getpage(self, url):
        try:
            request = urllib.request.Request(url)
            response = urllib.request.urlopen(request)
            return response.read().decode('utf-8')
        except:
            print(u"连接失败")
            return None

    def getlist(self):
        page = self.getpage('http://s.weibo.com/top/summary?cate=realtimehot')
        soup = BeautifulSoup(page, "html.parser")
        script = soup.find_all('script')
        for sc in script:
            if sc.string and "<\/td>" in sc.string:
                #print(re.findall('{.*}', sc.string)[0])
                x = json.loads(re.findall('{.*}', sc.string)[0], encoding="utf-8")
                break
        data = x['html']
        #print(data)
        ranks = re.findall('<td class="td_01"><span class="search_icon_rankn.*<em>(.*?)</em></span></td>', data)
        links = re.findall('<p class="star_name"><a href="(.*?)" target="_blank" suda-data="key=tblog_search_list&value=.*">.*</a>', data)
        titles = re.findall('<p class="star_name"><a href=".*" target="_blank" suda-data="key=tblog_search_list&value=.*">(.*?)</a>', data)
        numbers = re.findall(' <td class="td_03"><p class="star_num"><span>(.*?)</span></p></td>', data)
        list_data = []
        for i in range(len(ranks)):
            print(ranks[i], 's.weibo.com'+links[i], titles[i], numbers[i])
            list_data.append([ranks[i], 's.weibo.com'+links[i], titles[i], numbers[i]])
        return list_data


test = weibo()
#session = test.login('13717776265', 'n353081024')
#print(session.get('http://weibo.com/u/5917958078').content)
list_data = test.getlist()
date = str(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))
print(date)
